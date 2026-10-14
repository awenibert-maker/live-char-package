---
name: live-char-package
description: 生成 DF直播间 / DreamFace 数字人直播角色配置包（7 文件 + 上传 zip）。当用户说"生成直播间配置包""做角色包""生成数字人角色配置""生成直播角色配置"，或一次性发来多个角色 brief（姓名 / 语言 / 角色需求）时使用。流程：表单收集需求（可逐个新增，最多 10 个）→ 确认输出位置（默认 ~/Desktop/Live Input，首次运行必问）→ 小人填色实时进度可视化 → 脚本质检 → 输出「序号 / 角色名 / 文件夹名称」表格。
---

# 直播间角色配置包生成器

把「一个角色 brief → 一套可上传的 7 文件配置包」固化为标准流水线。**创作部分由 agent 写，机械部分一律调脚本**（弹幕生成 / 打包 / 质检 / 进度 / 汇总表），脚本已封装全部历史踩坑。

## 何时使用

- 触发词：「生成直播间配置包」「做一个角色包」「生成数字人角色配置」「配置包」「角色包」
- 用户一次性粘贴多个角色 brief（姓名 / 语言 / 需求）
- 用户只给角色名 + 一句话方向，要产出可上传配置

## 总流程（5 步）

```
1 确认输出位置（仅首次） → 2 收集需求（本地表单页） → 3 生成 + 实时进度 → 4 质检 → 5 交付表格
```

> **两步的顺序不能反，也不要合并进同一张问答卡**：输出位置是一次性设置，需求收集是逐角色业务输入，
> 混在一张卡里会让用户分不清哪些是全局设置、哪些是角色信息（已踩过，见下方「设计红线」）。

---

## 步骤 1：确认输出位置（仅首次，单独一张卡）

```bash
python3 ~/.workbuddy/skills/live-char-package/scripts/root.py get
```
- **返回路径** → 直接用，进入步骤 2，**不要再问**。
- **返回空**（本机首次）→ 脚本已自动创建 `~/Desktop/Live Input`，此时弹**一张只包含这一个问题**的卡：
  - 选项① `就用桌面 Live Input（默认，已创建）`
  - 选项② `我要放到别处（在下方输入框填绝对路径）`
  - 用户选② → `python3 scripts/root.py set --path "<绝对路径>"`

**目录结构**（**zip 与角色文件夹平级**，不放在文件夹里，便于批量选中）：
```
~/Desktop/Live Input/
├── Name_001/                   ← 7 个配置文件
│   ├── character_spec.md  soul.md  agent.md
│   └── prologue.md  直播间标题.md  livescript.md  comment.md
├── Name_001.zip                ← 上传包，与文件夹平级，仅含 soul/agent/prologue/livescript
├── _intake/                    ← 需求收集（briefs.json）
└── _progress/progress.html     ← 实时进度页
```

---

## 步骤 2：收集需求（本地表单页，带真正的「新增」按钮）

### 2a. 用户已粘贴 brief → 直接解析，不要再问一遍
用户习惯一次性把多个角色 brief 粘进来。**解析铁律**（踩过坑，见 references/conventions.md §多角色解析陷阱）：
- `[时间戳] ~角色名:` 之后的内容 = 该角色的**聊天记录**，不是规格；
- 另起一行、以 `角色名:` 开头的块 = **另一个独立角色**，不要把后一个名字误读成前一个角色的属性。

### 2b. 用户没给 brief → 对话内联表单弹窗（首选，不离开对话）
用 `show_widget` 渲染一个 HTML 表单片段，**直接出现在对话里**，用户填完点提交即回传，全程不跳出对话。

**回传机制（关键）**：组件环境提供 `sendPrompt(text)`，提交按钮调用它即可把填写内容作为用户的下一条消息发回对话：
```js
if (typeof sendPrompt === 'function') sendPrompt(promptText);
else if (navigator.clipboard) navigator.clipboard.writeText(promptText);  // 兜底
```
提交文本建议格式（便于解析）：
```
按以下需求生成直播间配置包，直接开工：
1. meriam malak | English | 温暖陪伴型互动主播
2. 小鹿 | 中文 | 深夜哄睡电台
```

