# live-char-package

WorkBuddy / CodeBuddy 通用 Skill：把「一个角色 brief」变成一套可上传的**数字人直播角色配置包**（7 文件 + 上传 zip）。

面向 DF直播间 / DreamFace 场景，沉淀了全部历史踩坑：弹幕严禁 `reply` 字段、agent §13 现行回复规则（无跳过/无去重）、口播首段禁止复读开场白、多角色 brief 解析陷阱、质检对拉丁语言必须按词而非字符判定重叠等。

## 能力

| 环节 | 说明 |
|---|---|
| 需求收集 | 对话**内联表单弹窗**：每行 姓名 / 语言 / 一句话需求，`＋ 新增一个角色` 上限 10 行，可删行，实时「已填 N / 10」；提交经 `sendPrompt()` 直接回传对话，**不跳出对话** |
| 输出位置 | 默认 `~/Desktop/Live Input`，首次运行弹窗确认，选择持久化到 `state.json` |
| 实时进度 | 小人轮廓按完成度**从头到脚填色**的进度页，2 秒自动刷新，全部完成自动停刷 |
| 机械环节 | 脚本生成 200 条弹幕、打 4 文件上传包、质检门禁、汇总表格 |
| 交付 | 「序号 / 角色名 / 文件夹名称 / 上传包」表格 + zip（**与文件夹平级**，便于批量选中） |

## 目录结构

```
live-char-package/
├── SKILL.md                      # 主流程（触发词 + 5 步 + 硬规则速查）
├── README.md
├── references/
│   ├── conventions.md            # 7 文件规范 / §13 §16 铁律 / 已知坑
│   └── intake_widget.html        # 内联表单弹窗组件（可直接复用）
└── scripts/
    ├── root.py                   # 输出根目录持久化
    ├── intake_server.py          # 备选：本地表单页（会跳出对话，非首选）
    ├── progress.py               # 小人填色进度 + 自动刷新 HTML
    ├── gen_comment.py            # 生成 200 条弹幕 JSON
    ├── make_zip.py               # 打 4 文件上传包
    ├── verify.py                 # 质检门禁
    └── manifest.py               # 汇总表格
```

## 安装

放到用户级 skills 目录即可：

```bash
cp -r live-char-package ~/.workbuddy/skills/
```

触发：对话里说「生成直播间配置包」，或直接把角色 brief 粘进来。

## 使用

统一用系统 Python（macOS managed Python 有 codesign 限制）：

```bash
/usr/bin/python3 scripts/root.py get
/usr/bin/python3 scripts/progress.py init --root "$ROOT" --chars "Name1|Name2"
/usr/bin/python3 scripts/progress.py update --root "$ROOT" --char 0 --step 3 --stage "写 agent.md"
/usr/bin/python3 scripts/gen_comment.py --out "$ROOT/Name_001/comment.md" --lang en --lines my_lines.txt
/usr/bin/python3 scripts/make_zip.py --dir "$ROOT/Name_001"
/usr/bin/python3 scripts/verify.py  --dir "$ROOT/Name_001" --lang en
/usr/bin/python3 scripts/manifest.py --root "$ROOT"
```

每个角色 8 步：`character_spec → soul → agent → prologue → 标题 → livescript → comment → zip`，每写完一个文件调一次 `progress.py update`。

## 产出

```
Live Input/
├── Name_001/          ← 7 个配置文件
└── Name_001.zip       ← 上传包（与文件夹平级），仅含 soul/agent/prologue/livescript
```

7 文件：`character_spec.md`(中文总纲) / `soul.md` / `agent.md` / `prologue.md` / `直播间标题.md` / `livescript.md` / `comment.md`

硬约束：

- prologue ≤40 词（英文）或 ≤40 字（中/阿等字符型语言）
- 标题 ≤40 字符，禁括号 / emoji / 破折号
- livescript 纯 TTS 口播，零括号零 emoji 零时间戳，且**首段禁止复读 prologue**
- comment 恰好 200 条，键仅 `{nickname,user_url,content}`，**严禁 `reply` 字段**，昵称唯一
- agent 必含 §13（无选择性回复 / 无去重 / 每条真实弹幕必回 + Output Rule 纯朗读）与 §16（自曝禁止硬规则）

## 注意

`state.json`（记录本机输出根目录）属本地状态，已在 `.gitignore` 中排除，**不包含在本包内**。
