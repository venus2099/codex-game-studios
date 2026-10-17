<!-- Project rules shared by Codex and Claude Code. Edit this file: CLAUDE.md
     imports it, and convert_to_codex.py copies it into AGENTS.md. -->

# Project notes

### Creative decisions are always the user's

`project.yaml` sets `modes.automation: guided` and lists four creative
categories in `modes.automation_always_ask`. Upstream only consults that list
in autonomous mode; in this project it applies in **every** mode. Treat any
decision in these categories as **major**: present options with your
recommendation, ask in chat, and wait. Never "recommend and proceed", and never
pick-and-log.

| Category | Covers |
|---|---|
| `art_and_visuals` | art style and art bible, character/creature/environment look, color palette, UI visual style, VFX look, concept and asset specs |
| `story_and_narrative` | plot, characters and their arcs, world and lore, factions, quests, endings, tone |
| `player_facing_text` | dialogue, barks, item/skill/quest descriptions, UI copy, tutorials, store page and marketing copy, patch notes for players |
| `music_and_audio` | music direction and tracks, sound palette and SFX style, voice casting and VO direction, audio mix intent |

This includes decisions made by subagents: a subagent returns these as
questions instead of deciding. Technical work around creative content (file
formats, import settings, wiring an approved line or sound into the game)
follows the normal guided rules.

### 交付与重试规矩

- 开始一项实现或修复任务前，先用一句话说清楚这次要交付什么（比如 PR 标题、要改哪个文件，或者预期看到的命令输出）。
- 遇到以下任一情况，就停下来先找我确认：
  （a）超过 10 分钟一处修改都没有做（只适用于写代码、修 bug 这类实现任务；设计讨论、调研、写文档不算）；
  （b）同一种方法失败了两次。
- 任何一个问题最多只试两次，不要再继续重试。这条优先于「卡住自动升级」：同一个问题失败两次后直接来问我，不要换更强的模型重试。升级机制只用于其他卡住的情况。
- 子 agent 同样遵守：同一个问题失败两次就返回 `BLOCKED: two attempts failed`，并说明两次各试了什么，由主会话来问我。

### 模型提醒

开始系统架构、技术决策、系统拆分、阶段评审这类工作前（`create-architecture`、`architecture-decision`、`map-systems`、`gate-check`、`review-all-gdds`、`architecture-review`），如果当前会话不是最强的模型（Claude 用 Fable，Codex 用 `gpt-6-astra`），先提醒我一次可以切换，再继续。