表单要素（照抄即可，见 `references/intake_widget.html`）：
- 每行 = **姓名（必填）/ 语言（下拉）/ 一句话需求**；默认给 3 行；
- 右下角 `＋ 新增一个角色`，**上限 10 行**，到 10 行时按钮禁用；每行右侧 `×` 可删；
- 底部实时显示「已填 N / 10」；提交时过滤掉姓名为空的行；姓名全空则提示。

样式约束（内联组件规范，违反会渲染异常）：
- 只输出片段，**不要** `<!DOCTYPE>/<html>/<head>/<body>`；
- 禁止 `position: fixed`（所以是内联卡片，不是悬浮模态）；
- 用 CSS 变量适配主题：`var(--color-background-primary)` / `var(--color-text-primary)` / `var(--color-border-tertiary)`；
- 字号 ≥11px，字重只用 400/500；表单元素写裸标签（宿主已预置样式）；
- 开头放一个 `<h2 class="sr-only">` 无障碍标题。

### 2c. 备选：本地表单页（需要更大填写空间时）
```bash
python3 ~/.workbuddy/skills/live-char-package/scripts/intake_server.py --out "$ROOT"
# → 打印 http://127.0.0.1:<port>/ ，同时写入 <ROOT>/_intake/url.txt
```
后台启动 → `present_files` 打开地址 → 用户提交后写 `<ROOT>/_intake/briefs.json`，服务自动退出。
⚠️ **会跳到浏览器面板、打断对话连贯性，只有在内联表单不满足时才用**；用完记得确认服务已退出。

### 2d. 兜底：都不可用 → 引导式问答
**一张卡只问一个角色**，绝不把"是否继续添加"和收集混在同一张卡：
- 卡 A（共 3 问）：`语言`（选项：English / 中文 / Português / العربية，其余走自由输入）、
  `姓名`（下方输入框）、`一句话需求`（下方输入框）。
- 卡 B（单独一张，1 问）：`是否继续添加下一个角色？` → `是（最多 10 个）` / `否，开始生成`。
- 选「是」→ 回到卡 A 收集下一个。累计 10 个后不再问。

> **为什么这样设计（踩过的坑）**：问答卡片是「预设选项 + 自由输入框」结构，天然不适合多字段表单——
> ① 把"输出位置"这种一次性设置和角色信息混在一张卡，用户分不清层级；
> ② 还没拿到第 1 个角色就问"是否继续添加"，顺序是错的；
> ③ 用选项承载"请你在下方输入框填写"这种提示语等于白问一题；
> ④ 本地表单页虽然结构对，但要跳出对话、打断连贯性，**不是首选**。
> 所以**主路径 = 内联表单弹窗**（不离开对话 + 真正的新增按钮 + `sendPrompt` 回传），
> 本地页面为备选，问答卡只作兜底且严格一卡一角色。

### 2e. 字段不完整时
只要拿到 **①角色名 ②直播语言 ③一句话需求** 就可开工；其余（开场白/世界观/声音/电商）走默认，不阻塞。
确实缺 ①②③ 中任一项 → 用 AskUserQuestion 补齐那一项，不要脑补。

---

## 步骤 3：生成 + 实时进度（小人从头到脚填色）

### 3.1 初始化并显示进度
```bash
ROOT=$(python3 ~/.workbuddy/skills/live-char-package/scripts/root.py get)
python3 ~/.workbuddy/skills/live-char-package/scripts/progress.py init \
  --root "$ROOT" --chars "Name1|Name2|Name3"
```
然后 **立刻调用 present_files 打开 `"$ROOT/_progress/progress.html"`**（页面每 2 秒自动刷新，一排小人按进度从头到脚填色；全部完成自动停止刷新）。

### 3.2 每个文件写完就更新一次进度（这是"实时"的关键）
每个角色 8 步：`1 character_spec → 2 soul → 3 agent → 4 prologue → 5 标题 → 6 livescript → 7 comment → 8 zip`

```bash
P=~/.workbuddy/skills/live-char-package/scripts/progress.py
python3 $P update --root "$ROOT" --char 0 --step 3 --stage "写 agent.md"
...
python3 $P done   --root "$ROOT" --char 0        # 置 100%，切下一个小人
```
- `--char` 用序号（0 起）或角色名均可。
- **禁止攒到最后一次性更新**：用户看不到过程等于没做进度。

