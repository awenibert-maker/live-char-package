#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify.py — 角色配置包质检门禁。

  verify.py --dir <pkg>/Name_001 --lang en
  verify.py --dir <pkg>/Jura_001 --lang pt --prologue-mode chars

校验：
  1 七文件齐全
  2 prologue 长度（英文 ≤40 词 / 字符型语言 ≤40 字）
  3 标题 ≤40 字符，禁括号/emoji/破折号
  4 livescript 无括号/emoji/时间戳，首段不复读 prologue
  5 comment.md 200 条、昵称唯一、键仅 {nickname,user_url,content}、无 reply
  6 agent.md §13 现行弹幕规则（无跳过/无去重）+ Output Rule 纯朗读
  7 agent.md §16 自曝禁止硬规则
  8 zip 内恰好 4 文件

退出码：0 = 全 PASS；1 = 有 FAIL
"""
import argparse
import json
import os
import re
import sys
import zipfile

REQ_FILES = [
    "character_spec.md", "soul.md", "agent.md",
    "prologue.md", "直播间标题.md", "livescript.md", "comment.md",
]
ZIP_FILES = {"soul.md", "agent.md", "prologue.md", "livescript.md"}

# prologue / 标题 长度按「字符」计数的语言（中日阿等字符型；pt/id 沿用历史做法）
CHAR_LANGS = {"zh", "ja", "ko", "ar", "fa", "he", "pt", "id", "th"}
# livescript 首段重叠判定用「字符集合」的语言 —— 仅限无空格书写的语种。
# 葡/英/阿/西 等空格分词语言必须走词集合，否则字符集太小、重叠率恒 ≈1，必误报。
OVERLAP_CHAR_LANGS = {"zh", "ja", "th"}

EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u2190-\u21FF\u2B00-\u2BFF]"
)
BRACKET_RE = re.compile(r"[()（）\[\]【】{}｛｝]")
TIME_RE = re.compile(r"\b\d{1,2}:\d{2}\b")

# §13「不跳过/不去重」的正面标记（多语言）
NOSKIP_MARKERS = [
    "NO selective reply", "NO \"营业态\"", "NO dedup", "NO skip list",
    "无选择性回复", "无选择性", "不跳过", "每条真实弹幕", "每条弹幕",
    "sem seleção", "não existe resposta seletiva", "não existe deduplicação",
    "nunca pule", "toda danmaku genuína", "precisa receber",
    "لا تتجاهل", "sem filtro",
]
# Output Rule「只输出会被念的话」的正面标记（多语言）
OUTPUT_MARKERS = [
    "spoken-only", "ONLY the words", "only spoken words", "spoken words",
    "somente falado", "apenas as palavras", "只输出", "纯朗读", "只念",
    "الكلمات المنطوقة",
]
# §16 自曝禁止硬规则标记
SELFID_MARKERS = [
    "Self-Identity", "self-identity", "Guardrails de Identidade",
    "自曝", "Disclosure Guardrails", "禁止自曝",
]


PUNCT_RE = re.compile(r"[\s，。,.!！?？、；;：:''\"“”‘’\-—…]+")


def norm(s):
    return PUNCT_RE.sub("", s).lower()


def tokset(s, char_mode):
    """字符型语言(中/阿等)按字符集合；拉丁字母语言按词集合。
    英文若用字符集合判定，重叠率恒为 1（字符集太小）→ 必然误报。"""
    if char_mode:
        return set(PUNCT_RE.sub("", s))
    return set(re.findall(r"[A-Za-z']+", s.lower()))


def overlap_ratio(a, b, char_mode):
    sa, sb = tokset(a, char_mode), tokset(b, char_mode)
    m = min(len(sa), len(sb))
    if m == 0:
        return 0.0
    if m < 8:  # 片段太短不做判定，避免误报
        return 0.0
    return len(sa & sb) / m


def check(root):
    rep, ok = [], True

    def fail(msg):
        nonlocal ok
        ok = False
        rep.append("  [FAIL] " + msg)

    def warn(msg):
        rep.append("  [WARN] " + msg)

    def read(name):
        p = os.path.join(root, name)
        if not os.path.exists(p):
            return None
        with open(p, encoding="utf-8") as f:
            return f.read()

    # 1 文件齐全
    for f in REQ_FILES:
        if not os.path.exists(os.path.join(root, f)):
            fail("缺少文件 " + f)
    if not ok:
        return rep, ok, None

    pro = read("prologue.md").strip()
    title = read("直播间标题.md").strip()
    ls = read("livescript.md")
    ag = read("agent.md")

    # 2 prologue
    mode = ("chars" if args.lang.lower()[:2] in CHAR_LANGS else "words")
    if args.prologue_mode and args.prologue_mode != "auto":
        mode = args.prologue_mode
    if mode == "chars":
        n = len(re.sub(r"\s", "", pro))
        limit = 40
        unit = "字"
    else:
        n = len(pro.split())
        limit = 40
        unit = "词"
    if n > limit:
        fail("prologue %d%s > %d%s" % (n, unit, limit, unit))
    else:
        rep.append("  [OK] prologue %d%s ≤ %d%s" % (n, unit, limit, unit))

    # 3 标题
    if len(title) > 40:
        fail("标题 %d 字符 > 40" % len(title))
    bad = []
    if BRACKET_RE.search(title):
        bad.append("括号")
    if EMOJI_RE.search(title):
        bad.append("emoji")
    if re.search(r"[—–~～]", title):
        bad.append("破折号/波浪号")
    if bad:
        fail("标题含禁用符号: " + "/".join(bad))
    if not bad and len(title) <= 40:
        rep.append("  [OK] 标题 %d 字符，无禁用符号" % len(title))

    # 4 livescript
    if BRACKET_RE.search(ls):
        fail("livescript 含括号")
    if EMOJI_RE.search(ls):
        fail("livescript 含 emoji")
    if TIME_RE.search(ls):
        fail("livescript 含时间戳")
    first_para = ls.strip().split("\n")[0]
    char_mode = (args.lang.lower()[:2] in OVERLAP_CHAR_LANGS)
    np_, nf = norm(pro)[:45], norm(first_para)
    ratio = overlap_ratio(pro, first_para, char_mode)
    if np_ and np_ in nf:
        fail("livescript 首段复读 prologue")
    elif ratio >= 0.45:
        fail("livescript 首段疑似改写复读 prologue（重叠 %.2f）" % ratio)
    else:
        rep.append("  [OK] livescript 无括号/emoji/时间戳，首段未复读 prologue")

    # 5 comment
    try:
        data = json.loads(read("comment.md"))
    except Exception as e:
        fail("comment.md 不是合法 JSON: %s" % e)
        data = None
    if data is not None:
        if len(data) != 200:
            fail("comment %d 条 ≠ 200" % len(data))
        nicks = [d.get("nickname", "") for d in data]
        if len(set(nicks)) != len(nicks):
            fail("comment 昵称重复（%d 唯一 / %d 总数）" % (len(set(nicks)), len(nicks)))
        keysets = {tuple(sorted(d.keys())) for d in data}
        if keysets != {("content", "nickname", "user_url")}:
            fail("comment 键集不合规: %s" % keysets)
        if any("reply" in d for d in data):
            fail("comment 出现 reply 字段（铁律禁止）")
        if len(data) == 200 and len(set(nicks)) == 200 and keysets == {("content", "nickname", "user_url")}:
            rep.append("  [OK] comment 200 条、昵称唯一、键合规、无 reply")

    # 6 agent §13
    ag_low = ag.lower()
    if not any(m.lower() in ag_low for m in NOSKIP_MARKERS):
        fail("agent §13 缺少「不跳过/不去重」现行规则标记")
    else:
        rep.append("  [OK] agent §13 含现行弹幕规则（无跳过/无去重）")
    if not any(m.lower() in ag.lower() for m in OUTPUT_MARKERS):
        fail("agent §13 缺少 Output Rule（纯朗读）")
    else:
        rep.append("  [OK] agent §13 含 Output Rule（spoken-only）")

    # 7 agent §16
    if not any(m.lower() in ag_low for m in SELFID_MARKERS):
        fail("agent 缺少 §16 自曝禁止硬规则")
    else:
        rep.append("  [OK] agent 含 §16 自曝禁止硬规则")

    # 8 zip
    zp = os.path.join(os.path.dirname(root), os.path.basename(root.rstrip("/")) + ".zip")
    if not os.path.exists(zp):
        fail("缺少上传 zip: %s" % zp)
    else:
        names = set(zipfile.ZipFile(zp).namelist())
        if names != ZIP_FILES:
            fail("zip 内文件不符: %s" % sorted(names))
        else:
            rep.append("  [OK] zip 内恰好 4 文件")

    return rep, ok, os.path.basename(root)


def main():
    global args
    ap = argparse.ArgumentParser(description="角色包质检")
    ap.add_argument("--dir", required=True)
    ap.add_argument("--lang", default="en")
    ap.add_argument("--prologue-mode", choices=["auto", "words", "chars"], default="auto")
    args = ap.parse_args()

    root = os.path.abspath(args.dir)
    print("=== 质检 %s (lang=%s) ===" % (os.path.basename(root), args.lang))
    rep, ok, name = check(root)
    print("\n".join(rep))
    print("→ %s" % ("PASS ✔" if ok else "FAIL ✘（必须修复后重跑）"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
