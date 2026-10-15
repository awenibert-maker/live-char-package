---
name: live-char-package
description: 生成 DF直播间 / DreamFace 数字人直播角色配置包（7 文件 + 上传 zip）。当用户说"生成直播间配置包""做角色包""生成数字人角色配置"，或一次性发来多个角色 brief（姓名 / 语言 / 角色需求）时使用。支持一次最多 10 个角色。流程：收集需求 → 确认输出位置（默认桌面 Live Input）→ 小人填色实时进度 → 脚本质检 → 输出「序号 / 角色名 / 文件夹名称」表格。
---

# 直播间角色配置包生成器

把「一个角色 brief」变成一套可上传的**数字人直播角色配置包**（7 文件 + 上传 zip）。

> **可移植版**：只依赖标准命令与文件系统，不绑定任何平台专属工具。
> 完整细则见同目录 `AGENTS.md` 与 `references/conventions.md`。
> 下文中 `$SKILL` = 本 skill 目录；命令示例用 `python3`（Windows 用 `python`）。

## 总流程

```
1 收集需求 → 2 确认输出位置 → 3 生成 + 实时进度 → 4 质检 → 5 交付表格
```

**创作部分（人格、口播、文案）由你写；机械部分（弹幕、打包、质检、进度、表格）一律调脚本。**

## 步骤 1：收集需求

**用户已粘贴 brief → 直接解析，别再问一遍。** 解析铁律：
- `[时间戳] ~角色名:` 之后的内容 = 聊天记录，不是规格；
- 以 `角色名:` 另起的块 = 另一个独立角色，别把后一个名字误读成前一个角色的属性。

**用户没给 brief → 三选一：**
1. **命令行问答**（默认）：问姓名 / 语言 / 一句话需求，收集完问「还要加吗」，上限 10 个。
2. **本地表单页**（有浏览器时，适合一次填多个）：
   ```bash
   python3 "$SKILL/scripts/intake_server.py" --out "$ROOT"   # 打印 URL，让用户浏览器打开
   ```
   提交后写 `<ROOT>/_intake/briefs.json`（`[{name,lang,need}]`），服务自动退出。
3. **让用户粘贴**：请用户按「姓名 / 语言 / 需求」一次给全，你再解析。

拿到 **①角色名 ②直播语言 ③一句话需求** 即可开工，其余走默认。

## 步骤 2：确认输出位置

```bash
python3 "$SKILL/scripts/root.py get"
```
- 返回路径 → 直接用。
- 返回空（本机首次）→ 脚本已自动创建默认目录（优先桌面 `Live Input`）；告知用户位置并问是否更换，更换用 `root.py set --path`。

```
Live Input/
├── Name_001/          ← 7 个配置文件
├── Name_001.zip       ← 上传包（与文件夹平级），仅含 soul/agent/prologue/livescript
├── _intake/
└── _progress/
```

## 步骤 3：生成 + 实时进度

```bash
ROOT=$(python3 "$SKILL/scripts/root.py" get)
python3 "$SKILL/scripts/progress.py" init --root "$ROOT" --chars "Name1|Name2"
```
生成 `<ROOT>/_progress/progress.html`：一排小人按完成度**从头到脚填色**，2 秒自动刷新，完成自动停刷。**把该文件的绝对路径告诉用户，让他用浏览器打开即可实时看进度。**

每角色 8 步（`character_spec → soul → agent → prologue → 标题 → livescript → comment → zip`），**每写完一个文件更新一次**：
```bash
python3 "$SKILL/scripts/progress.py" update --root "$ROOT" --char 0 --step 3 --stage "写 agent.md"
python3 "$SKILL/scripts/progress.py" done   --root "$ROOT" --char 0
python3 "$SKILL/scripts/progress.py" show   --root "$ROOT"    # 文本进度
```

comment.md 交给脚本（可喂自己写的语料，质量更好）：
```bash
python3 "$SKILL/scripts/gen_comment.py" --out "$ROOT/Name_001/comment.md" --lang en --lines my_lines.txt
```

打包：
```bash
python3 "$SKILL/scripts/make_zip.py" --dir "$ROOT/Name_001"
```

## 步骤 4：质检（必跑）

```bash
python3 "$SKILL/scripts/verify.py" --dir "$ROOT/Name_001" --lang en
```
**出现 FAIL 必须修复后重跑，不许带着 FAIL 交付。**

## 步骤 5：交付

```bash
python3 "$SKILL/scripts/manifest.py" --root "$ROOT"
```
贴出「序号 / 角色名 / 文件夹名称 / 上传包」表格，并说明输出目录绝对路径。

## 硬性约定速查

| 项 | 规则 |
|---|---|
| 命名 | 文件夹 `Name_001`；zip 同名放**上层目录、与文件夹平级**；纯角色名，不带 `type_` 前缀 |
| 语言 | `character_spec` 恒中文；soul/agent 按直播语言（非中文直播→英文）；口播文件用直播语言 |
| prologue | ≤40 词（英文）/ ≤40 字（中·阿等字符型语言） |
| 标题 | ≤40 字符，禁括号 / emoji / 破折号 |
| livescript | 纯 TTS 口播，零括号零 emoji 零时间戳；**首段禁止复读 prologue** |
| comment | JSON 200 条，键仅 `{nickname,user_url,content}`，**严禁 reply 字段**，昵称唯一 |
| agent §13 | 无选择性回复 / 无营业态 / 无去重 / 无跳过，每条真实弹幕必回 + Output Rule 纯朗读 |
| agent §16 | 自曝禁止硬规则（禁承认数字人/AI 助手、不透露开发方、言简意赅、自信直接） |

## 脚本

| 脚本 | 用途 |
|---|---|
| `scripts/root.py get\|set` | 输出根目录持久化 |
| `scripts/intake_server.py --out ROOT` | 本地需求表单页 |
| `scripts/progress.py init\|update\|done\|render\|show` | 小人填色进度 + 自动刷新 HTML |
| `scripts/gen_comment.py` | 生成 200 条弹幕 JSON |
| `scripts/make_zip.py` | 打 4 文件上传包 |
| `scripts/verify.py` | 质检门禁 |
| `scripts/manifest.py` | 汇总表格 |

## 跨平台

- 命令用 `python3`（Windows 用 `python`）；脚本只用标准库，无需依赖。
- 默认输出目录自动适配：优先桌面 `Live Input`，无桌面则用家目录下 `Live Input`。
- macOS 若 Python 报 codesign 错误，改 `/usr/bin/python3`。
- `state.json` 是本地状态（记录输出根目录），不要提交到仓库。
