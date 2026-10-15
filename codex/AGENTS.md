# 直播间角色配置包生成器

把「一个角色 brief」变成一套可上传的**数字人直播角色配置包**（7 文件 + 上传 zip）。
面向 DF直播间 / DreamFace 场景，沉淀了全部历史踩坑。

> **通用版**：不依赖任何平台专属工具。Codex CLI、Claude Code、Cursor、Aider 或任何能执行命令、读写文件的 agent 都能跑。
> 下文中 `$SKILL` = 本文件所在目录。示例命令用 `python3`（Windows 若不可用请换成 `python`）。

## 何时使用

- 用户说「生成直播间配置包」「做一个角色包」「生成数字人角色配置」
- 或一次性发来多个角色 brief（姓名 / 语言 / 需求）

## 总流程

```
1 收集需求 → 2 确认输出位置 → 3 生成 + 实时进度 → 4 质检 → 5 交付表格
```

**创作部分（人格、口播、文案）由你写；机械部分（弹幕、打包、质检、进度、表格）一律调脚本。**

---

## 步骤 1：收集需求

### 1a. 用户已粘贴 brief → 直接解析，不要再问一遍
**解析铁律**（踩过坑）：
- `[时间戳] ~角色名:` 之后的内容 = 该角色的**聊天记录**，不是规格；
- 另起一行、以 `角色名:` 开头的块 = **另一个独立角色**，不要把后一个名字误读成前一个角色的属性。

### 1b. 用户没给 brief → 三选一
| 方式 | 怎么用 | 适用 |
|---|---|---|
| **A 命令行问答**（默认） | 直接问：姓名？语言？一句话需求？收集完问「还要加吗」，上限 10 个 | 任何环境 |
| **B 本地表单页** | `python3 "$SKILL/scripts/intake_server.py" --out "$ROOT"` → 打印 URL，让用户在浏览器打开填写 | 有浏览器时，适合一次填多个 |
| **C 让用户粘贴** | 请用户按「姓名 / 语言 / 需求」格式一次给全，你再解析 | 用户习惯批量粘贴时 |

方式 B 说明：服务提交后写 `<ROOT>/_intake/briefs.json`（`[{name,lang,need}]`）并自动退出；若文件迟迟未出现，等用户告知后再读，不要空转轮询。

### 1c. 字段不完整
拿到 **①角色名 ②直播语言 ③一句话需求** 即可开工，其余走默认不阻塞。缺 ①②③ 任一项才追问，不要脑补。

---

## 步骤 2：确认输出位置

```bash
python3 "$SKILL/scripts/root.py get"
```
- **返回路径** → 直接用。
- **返回空**（本机首次）→ 脚本已自动创建默认目录（优先桌面 `Live Input`）。此时告知用户默认位置，并问是否要换；要换则 `python3 "$SKILL/scripts/root.py set" --path "<绝对路径>"`。

**目录结构**（zip 与文件夹**平级**，便于批量选中）：
```
Live Input/
├── Name_001/          ← 7 个配置文件
├── Name_001.zip       ← 上传包，仅含 soul/agent/prologue/livescript
├── _intake/           ← 需求收集
└── _progress/         ← 进度页
```

---

## 步骤 3：生成 + 实时进度

### 3.1 初始化
```bash
ROOT=$(python3 "$SKILL/scripts/root.py" get)
python3 "$SKILL/scripts/progress.py" init --root "$ROOT" --chars "Name1|Name2"
```
生成 `<ROOT>/_progress/progress.html`（一排小人按完成度**从头到脚填色**，2 秒自动刷新，全部完成自动停刷）。
**告诉用户该文件的绝对路径，让他用浏览器打开即可实时看到进度。**

### 3.2 每写完一个文件就更新进度
每个角色 8 步：`1 character_spec → 2 soul → 3 agent → 4 prologue → 5 标题 → 6 livescript → 7 comment → 8 zip`

```bash
python3 "$SKILL/scripts/progress.py" update --root "$ROOT" --char 0 --step 3 --stage "写 agent.md"
python3 "$SKILL/scripts/progress.py" done   --root "$ROOT" --char 0
```
- `--char` 用序号（0 起）或角色名。
- **禁止攒到最后一次性更新**。
- 想看文本进度：`python3 "$SKILL/scripts/progress.py" show --root "$ROOT"`

### 3.3 写文件顺序与规范
严格按 `references/conventions.md`：中文 `character_spec` → `soul` → `agent` → `prologue` → 标题 → `livescript` → `comment`。

comment.md 交给脚本，别手写 200 条：
```bash
python3 "$SKILL/scripts/gen_comment.py" --out "$ROOT/Name_001/comment.md" --lang en --lines my_lines.txt
```
`--lines` 是你写的 30-60 条该语言观众弹幕（一行一条），质量明显高于内置池，推荐用。
不给则用内置语料池（en / zh / pt / ar）；其他语种必须自己写 `--lines`。

### 3.4 打包
```bash
python3 "$SKILL/scripts/make_zip.py" --dir "$ROOT/Name_001"   # → $ROOT/Name_001.zip
```

---

## 步骤 4：质检（必跑，逐个包）

```bash
python3 "$SKILL/scripts/verify.py" --dir "$ROOT/Name_001" --lang en
```
校验：7 文件齐全 / prologue 长度 / 标题 ≤40 字符无括号无 emoji 无破折号 / livescript 无括号无 emoji 无时间戳且首段不复读 prologue / comment 200 条·昵称唯一·键仅 `{nickname,user_url,content}`·无 `reply` / agent 含 §13 现行弹幕规则与 Output Rule / agent 含 §16 自曝禁止硬规则 / zip 内 4 文件。

**出现 FAIL 必须修复后重跑，不许带着 FAIL 交付。**

---

## 步骤 5：交付

```bash
python3 "$SKILL/scripts/manifest.py" --root "$ROOT"
```
把「序号 / 角色名 / 文件夹名称 / 上传包」表格贴给用户，并说明输出目录的绝对路径。

---

## 硬性约定速查（详见 references/conventions.md）

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

## 脚本清单

| 脚本 | 用途 |
|---|---|
| `scripts/root.py get\|set` | 输出根目录持久化 |
| `scripts/intake_server.py --out ROOT` | 本地需求表单页（有浏览器时用） |
| `scripts/progress.py init\|update\|done\|render\|show` | 小人填色进度 + 自动刷新 HTML |
| `scripts/gen_comment.py` | 生成 200 条弹幕 JSON |
| `scripts/make_zip.py` | 打 4 文件上传包 |
| `scripts/verify.py` | 质检门禁 |
| `scripts/manifest.py` | 汇总表格 |

## 跨平台注意

- 命令用 `python3`（Windows 可能是 `python`）。脚本只用标准库，无需装依赖。
- 默认输出目录自动适配：优先桌面 `Live Input`，找不到桌面则用家目录下的 `Live Input`。
- macOS 上若 Python 报 codesign 相关错误，改用系统 Python（`/usr/bin/python3`）。
- 脚本全部通过参数接收路径，可放在任意目录；`state.json` 记录在 skill 目录下，属本地状态，不要提交到仓库。
