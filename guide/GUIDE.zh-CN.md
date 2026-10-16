# Codex Game Studios 使用指南

[English](GUIDE.md) · **简体中文** · [返回 README](../README.zh-CN.md)

1. [整体结构](#1-整体结构)
2. [安装](#2-安装)
3. [新建一个游戏](#3-新建一个游戏)
4. [用在已有的游戏项目上](#4-用在已有的游戏项目上)
5. [日常使用](#5-日常使用)
6. [模型与升级机制](#6-模型与升级机制)
7. [自动化模式与创作决定](#7-自动化模式与创作决定)
8. [配置参考](#8-配置参考)
9. [重新生成 Codex 配置层](#9-重新生成-codex-配置层)
10. [钩子与安全规则](#10-钩子与安全规则)
11. [跟进原版更新（维护者）](#11-跟进原版更新维护者)
12. [常见问题](#12-常见问题)
13. [与原版的差别](#13-与原版的差别)

---

## 1. 整体结构

**模板和你的游戏是分开的两个文件夹。** 这个仓库只需要克隆一次，克隆下来的就是模板。每做一个游戏，就用脚本把模板复制到一个新文件夹，或者装进一个已有的项目。之后在那个文件夹里做游戏，模板本身保持不动。

一个游戏项目里有这些东西：

| 路径 | 是什么 |
|---|---|
| `AGENTS.md` | 给 Codex 的项目说明书，每次会话开始时自动读取。这个文件是脚本生成的，只有其中的「Project notes」区块归你自己写。 |
| `CLAUDE.md`、`.claude/` | 原版工作室的全部内容：agent 角色、技能、规则、文档、钩子。这是唯一的权威来源，Codex 配置层都指向这里。 |
| `.agents/skills/` | 每个技能对应一个很小的 Codex 入口文件，指向 `.claude/skills/<名字>/SKILL.md`。 |
| `.codex/agents/` | 49 个 agent 对应的 Codex 自定义 agent，以及移植版新增的执行 agent 和升级 agent。 |
| `.codex/hooks.json`、`.codex/hooks/` | 原版的钩子，通过一个适配脚本接入 Codex。 |
| `.codex/rules/ccgs.rules` | 被禁止的命令。 |
| `project.yaml` | 项目设置，比如引擎、自动化模式、评审强度等。 |
| `codex-port/` | 转换脚本和它的配置（`model_tiers.toml`、`skills.toml`、`preset/`）。 |
| `design/`、`docs/`、`production/`、`src/`、`tests/` | 你的游戏本身：设计文档、技术架构、冲刺与任务卡、代码、测试。 |

## 2. 安装

准备工作：

- **Codex CLI**：已在 0.162.1 版本上测试。运行 `codex features list`，确认 `hooks` 和 `multi_agent` 都是 `true`（默认就是）。
- **git 和 bash**：Windows 上装 [Git for Windows](https://git-scm.com/download/win) 就都有了。钩子要用 `bash` 运行，所以它必须在 `PATH` 上。
- **Python 3.11 及以上**：只有重新生成 Codex 配置层时才需要（见第 9 节）。

克隆模板：

```bash
git clone https://github.com/venus2099/codex-game-studios.git ~/code/codex-game-studios
```

Windows 用户还要运行一次下面这条命令。工作室的目录层级很深，不开长路径支持的话，git 会报「Filename too long」：

```bash
git config --global core.longpaths true
```

## 3. 新建一个游戏

```bash
bash ~/code/codex-game-studios/codex-port/new-game.sh ~/code/my-game
```

目标文件夹必须是新的或空的。脚本会依次：
- 运行 `git init`，并打开长路径支持；
- 复制模板的 `.gitignore` 和 `.gitattributes`；
- 装好工作室的全部文件。

它不会提交任何东西。

然后进入新项目，启动 Codex：

```bash
cd ~/code/my-game
codex
```

1. Codex 问是否信任这个项目时，选信任。只有信任过的项目，Codex 才会启用项目自己的配置（agent、钩子、规则）。
2. 输入 `/hooks`，信任项目自带的钩子。每个项目只需要确认一次。
3. 描述你想做的游戏，或者输入 `$start` 开始新手引导。

也可以在任意文件夹打开 Codex，让它替你运行脚本：

> 运行 `bash ~/code/codex-game-studios/codex-port/new-game.sh ~/code/my-game`，把脚本输出的下一步告诉我，不要提交任何东西。

注意：Codex 只在会话启动时读取 `AGENTS.md`、技能、agent 和钩子。脚本跑完后，要退出 Codex，进到新文件夹里重新启动。

## 4. 用在已有的游戏项目上

1. 先提交项目当前的改动。这一步不是必须的，但方便之后查看脚本加了什么。
2. 运行：

   ```bash
   bash ~/code/codex-game-studios/codex-port/add-to-project.sh ~/code/existing-game
   ```

   这个脚本可以放心地重复运行：
   - **不覆盖任何文件**：项目里没有的文件直接复制进去；已有但内容不同的文件，你的文件保持原样，模板的版本另存为旁边的 `文件名.ccgs-new`。
   - **`.gitignore` 只追加工作室相关的条目**：包括本地设置、会话日志等。原版里引擎和构建相关的忽略规则不会合并进来，因为它们可能误伤你项目里有意提交的文件（比如 `*.csproj`）。
   - **不会提交任何东西。**
3. **如果项目原本就有 `AGENTS.md`，必须合并**。不合并的话，Codex 读的还是你原来的文件，工作室的规则不会生效（技能本身还能用）。最简单的办法是直接让 Codex 合并：

   > 把我 AGENTS.md 里原来的规则移到 AGENTS.md.ccgs-new 的「Project notes」区块里，然后用它替换 AGENTS.md，再删掉 .ccgs-new 文件。

   其他 `.ccgs-new` 文件也照这个思路处理。
4. 在项目根目录启动 Codex，信任项目，再输入 `/hooks` 信任钩子。
5. 说「分析一下这个已有项目」，或者输入 `$adopt`。它会对照工作室的流程检查你现有的代码和文档，生成一份迁移计划，保存在 `docs/adoption-plan-日期.md`。

   之后常用的技能：
   - `$setup-engine`：登记项目使用的引擎和版本。
   - `$reverse-document`：根据已有代码反推出设计文档。
   - `$project-stage-detect`：判断项目目前处在哪个阶段。

工作室默认的代码目录是：Godot 用 `src/`，Unity 用 `Assets/`，Unreal 用 `Source/`。如果你的代码放在别处，迁移计划里会指出来，由你决定是挪代码还是改配置。

## 5. 日常使用

**直接说话就行。** Codex 能看到每个技能的简介，会自动启动最匹配的那个。比如说「帮我想几个游戏点子」会启动 `brainstorm`，「我接下来该干嘛？」会启动 `help`。想指定某个技能时，在话里带上它的名字（「用 brainstorm」），或者直接输入 `$名字`。输入 `/skills` 可以查看全部技能。默认 74 个技能都能自动触发，想改的话见第 8 节的 `skills.toml`。

**提问以编号选项的形式出现。** 原版用 Claude 的选项卡提问。在 Codex 里，你会看到一个简短的问题、几个编号选项，以及 Codex 推荐的那一个。回复数字或者直接用自己的话回答都行。Codex 会一直等你回答；你没回答，它不会当成你已经同意。

**一个项目的典型流程：**

| 阶段 | 常用技能 |
|---|---|
| 构思 | `$start`、`$brainstorm`、`$setup-engine`、`$prototype` |
| 系统设计 | `$art-bible`、`$map-systems`、`$design-system`、`$design-review`、`$review-all-gdds` |
| 技术准备 | `$create-architecture`、`$architecture-decision`、`$create-control-manifest`、`$test-setup` |
| 预制作 | `$create-epics`、`$create-stories`、`$ux-design`、`$vertical-slice` |
| 制作 | `$sprint-plan`、`$story-readiness`、`$dev-story`、`$code-review`、`$story-done`、`$sprint-status` |
| 打磨与测试 | `$qa-plan`、`$smoke-check`、`$playtest-report`、`$perf-profile`、`$team-polish` |
| 发布 | `$release-checklist`、`$launch-checklist`、`$patch-notes`、`$changelog` |
| 随时可用 | `$help`、`$gate-check`、`$scope-check`、`$estimate`、`$bug-report`、`$settings` |

`$gate-check` 用来判断项目能不能进入下一个阶段。`team-*` 系列技能（`$team-combat`、`$team-narrative`、`$team-ui` 等）会调动整个部门来完成一个功能。

**会话与记忆。** 工作室把进度存档保存在 `production/session-state/active.md`，每次会话开始时由钩子自动加载。用 `/new` 开新会话或者程序崩溃之后，直接接着干就行。想看进度摘要的话，问一句「我们做到哪了？」。

## 6. 模型与升级机制

原版给每个技能和 agent 都标了难度。移植版在 `codex-port/model_tiers.toml` 里把这些难度对应到 Codex 的模型：

| 档位 | 原版 | 默认模型（推理强度） | 用在哪 |
|---|---|---|---|
| heavy | opus | `gpt-6-astra`（high） | `creative-director`、`producer`、`technical-director` 三位总监；`$gate-check`、`$architecture-review`、`$review-all-gdds` 三个技能 |
| standard | sonnet，以及原版跟随会话模型的 agent | `gpt-6.1-sol`（high） | 其余 46 个 agent |
| light | haiku | `gpt-6-luna`（high） | `$help`、`$onboard`、`$project-stage-detect`、`$scope-check`、`$sprint-status` |

Codex 的技能没法自己切换模型，所以各档的处理方式不同：

- **agent**：固定使用所在档位的模型。
- **light 技能**：交给 `ccgs-light-runner` 执行。这是一个跑在快速模型上的 agent，做完把结果交回来；中途需要你做决定时，问题会转给你。
- **heavy 技能**：会先看当前会话用的是什么模型。如果不是 heavy 档的模型，Codex 会提醒你一次可以用 `/model` 切换，然后继续。
- **其余技能**：在你的会话里运行，用的是你当前会话的模型。

**省钱建议**：大部分工作都在主会话里完成，所以开销主要取决于你的默认模型。想省钱的话，日常用 `gpt-6.1-sol`，碰到 heavy 技能提醒时，再用 `/model` 切到 `gpt-6-astra`。

**升级机制**：agent 做不出来或者对结果没把握时，会返回以 `BLOCKED:` 开头的报告，而不是交一个看起来像完成了的东西。这时 Codex 会逐级升级，每次升级都会告诉你一声：

1. `ccgs-escalation`（`gpt-6-astra`，high）
2. `ccgs-escalation-max`（`gpt-6-astra`，xhigh）
3. 停下来问你，并说明每一级都试过什么。

如果结果明显不能用（测试还是没过、不满足验收标准、和设计文档矛盾），Codex 也会主动升级。heavy 档的 agent 本来就是 astra + high，所以直接跳到第 2 级。同一步在每一级最多只试一次。需要你回答的问题和创作类决定永远不会被升级，而是直接交给你。

想调整的话，改 `model_tiers.toml`，然后重新生成（见第 9 节）：
- **改某一档的模型或推理强度**：修改 `[tiers.*]`。
- **改升级顺序**：修改 `[escalation] ladder`。
- **把单个 agent 或技能换到别的档位**：在 `[overrides]` 里加一行，比如 `"game-designer" = "heavy"`。

模型名称必须是你的 Codex 账号能用的，输入 `/model` 可以查看。

## 7. 自动化模式与创作决定

`project.yaml` 里的 `modes.automation` 决定 Codex 多久停下来问你一次：

| 模式 | 行为 |
|---|---|
| `collaborative` | 每个决定都问你，每次写文件都要你先确认。 |
| `guided`（模板默认） | 大事问你（引擎、核心玩法、范围变更、改起来代价大的事），小事自己决定，然后告诉你它选了什么。新建文件前会先问你，修改已有文件时给个简短说明就直接改。 |
| `autonomous` | 除了 `modes.automation_always_ask` 里列出的类别，其他都由 Codex 自己决定，并把每个决定记录到 `production/session-logs/decision-log.md`。 |

要切换模式，说一句「把 automation 改成 collaborative」就行（Codex 会调用 `$settings`），也可以直接编辑 `project.yaml`。`$start` 新手引导时会问你选哪种模式，想保持 guided 的话记得再选一次。

**创作类决定始终由你来定。** 模板在 `modes.automation_always_ask` 里加了四个类别：
- `art_and_visuals`
- `story_and_narrative`
- `player_facing_text`
- `music_and_audio`

原版只在 autonomous 模式下才会查看这个清单，所以 `AGENTS.md` 的「Project notes」区块另外规定：这四类决定在任何模式下都必须问你。它们涵盖：
- **美术**：美术风格、角色和场景的外观、配色、UI 外观、特效。
- **故事**：剧情、角色、世界观和背景设定、任务、结局、基调。
- **玩家可见的文本**：对话、道具和技能说明、界面文字、教程、商店页。
- **音乐与音效**：音乐方向、音效风格、配音。

围绕已确定内容的技术工作仍按普通规则处理，比如文件格式、导入设置、把你批准的台词或音效接进游戏。

子 agent 没法直接和你对话，遇到这类决定时，会把问题带回来交给你。

## 8. 配置参考

| 文件 | 控制什么 |
|---|---|
| `codex-port/model_tiers.toml` | 每一档对应的模型和推理强度、升级顺序、单个 agent 或技能的档位覆盖 |
| `codex-port/skills.toml` | `implicit_invocation = "all"` 表示所有技能都能自动触发；改成 `"upstream"` 恢复原版行为，即 `$dev-story`、`$story-done`、`$hotfix`、`$day-one-patch` 只在你手动输入时才运行 |
| `codex-port/preset/project-notes.md` | 新生成的 `AGENTS.md` 里「Project notes」的默认内容（也就是创作决定那条规则） |
| `codex-port/preset/project-modes.yaml` | 全新构建模板时，写进 `project.yaml` 的默认 `modes:` 区块 |
| `project.yaml` | 引擎、自动化模式、必问类别、评审强度等工作室设置。可以用 `$settings` 修改，也可以直接编辑。 |
| `project.local.yaml` | 你个人对 `project.yaml` 的覆盖设置，不会被 git 提交 |
| `AGENTS.md` 的「Project notes」 | 你给 Codex 定的项目规矩 |

**自己的规矩应该写在哪：**

| 规矩类型 | 写在哪里 |
|---|---|
| 所有项目都适用的个人习惯（比如「用中文回复」） | `~/.codex/AGENTS.md` |
| 这个项目的简短规矩 | `AGENTS.md` 的「Project notes」区块 |
| 很长、很细的规矩 | 单独写一个文件，再在 Project notes 里加一行说明什么时候去读它 |
| 只针对某类文件的规矩 | `.claude/rules/` 里的规则文件，开头用 `paths:` 指定适用的文件 |
| 项目设置 | `project.yaml`，或者用 `$settings` 修改 |
| 绝对不能发生的事 | `.codex/rules/` 或钩子。`AGENTS.md` 只是给 AI 的指引，规则和钩子才是强制执行的 |

Codex 默认最多读取 32 KiB 的 `AGENTS.md`，生成出来的文件大约 23 KiB，所以 Project notes 请尽量写得简短。Project notes 放在文件靠前的位置，就算文件超出上限，它也不会被截掉。

## 9. 重新生成 Codex 配置层

修改了 `model_tiers.toml`、`skills.toml` 或 `.claude/` 里的任何内容之后，在项目根目录运行：

```bash
python -I codex-port/convert_to_codex.py . .
```

它只重写下面这些生成出来的文件：
- `AGENTS.md`（「Project notes」区块会保留）
- `.agents/skills/`
- `.codex/agents/`
- `.codex/hooks.json`
- `.codex/hooks/codex-hook.sh`
- `.codex/rules/ccgs.rules`
- `README-CODEX.md`

你的代码、设计文档、`production/` 和 `project.yaml` 都不会被改动。如果你把输出目录指向一个已存在、非空、又不是源目录本身的文件夹，脚本会拒绝运行。

在模板里改设置，影响的是以后新建的游戏；在某个游戏项目里改，只影响这一个游戏。

## 10. 钩子与安全规则

| 时机 | 做什么 |
|---|---|
| 会话开始 | 加载进度存档和最近的提交，检查项目缺了什么 |
| 执行 shell 命令前 | 检查 `git commit` 和 `git push`，比如拦下包含损坏 JSON 数据文件的提交 |
| 修改文件后 | 校验资源文件（比如 JSON 语法），标记被修改的技能 |
| 压缩上下文、会话结束、子 agent 启停 | 保存会话状态，记录 agent 的活动 |

Codex 用 `apply_patch` 修改文件，而原版的钩子需要的是 Claude 格式的 `file_path` 输入。`.codex/hooks/codex-hook.sh` 负责在两者之间转换，所以原版的钩子脚本不用做任何改动就能运行。

`.codex/rules/ccgs.rules` 禁止以下命令：
- `rm -rf`（包括各种参数写法）
- `git push --force`
- `git reset --hard`
- `git clean -f`
- `sudo`
- `chmod 777`

想检查某条命令会不会被拦截：

```bash
codex execpolicy check --rules .codex/rules/ccgs.rules git reset --hard
```

如果你的 Codex 版本不加载项目里的规则文件，把它复制到 `~/.codex/rules/` 即可。

## 11. 跟进原版更新（维护者）

1. 下载新版的 Claude Code Game Studios。
2. 用它构建一份全新的模板。这一步会同时应用 preset，去掉原版的 `.github/`，并把原版的 README、CHANGELOG 等文件移到 `upstream/` 里：

   ```bash
   python -I codex-port/convert_to_codex.py <原版文件夹> <新文件夹>
   ```

3. 把本仓库里的 `README.md`、`README.zh-CN.md`、`guide/` 和 `LICENSE` 复制到新文件夹。
4. 对比新旧两个文件夹的差异，确认没问题后提交。

已有的游戏项目可以按 `upstream/` 里原版的 `UPGRADING.md` 更新 `.claude/`，然后在项目里原地重新生成。

## 12. 常见问题

| 现象 | 解决办法 |
|---|---|
| Windows 上 git 报 `Filename too long` | 运行 `git config --global core.longpaths true`（新建和安装脚本已经对单个项目开启了） |
| 钩子一直没有运行 | 输入 `/hooks` 信任钩子；确认 `bash` 在 `PATH` 上；从项目根目录启动 Codex |
| Codex 不遵守工作室的规则 | 在项目根目录启动 Codex；如果存在 `AGENTS.md.ccgs-new`，按第 4 节合并 |
| 技能没有自动触发 | 在话里带上技能名字（「用 sprint-plan」），或者直接输入 `$sprint-plan`；检查 `skills.toml` 的设置 |
| 派不出 agent | 运行 `codex features list`，确认 `multi_agent` 是 `true`。派不出来时，Codex 会读取 `.claude/agents/<名字>.md`，自己扮演这个角色 |
| 提示模型名称无效 | 你的账号可能用不了这个模型。修改 `model_tiers.toml` 后重新生成 |
| 转换脚本报 Python 版本太低 | 脚本用到了 `tomllib`，需要 Python 3.11 或以上 |

## 13. 与原版的差别

| 原版（Claude Code） | 移植版（Codex） |
|---|---|
| `/技能名` | `$技能名`，或者直接用自然语言描述 |
| 选项卡提问（`AskUserQuestion`） | 在聊天里列出编号选项，等你回复 |
| 通过 `Agent` 工具派出子 agent | `.codex/agents/` 里的 Codex 自定义 agent；派不出来时，Codex 自己扮演该角色 |
| 每个技能单独指定 `model:` | agent 按档位固定模型；light 技能交给专门的 agent 执行；heavy 技能提醒你切换模型 |
| 没有升级机制 | `BLOCKED:` → astra high → astra xhigh → 问你 |
| 默认 collaborative 模式 | 默认 guided 模式，创作类决定始终由你来定 |
| 4 个技能只能手动调用 | 所有技能都能自动触发（可以配置） |
| 子目录里的 `CLAUDE.md` 自动加载 | 列在 `AGENTS.md` 的路径规则表里，Codex 修改这些目录下的文件前会先去读 |
| 状态栏、桌面通知、agent 团队 | Codex 里没有对应功能 |
