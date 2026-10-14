#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
progress.py — 直播间配置包生成的「小人填色」实时进度可视化。

用法：
  progress.py init   --root <输出根目录> --chars "Name1|Name2|Name3"
  progress.py update --root <输出根目录> --char 0 --step 3 --stage "写 agent.md"
  progress.py done   --root <输出根目录> --char 0
  progress.py render --root <输出根目录>
  progress.py show   --root <输出根目录>

产物：<root>/_progress/status.json 与 <root>/_progress/progress.html
页面每 2 秒自动刷新；全部完成后停止刷新。
"""
import argparse
import html
import json
import os
import sys
from datetime import datetime

FIG_VIEWBOX_H = 170.0
PALETTE = [
    "#34d399", "#22d3ee", "#a78bfa", "#f472b6", "#fbbf24",
    "#60a5fa", "#f87171", "#4ade80", "#c084fc", "#2dd4bf",
]

# 小人轮廓（头 → 躯干 → 双臂 → 双腿 → 双脚），按 y 从上到下排列，保证填色是「从头到脚」
SHAPES = (
    '<circle cx="50" cy="20" r="14"/>'
    '<path d="M38 38 L62 38 L66 88 L34 88 Z"/>'
    '<path d="M38 42 L30 40 L14 78 L21 82 Z"/>'
    '<path d="M62 42 L70 40 L86 78 L79 82 Z"/>'
    '<path d="M36 88 L48 88 L47 148 L35 148 Z"/>'
    '<path d="M52 88 L64 88 L65 148 L53 148 Z"/>'
    '<rect x="29" y="146" width="23" height="10" rx="4"/>'
    '<rect x="48" y="146" width="23" height="10" rx="4"/>'
)


def state_path(root):
    d = os.path.join(root, "_progress")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "status.json")


def load(root):
    p = state_path(root)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def save(root, st):
    with open(state_path(root), "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def resolve_char(st, key):
    """key 可以是序号(0起)或角色名"""
    chars = st["chars"]
    try:
        i = int(key)
        if 0 <= i < len(chars):
            return i
    except (TypeError, ValueError):
        pass
    for i, c in enumerate(chars):
        if c["name"] == key:
            return i
    raise SystemExit("找不到角色: %s" % key)


def figure_svg(idx, name, pct, stage, done, color):
    pct = max(0.0, min(100.0, float(pct or 0)))
    fill_h = FIG_VIEWBOX_H * pct / 100.0
    outline = "#3a4150"
    gid = "fig%d" % idx
    label = html.escape(str(name))
    stage_txt = html.escape(stage or ("完成" if done else "排队中"))
    badge = "#34d399" if done else ("#fbbf24" if pct > 0 else "#4b5563")
    return """<div class="fig">
  <svg viewBox="0 0 100 170" width="88" height="150" role="img" aria-label="%(label)s">
    <defs><clipPath id="%(gid)s"><rect x="0" y="0" width="100" height="%(fh).2f"/></clipPath></defs>
    <g fill="none" stroke="%(outline)s" stroke-width="2.2" stroke-linejoin="round">%(shapes)s</g>
    <g clip-path="url(#%(gid)s)" fill="%(color)s" stroke="%(color)s" stroke-width="2.2" stroke-linejoin="round">%(shapes)s</g>
  </svg>
  <div class="pct">%(pct).0f%%</div>
  <div class="nm">%(label)s</div>
  <div class="st"><span class="dot" style="background:%(badge)s"></span>%(stage_txt)s</div>