### 3.3 写文件的顺序与规范
严格按 references/conventions.md 的 7 文件规范写（中文 character_spec → soul → agent → prologue → 标题 → livescript → comment）。
comment.md 交给脚本生成，别手写 200 条：
```bash
python3 ~/.workbuddy/skills/live-char-package/scripts/gen_comment.py \
  --out "$ROOT/Name_001/comment.md" --lang en \
  --lines /tmp/name_lines.txt        # 可选：你写的 30-60 条该语言观众弹幕，一行一条
```
不给 `--lines` 时，脚本用内置语料池（en / zh / pt / ar）。其他语种请自己写 `--lines`（质量更高）。

### 3.4 打包
```bash
python3 ~/.workbuddy/skills/live-char-package/scripts/make_zip.py --dir "$ROOT/Name_001"
# → 生成 $ROOT/Name_001.zip（与文件夹平级，便于批量选中；内部仅 soul/agent/prologue/livescript）
```

---

## 步骤 4：质检（必跑，逐个包）

```bash
python3 ~/.workbuddy/skills/live-char-package/scripts/verify.py \
  --dir "$ROOT/Name_001" --lang en
```
校验项：7 文件齐全 / prologue 长度 / 标题 ≤40 字符无括号无 emoji 无破折号 / livescript 无括号无 emoji 无时间戳且首段不复读 prologue / comment 200 条·昵称唯一·键仅 `{nickname,user_url,content}`·无 `reply` / agent 含 §13 现行弹幕规则与 Output Rule / agent 含 §16 自曝禁止硬规则 / zip 内 4 文件。

**出现 FAIL 必须修复后重跑，不许带着 FAIL 交付。**

---

## 步骤 5：交付表格

```bash
python3 ~/.workbuddy/skills/live-char-package/scripts/manifest.py --root "$ROOT"
```
在回复里贴出「序号 / 角色名 / 文件夹名称 / zip」表格，并说明输出目录绝对路径。
最后把本次各包的 zip 用 present_files 一次性交付。

---

## 硬性约定速查（详见 references/conventions.md）

| 项 | 规则 |
|---|---|
| 命名 | 文件夹 `Name_001`；zip 同名放**上层目录、与文件夹平级**（便于批量选中）；**纯角色名，不带 type_ 前缀** |
| 语言 | character_spec 恒中文；soul/agent 按直播语言（非中文直播→英文，中文直播→中文）；口播文件用直播语言 |
| prologue | ≤40 词（英文）/ ≤40 字（中文·阿拉伯等字符型语言） |
| 标题 | ≤40 字符，禁括号 / emoji / 破折号 |
| livescript | 纯 TTS 口播，零括号零 emoji 零时间戳；**首段禁止复读 prologue** |
| comment | JSON 200 条，键仅 `{nickname,user_url,content}`，**严禁 reply 字段**，昵称唯一 |
| agent §13 | 现行规则：无选择性回复 / 无营业态 / 无去重 / 无跳过，每条真实弹幕必回 + Output Rule 纯朗读 |
| agent §16 | 自曝禁止硬规则（禁承认数字人/AI 助手、不透露开发方、言简意赅、自信直接） |

## 脚本清单

| 脚本 | 用途 |
|---|---|
| `scripts/root.py get\|set` | 输出根目录持久化（默认 `~/Desktop/Live Input`） |
| `references/intake_widget.html` | **需求收集内联表单弹窗**（首选，show_widget 直接用） |
| `scripts/intake_server.py --out ROOT` | 备选：本地表单页（需跳出对话，提交后自动退出） |
| `scripts/progress.py init\|update\|done\|render\|show` | 小人填色进度 + 自动刷新 HTML |
| `scripts/gen_comment.py` | 生成 200 条弹幕 JSON |
| `scripts/make_zip.py` | 打 4 文件上传包 |
| `scripts/verify.py` | 质检门禁 |
| `scripts/manifest.py` | 汇总表格 |

运行统一用 `/usr/bin/python3`（managed Python 在 macOS 有 codesign 限制）。
