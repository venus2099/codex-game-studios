# Codex Game Studios: quick reference

This project uses [Codex Game Studios](https://github.com/venus2099/codex-game-studios), a Codex port of [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios). Full guide: [English](https://github.com/venus2099/codex-game-studios/blob/main/guide/GUIDE.md) · [简体中文](https://github.com/venus2099/codex-game-studios/blob/main/guide/GUIDE.zh-CN.md)

**First run:**
1. Start `codex` in this folder and trust the project.
2. Type `/hooks` and trust the hooks.
3. Describe what you want, or type `$start`.

**Every day:**
- Talk normally and Codex picks the matching skill. You can also name it: `$brainstorm`, `$sprint-plan`, `$dev-story`, `$help`.
- Questions come as numbered options; reply with a number.
- Art, story, player-facing text and music decisions are always yours.
- A stuck agent escalates to a stronger model automatically, then asks you.

**Settings:** `codex-port/model_tiers.toml` (models, escalation) and `codex-port/skills.toml` (which skills start automatically). After you change them, run:

```bash
python -I codex-port/convert_to_codex.py . .
```

Your own rules go in `PROJECT-NOTES.md`. Codex and Claude Code both follow it; after you edit it, run the command above so Codex's copy in `AGENTS.md` is refreshed.

---

# Codex Game Studios 速查

本项目使用 [Codex Game Studios](https://github.com/venus2099/codex-game-studios)，它是 [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) 的 Codex 移植版。完整使用指南：[English](https://github.com/venus2099/codex-game-studios/blob/main/guide/GUIDE.md) · [简体中文](https://github.com/venus2099/codex-game-studios/blob/main/guide/GUIDE.zh-CN.md)

**第一次使用：**
1. 在本文件夹启动 `codex`，选择信任这个项目。
2. 输入 `/hooks`，信任钩子。
3. 描述你想做什么，或者输入 `$start`。

**日常使用：**
- 直接说话，Codex 会自动挑合适的技能；也可以指定，比如 `$brainstorm`、`$sprint-plan`、`$dev-story`、`$help`。
- 提问会以编号选项的形式出现，回复数字即可。
- 美术、故事、玩家可见的文本、音乐这四类决定，始终由你来定。
- agent 卡住时会自动换更强的模型重试，还不行就来问你。

**设置：** `codex-port/model_tiers.toml` 管模型和升级顺序，`codex-port/skills.toml` 管哪些技能能自动触发。改完后运行：

```bash
python -I codex-port/convert_to_codex.py . .
```

你自己定的规矩写在 `PROJECT-NOTES.md` 里，Codex 和 Claude Code 都会遵守。改完后运行上面那条命令，刷新 `AGENTS.md` 里给 Codex 的副本。
