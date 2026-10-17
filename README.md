# Codex Game Studios

**English** · [简体中文](README.zh-CN.md)

Run a whole indie game studio inside [OpenAI Codex](https://github.com/openai/codex): 49 specialist agents, 74 workflow skills, safety hooks and a structured pipeline from first idea to release.

This is a Codex port of [Claude Code Game Studios](https://github.com/Donchitos/Claude-Code-Game-Studios) by Donchitos (MIT). The original studio was built for Claude Code. This port adds a Codex layer on top of it so the same agents, skills and rules work natively in Codex. It leaves the original files unchanged, so a project made from this template also still works in Claude Code.

> Not affiliated with OpenAI, Anthropic or the original author.

## What you get

| | |
|---|---|
| **49 agents** | Creative, technical and production directors, department leads, and specialists for Godot, Unity and Unreal. Each one is a Codex custom agent with its own role, rules and model. |
| **74 skills** | Concept and brainstorming, engine setup, game design documents, architecture, sprints, stories, code review, QA, playtests, localization and release. Codex picks the skill that matches what you ask for, or you call it by name (`$brainstorm`). |
| **Collaborative by default** | Every task follows question → options → decision → draft → approval. Codex asks before writing new files and never commits on its own. |
| **Safety hooks and rules** | Commit checks, asset validation and session checkpoints run as Codex hooks. Destructive commands such as `rm -rf`, `git push --force` and `git reset --hard` are blocked. |

## What this port adds

- **Native Codex layout.** `AGENTS.md`, skills in `.agents/skills/`, custom agents in `.codex/agents/`, hooks in `.codex/hooks.json` and command rules in `.codex/rules/`.
- **Models by task difficulty.** Directors, architecture work and phase-gate reviews run on the strongest model, everyday agents on a workhorse model, and status checks on a fast model. You can change the mapping in one file.
- **Automatic escalation.** An agent that gets stuck reports `BLOCKED:` instead of guessing. Codex then retries the step on a stronger model, then on the strongest model at maximum reasoning, and asks you only if that also fails.
- **Creative decisions stay yours.** The template runs in *guided* mode, so Codex handles small decisions on its own. Decisions about art, story, player-facing text and music always come back to you.
- **Safe install scripts.** One script creates a new game. Another adds the studio to an existing game without overwriting any of its files.
- **One rules file for both tools.** Your project's own rules live in `PROJECT-NOTES.md`. Codex gets a copy in `AGENTS.md`, and Claude Code imports it from `CLAUDE.md`, so both follow the same rules.
- **Regenerator.** `codex-port/convert_to_codex.py` rebuilds the Codex layer after you change a setting or update from upstream.

## Requirements

- [Codex CLI](https://github.com/openai/codex). Tested with 0.162.1. Hooks and multi-agent support must be enabled; both are on by default.
- `git` and `bash`. On Windows, install [Git for Windows](https://git-scm.com/download/win), which provides both.
- Python 3.11 or newer. You only need it to regenerate the Codex layer.

## Quick start

```bash
git clone https://github.com/venus2099/codex-game-studios.git ~/code/codex-game-studios
```

This folder is the **template**. Don't build games inside it.

### Start a new game

```bash
bash ~/code/codex-game-studios/codex-port/new-game.sh ~/code/my-game
cd ~/code/my-game && codex
```

In Codex:
1. Trust the project when Codex asks.
2. Type `/hooks` and trust the project hooks.
3. Describe the game you want to make, or type `$start`.

### Add the studio to an existing game

```bash
bash ~/code/codex-game-studios/codex-port/add-to-project.sh ~/code/existing-game
```

The script never overwrites a file. If a file already exists with different content, it leaves yours alone and writes the template's version next to it as `<file>.ccgs-new`.

If your project already had an `AGENTS.md`, merge it before you start: move your own rules into `PROJECT-NOTES.md`, then replace `AGENTS.md` with `AGENTS.md.ccgs-new` and regenerate (`python -I codex-port/convert_to_codex.py . .`). Until you do, the studio rules are inactive. If it already had a `CLAUDE.md`, add the line `@PROJECT-NOTES.md` to it so Claude Code follows the same rules.

Then start Codex in the project, trust it and its hooks, and type `$adopt` to get a migration plan.

You can also ask Codex to run either script for you.

## Documentation

- **[Usage guide](guide/GUIDE.md)**: installation, daily workflow, models and escalation, configuration, updating, troubleshooting.
- [Original Claude Code Game Studios README](upstream/README.md): the full description of the studio's agents, skills and philosophy.

## Status and limitations

- The Codex layer was checked with Codex's own tools: `codex debug prompt-input` confirms that `AGENTS.md` and all skills load, `codex execpolicy check` covers the command rules, and every hook was run against simulated Codex events. Long real-world sessions have had little testing so far, so please report anything that behaves oddly.
- Codex skills can't switch models. Skills therefore run on your session's model; only the agents they spawn use their tier's model. See [Models](guide/GUIDE.md#6-models-and-escalation).
- Desktop notifications and the status line from the original have no Codex equivalent and are not ported.

## License

MIT. The original studio is © 2026 Donchitos, and the Codex port additions are © 2026 their author. See [LICENSE](LICENSE).
