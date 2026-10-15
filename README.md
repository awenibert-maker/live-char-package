# live-char-package

把「一个角色 brief」变成一套可上传的**数字人直播角色配置包**（7 文件 + 上传 zip）。

面向 DF直播间 / DreamFace 场景。创作部分（人格、口播、文案）由 AI 生成，机械部分（弹幕、打包、质检、进度、汇总表）由脚本完成，全部历史踩坑已沉淀进规则。

## 两个版本怎么选

| | `workbuddy/` | `codex/` |
|---|---|---|
| **用在** | WorkBuddy / CodeBuddy | Codex CLI、Claude Code、Cursor、Aider 或任何能执行命令的 agent |
| **需求收集** | 对话内联表单弹窗（`show_widget` + `sendPrompt`），填完直接回传对话，不跳出 | 命令行问答 / 本地表单页 / 用户粘贴，三选一 |
| **进度可视化** | 进度页自动在结果区打开 | 生成 HTML，自行用浏览器打开 |
| **依赖** | WorkBuddy 平台工具 | 仅 Python 标准库 |

**在 WorkBuddy 里用 → 选 `workbuddy/`；其他环境 → 选 `codex/`。**
两版的生成逻辑、7 个脚本、质检规则完全一致，只是交互方式不同。

## 目录

```
live-char-package/
├── README.md        ← 本文件
├── workbuddy/       ← WorkBuddy 版
│   ├── SKILL.md
│   ├── README.md
│   ├── references/{conventions.md, intake_widget.html}
│   └── scripts/{root, progress, gen_comment, make_zip, verify, manifest, intake_server}.py
└── codex/           ← 通用版
    ├── AGENTS.md    ← Codex CLI 及通用入口
    ├── SKILL.md     ← Claude Code skill 格式
    ├── README.md
    ├── references/conventions.md
    └── scripts/{root, progress, gen_comment, make_zip, verify, manifest, intake_server}.py
```

## 安装

```bash
# WorkBuddy / CodeBuddy
cp -r workbuddy ~/.workbuddy/skills/live-char-package

# Claude Code
cp -r codex ~/.claude/skills/live-char-package

# Codex CLI
# 把 codex/AGENTS.md 的内容并入项目根的 AGENTS.md，脚本目录保留
```

触发：对话里说「生成直播间配置包」，或直接把角色 brief 粘进来。

## 使用（以 codex 版为例）

```bash
ROOT=$(python3 "$SKILL/scripts/root.py" get)                      # 首次运行会创建默认输出目录
python3 "$SKILL/scripts/progress.py" init --root "$ROOT" --chars "Name1|Name2"
python3 "$SKILL/scripts/progress.py" update --root "$ROOT" --char 0 --step 3 --stage "写 agent.md"
python3 "$SKILL/scripts/gen_comment.py" --out "$ROOT/Name_001/comment.md" --lang en --lines my_lines.txt
python3 "$SKILL/scripts/make_zip.py" --dir "$ROOT/Name_001"
python3 "$SKILL/scripts/verify.py"  --dir "$ROOT/Name_001" --lang en
python3 "$SKILL/scripts/manifest.py" --root "$ROOT"
```

- 每个角色 8 步：`character_spec → soul → agent → prologue → 标题 → livescript → comment → zip`
- **每写完一个文件更新一次进度**，用户才能实时看到小人从头到脚填色
- 进度页：`<ROOT>/_progress/progress.html`（2 秒自动刷新，全部完成自动停刷）

## 产出

```
Live Input/
├── Name_001/          ← 7 个配置文件
└── Name_001.zip       ← 上传包（与文件夹平级，便于批量选中）
```

7 文件：`character_spec.md`(中文总纲) · `soul.md` · `agent.md` · `prologue.md` · `直播间标题.md` · `livescript.md` · `comment.md`
上传 zip 内含：`soul.md` / `agent.md` / `prologue.md` / `livescript.md`

## 硬约束

| 项 | 规则 |
|---|---|
| 命名 | 文件夹 `Name_001`，纯角色名，不带 `type_` 前缀 |
| prologue | ≤40 词（英文）/ ≤40 字（中·阿等字符型语言） |
| 标题 | ≤40 字符，禁括号 / emoji / 破折号 |
| livescript | 纯 TTS 口播，零括号零 emoji 零时间戳，**首段禁止复读 prologue** |
| comment | 200 条，键仅 `{nickname,user_url,content}`，**严禁 `reply` 字段**，昵称唯一 |
| agent §13 | 无选择性回复 / 无跳过 / 无去重，每条真实弹幕必回 + Output Rule 纯朗读 |
| agent §16 | 自曝禁止：禁承认数字人 / AI 助手，不透露开发方，言简意赅 |

完整规范见 `workbuddy/references/conventions.md` 或 `codex/references/conventions.md`。

## 相关

反馈处理脚本在另一个仓库：[THS_WorkScript](https://github.com/awenibert-maker/THS_WorkScript)。
