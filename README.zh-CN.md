# Codex Game Studios

[English](README.md) · **简体中文**

在 [OpenAI Codex](https://github.com/openai/codex) 里运行一整个独立游戏工作室：49 个专职 agent、74 个工作流技能、安全钩子，以及一条从最初的点子到正式发布的完整流程。

本项目是 [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios)（作者 Donchitos，MIT 协议）的 Codex 移植版。原版是为 Claude Code 设计的，这个移植版在原版之上加了一层 Codex 配置，让同一套 agent、技能和规则可以直接在 Codex 里运行。原版文件一个都没改，所以用这个模板创建的项目在 Claude Code 里也照样能用。

> 本项目与 OpenAI、Anthropic 以及原版作者均无隶属关系。

## 包含什么

| | |
|---|---|
| **49 个 agent** | 创意、技术、制作三位总监，各部门负责人，以及 Godot、Unity、Unreal 的引擎专家。每个都是一个 Codex 自定义 agent，有自己的职责、规则和模型。 |
| **74 个技能** | 构思与头脑风暴、引擎配置、游戏设计文档、技术架构、冲刺计划、任务卡、代码评审、测试、试玩报告、本地化、发布。你描述想做的事，Codex 会自动挑合适的技能；也可以直接用名字调用，比如 `$brainstorm`。 |
| **默认协作模式** | 每项任务都按「提问 → 给选项 → 你决定 → 出草稿 → 你确认」进行。新建文件前会先问你，也不会自己提交代码。 |
| **安全钩子和规则** | 提交检查、资源校验、会话存档以 Codex 钩子的形式运行。`rm -rf`、`git push --force`、`git reset --hard` 等危险命令会被直接拦截。 |

## 移植版新增的功能

- **原生 Codex 结构**：`AGENTS.md`、`.agents/skills/` 下的技能、`.codex/agents/` 下的自定义 agent、`.codex/hooks.json` 钩子、`.codex/rules/` 命令规则，都是 Codex 原生的格式。
- **按任务难度分配模型**：总监和阶段评审用最强的模型，日常 agent 用主力模型，状态查询这类轻活用快速模型。对应关系在一个配置文件里，可以随时改。
- **卡住时自动升级**：agent 解决不了问题时会报告 `BLOCKED:`，不会瞎猜。Codex 会先换更强的模型重做这一步，还不行就用最强模型加最高推理强度，最后才来问你。
- **创作决定始终归你**：模板默认使用 guided 模式，小事 Codex 自己处理，但美术、故事、玩家可见的文本、音乐这四类决定，一律交给你拍板。
- **安全的安装脚本**：一个脚本用来新建游戏，另一个用来把工作室装进已有的游戏项目，不会覆盖项目里的任何文件。
- **重新生成工具**：改了设置或者原版更新之后，用 `codex-port/convert_to_codex.py` 重新生成 Codex 配置层。

## 环境要求

- [Codex CLI](https://github.com/openai/codex)，已在 0.162.1 版本上测试。需要开启钩子和多 agent 功能，两者默认都是开启的。
- `git` 和 `bash`。Windows 上安装 [Git for Windows](https://git-scm.com/download/win) 即可，两个都带。
- Python 3.11 或以上，只在重新生成 Codex 配置层时需要。

## 快速开始

```bash
git clone https://github.com/venus2099/codex-game-studios.git ~/code/codex-game-studios
```

这个文件夹是**模板**，不要直接在里面做游戏。

### 新建一个游戏

```bash
bash ~/code/codex-game-studios/codex-port/new-game.sh ~/code/my-game
cd ~/code/my-game && codex
```

在 Codex 里：
1. Codex 问是否信任这个项目时，选信任。
2. 输入 `/hooks`，信任项目自带的钩子。
3. 描述你想做的游戏，或者输入 `$start` 开始引导。

### 用在已有的游戏项目上

```bash
bash ~/code/codex-game-studios/codex-port/add-to-project.sh ~/code/existing-game
```

这个脚本不会覆盖任何文件。如果项目里已经有同名但内容不同的文件，你的文件保持原样，模板的版本会另存为旁边的 `文件名.ccgs-new`。

如果项目原本就有 `AGENTS.md`，开始之前一定要先合并：把你自己的规则移到 `AGENTS.md.ccgs-new` 的「Project notes」区块里，再用它替换 `AGENTS.md`。不合并的话，工作室规则不会生效。

合并好之后，在项目里启动 Codex，信任项目和钩子，然后输入 `$adopt` 生成迁移计划。

上面两个脚本也可以直接让 Codex 替你运行。

## 文档

- **[使用指南](guide/GUIDE.zh-CN.md)**：安装、日常使用流程、模型与升级机制、配置、更新、常见问题。
- [原版 Claude Code Game Studios 的 README](upstream/README.md)（英文）：完整介绍工作室的 agent、技能和设计理念。

## 现状与限制

- Codex 配置层用 Codex 自带的工具检查过：
  - `codex debug prompt-input` 确认 `AGENTS.md` 和所有技能都能正常加载；
  - `codex execpolicy check` 验证了命令规则；
  - 所有钩子都用模拟的 Codex 事件跑过。

  长时间的真实使用测试还不多，遇到任何异常欢迎提 issue。
- Codex 的技能没法自己切换模型，所以技能本身用的是你当前会话的模型，只有技能派出的 agent 才会按档位使用对应的模型。详见[模型说明](guide/GUIDE.zh-CN.md#6-模型与升级机制)。
- 原版的桌面通知和状态栏在 Codex 里没有对应功能，没有移植。

## 许可协议

MIT 协议。原版工作室 © 2026 Donchitos，Codex 移植部分 © 2026 移植作者，详见 [LICENSE](LICENSE)。