</div>""" % {
        "gid": gid, "fh": fill_h, "outline": outline, "shapes": SHAPES,
        "color": color, "pct": pct, "label": label, "stage_txt": stage_txt, "badge": badge,
    }


def render(root):
    st = load(root)
    if not st:
        raise SystemExit("尚未 init，请先运行 progress.py init")
    chars = st["chars"]
    figs = []
    for i, c in enumerate(chars):
        figs.append(figure_svg(i, c["name"], c["pct"], c.get("stage", ""), c.get("done", False),
                               PALETTE[i % len(PALETTE)]))
    overall = sum(c["pct"] for c in chars) / max(1, len(chars))
    all_done = all(c.get("done") for c in chars)
    refresh = "" if all_done else '<meta http-equiv="refresh" content="2">'
    js = "" if all_done else "setTimeout(function(){location.reload();},2000);"
    title = "全部生成完成" if all_done else "正在生成配置包"
    stamp = datetime.now().strftime("%H:%M:%S")

    page = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>配置包生成进度</title>%(refresh)s
<style>
:root{color-scheme:dark}
body{margin:0;padding:28px 32px;background:#0f1115;color:#e5e7eb;
 font:14px/1.6 -apple-system,BlinkMacSystemFont,"PingFang SC","Helvetica Neue",Arial,sans-serif}
h1{margin:0 0 4px;font-size:19px;font-weight:600}
.sub{color:#9ca3af;font-size:12px;margin-bottom:18px}
.bar{height:8px;border-radius:99px;background:#1f2937;overflow:hidden;max-width:640px;margin:10px 0 22px}
.bar>i{display:block;height:100%%;border-radius:99px;
 background:linear-gradient(90deg,#34d399,#22d3ee);transition:width .4s ease}
.row{display:flex;flex-wrap:wrap;gap:14px}
.fig{width:132px;padding:14px 10px 12px;border:1px solid #232936;border-radius:12px;
 background:#141821;text-align:center}
.pct{font-size:15px;font-weight:600;margin-top:6px;font-variant-numeric:tabular-nums}
.nm{margin-top:2px;font-size:12px;color:#e5e7eb;word-break:break-all}
.st{margin-top:5px;font-size:11px;color:#9ca3af;display:flex;align-items:center;justify-content:center;gap:5px}
.dot{width:6px;height:6px;border-radius:99px;display:inline-block}
code{color:#22d3ee}
</style></head><body>
<h1>%(title)s</h1>
<div class="sub">共 %(n)d 个角色 · 总体 %(overall).0f%% · 更新于 %(stamp)s · 目录 <code>%(root)s</code></div>
<div class="bar"><i style="width:%(overall).1f%%"></i></div>
<div class="row">%(figs)s</div>
<script>%(js)s</script>
</body></html>""" % {
        "refresh": refresh, "title": title, "n": len(chars), "overall": overall,
        "stamp": stamp, "root": html.escape(root), "figs": "\n".join(figs), "js": js,
    }
    out = os.path.join(root, "_progress", "progress.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(page)
    return out, overall, all_done


def cmd_init(a):
    names = [n.strip() for n in a.chars.split("|") if n.strip()]
    if not names:
        raise SystemExit("--chars 不能为空")
    st = {
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "chars": [{"name": n, "pct": 0.0, "stage": "排队中", "done": False} for n in names],
    }
    save(a.root, st)
    out, overall, _ = render(a.root)
    print("已初始化 %d 个角色 → %s" % (len(names), out))
    return out


def cmd_update(a):
    st = load(a.root)
    if not st:
        raise SystemExit("尚未 init")
    i = resolve_char(st, a.char)
    c = st["chars"][i]
    if a.pct is not None:
        c["pct"] = float(a.pct)
    elif a.step is not None:
        total = a.total or 8
        c["pct"] = round(min(100.0, float(a.step) / float(total) * 100.0), 1)
    if a.stage:
        c["stage"] = a.stage
    save(a.root, st)
    out, overall, all_done = render(a.root)
    print("[%s] %s%% — %s | 总体 %.0f%%" % (c["name"], c["pct"], c["stage"], overall))
    return out


def cmd_done(a):
    st = load(a.root)
    if not st:
        raise SystemExit("尚未 init")
    i = resolve_char(st, a.char)
    st["chars"][i]["pct"] = 100.0
    st["chars"][i]["stage"] = "完成"
    st["chars"][i]["done"] = True
    save(a.root, st)
    out, overall, all_done = render(a.root)
    print("✔ %s 完成 | 总体 %.0f%%%s" % (st["chars"][i]["name"], overall, " · 全部完成" if all_done else ""))
    return out


def cmd_show(a):
    st = load(a.root)
    if not st:
        raise SystemExit("尚未 init")
    for i, c in enumerate(st["chars"]):
        print("%2d  %-28s %5.1f%%  %s%s" % (i, c["name"], c["pct"], c.get("stage", ""), "  ✔" if c.get("done") else ""))
    overall = sum(c["pct"] for c in st["chars"]) / max(1, len(st["chars"]))
    print("总体 %.0f%%" % overall)


def main():
    p = argparse.ArgumentParser(description="小人填色进度可视化")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("init"); s.add_argument("--root", required=True); s.add_argument("--chars", required=True)
    s.set_defaults(fn=cmd_init)

    s = sub.add_parser("update"); s.add_argument("--root", required=True); s.add_argument("--char", required=True)
    s.add_argument("--step", type=int); s.add_argument("--total", type=int, default=8)
    s.add_argument("--pct", type=float); s.add_argument("--stage")
    s.set_defaults(fn=cmd_update)

    s = sub.add_parser("done"); s.add_argument("--root", required=True); s.add_argument("--char", required=True)
    s.set_defaults(fn=cmd_done)

    s = sub.add_parser("render"); s.add_argument("--root", required=True)
    s.set_defaults(fn=lambda a: render(a.root)[0])

    s = sub.add_parser("show"); s.add_argument("--root", required=True)
    s.set_defaults(fn=cmd_show)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
