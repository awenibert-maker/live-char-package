# live-char-package · 通用版

把「一个角色 brief」变成一套可上传的**数字人直播角色配置包**（7 文件 + 上传 zip）。
面向 DF直播间 / DreamFace 场景，沉淀了全部历史踩坑。

**通用版特性**：不依赖任何平台专属工具，只用标准库脚本 + 文件读写。Codex CLI、Claude Code、Cursor、Aider 或任何能执行命令的 agent 都能跑。

## 目录

```
live-char-package-codex/
├── AGENTS.md              # 指令入口（Codex CLI / 通用）
├── SKILL.md               # 指令入口（Claude Code skill 格式）
├── README.md
├── references/
│   └── conventions.md     # 7 文件规范 / §13 §16 铁律 / 已知坑
└── scripts/
    ├── root.py            # 输出根目录持久化
    ├── intake_server.py   # 本地需求表单页（有浏览器时用）
    ├── progress.py        # 小人填色进度 + 自动刷新 HTML
    ├── gen_comment.py     # 生成 200 条弹幕 JSON
    ├── make_zip.py        # 打 4 文件上传包
    ├── verify.py          # 质检门禁
    └── manifest.py        # 汇总表格
```

## 安装

### Codex CLI（OpenAI）
把整个目录放到你的项目下，或把 `AGENTS.md` 的内容并入项目根的 `AGENTS.md`；脚本目录保留，指令里写清脚本路径。
全局生效可放 `~/.codex/AGENTS.md`（需在其中写明脚本的绝对路径）。

### Claude Code
```bash
cp -r live-char-package-codex ~/.claude/skills/live-char-package
```

### 其他 agent（Cursor / Aider / 自研）
把 `AGENTS.md` 作为系统指令或项目规则文件引入，脚本目录保留即可。

## 用法

统一用 `python3`（Windows 用 `python`）。以下 `$SKILL` 指脚本所在目录，`$ROOT` 指输出根目录。

```bash
ROOT=$(python3 "$SKILL/scripts/root.py" get)                       # 首次运行会创建默认目录
python3 "$SKILL/scripts/progress.py" init --root "$ROOT" --chars "Name1|Name2"
python3 "$SKILL/scripts/progress.py" update --root "$ROOT" --char 0 --step 3 --stage "写 agent.md"
python3 "$SKILL/scripts/gen_comment.py" --out "$ROOT/Name_001/comment.md" --lang en --lines my_lines.txt
python3 "$SKILL/scripts/make_zip.py" --dir "$ROOT/Name_001"
python3 "$SKILL/scripts/verify.py"  --dir "$ROOT/Name_001" --lang en
python3 "$SKILL/scripts/manifest.py" --root "$ROOT"
```

进度页：`<ROOT>/_progress/progress.html`，浏览器打开即可，2 秒自动刷新，全部完成自动停刷。

## 产出

```
Live Input/
├── Name_001/          ← 7 个配置文件
└── Name_001.zip       ← 上传包（与文件夹平级），仅含 soul/agent/prologue/livescript
```

7 文件：`character_spec.md`(中文总纲) / `soul.md` / `agent.md` / `prologue.md` / `直播间标题.md` / `livescript.md` / `comment.md`

硬约束：prologue ≤40 词(英) 或 ≤40 字(字符型语言)；标题 ≤40 字符无括号无 emoji 无破折号；livescript 纯口播零括号零 emoji 零时间戳且首段不复读 prologue；comment 200 条、键仅 `{nickname,user_url,content}`、**严禁 `reply` 字段**。

## 与 WorkBuddy 版的差异

WorkBuddy 版（本仓库 `live-char-package/` 子目录）额外用到了 3 个平台专属工具，通用版全部去掉：

| 能力 | WorkBuddy 版 | 通用版 |
|---|---|---|
| 需求收集 | `show_widget` 对话内联表单 + `sendPrompt()` 回传 | 命令行问答 / 本地表单页（`intake_server.py`）/ 用户粘贴 |
| 交付 | `present_files` 展示进度页与 zip | 打印路径，用户自行打开 |
| 位置确认 | `AskUserQuestion` 弹卡 | 命令行询问 |

生成逻辑、质检规则、脚本完全共用。若你在 WorkBuddy 里用，建议用 WorkBuddy 版（交互更顺）；其他环境用本通用版。

## 注意

`state.json`（记录本机输出根目录）属本地状态，不要提交到仓库。
