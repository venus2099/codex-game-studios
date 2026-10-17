# Codex Game Studios: Usage Guide

**English** · [简体中文](GUIDE.zh-CN.md) · [Back to README](../README.md)

1. [How it fits together](#1-how-it-fits-together)
2. [Install](#2-install)
3. [Start a new game](#3-start-a-new-game)
4. [Add the studio to an existing game](#4-add-the-studio-to-an-existing-game)
5. [Daily use](#5-daily-use)
6. [Models and escalation](#6-models-and-escalation)
7. [Automation mode and creative decisions](#7-automation-mode-and-creative-decisions)
8. [Configuration reference](#8-configuration-reference)
9. [Regenerating the Codex layer](#9-regenerating-the-codex-layer)
10. [Hooks and safety rules](#10-hooks-and-safety-rules)
11. [Updating from upstream (maintainers)](#11-updating-from-upstream-maintainers)
12. [Troubleshooting](#12-troubleshooting)
13. [Differences from the original](#13-differences-from-the-original)

---

## 1. How it fits together

**The template and your games are separate folders.** You clone this repository once; that clone is the template. For each game, a script copies the template into a new folder or into an existing project. You work on the game in that folder and leave the template untouched.

What a game project contains:

| Path | What it is |
|---|---|
| `AGENTS.md` | Codex's standing instructions for the project, read at the start of every session. Generated; don't edit it. |
| `PROJECT-NOTES.md` | **Your own rules for the project**, shared by both tools: Codex gets a copy inside `AGENTS.md`, and Claude Code imports it from `CLAUDE.md`. |
| `CLAUDE.md`, `.claude/` | The original studio: agent roles, skills, rules, docs, hooks. This is the single source of truth, and the Codex layer points into it. |
| `.agents/skills/` | One small Codex entry point per skill, pointing at `.claude/skills/<name>/SKILL.md`. |
| `.codex/agents/` | The 49 agents as Codex custom agents, plus the runner and escalation agents added by the port. |
| `.codex/hooks.json`, `.codex/hooks/` | The original hooks wired into Codex through an adapter. |
| `.codex/rules/ccgs.rules` | Blocked shell commands. |
| `project.yaml` | Project settings: engine, automation mode, review intensity and so on. |
| `codex-port/` | The converter and its settings (`model_tiers.toml`, `skills.toml`, `preset/`). |
| `design/`, `docs/`, `production/`, `src/`, `tests/` | Your game: design documents, architecture, sprints and stories, code, tests. |

## 2. Install

Prerequisites:

- **Codex CLI.** Tested with 0.162.1. Run `codex features list` and check that `hooks` and `multi_agent` are `true`; they are by default.
- **git and bash.** On Windows, [Git for Windows](https://git-scm.com/download/win) provides both. The hooks run with `bash`, so it must be on `PATH`.
- **Python 3.11+.** You only need it to regenerate the Codex layer (section 9).

Clone the template:

```bash
git clone https://github.com/venus2099/codex-game-studios.git ~/code/codex-game-studios
```

On Windows, also run this once. The studio has deeply nested paths that otherwise make git fail with "Filename too long":

```bash
git config --global core.longpaths true
```

## 3. Start a new game

```bash
bash ~/code/codex-game-studios/codex-port/new-game.sh ~/code/my-game
```

The target folder must be new or empty. The script:
- runs `git init` with long paths enabled;
- copies the template's `.gitignore` and `.gitattributes`;
- installs the studio files.

It commits nothing.

Then:

```bash
cd ~/code/my-game
codex
```

1. Trust the project when Codex asks. Codex only applies a project's own configuration (agents, hooks, rules) when you trust the project.
2. Type `/hooks` and trust the project's hooks. Codex asks for this once per project.
3. Describe what you want to make, or type `$start` for the guided onboarding.

You can also ask Codex to run the script for you from any folder:

> Run `bash ~/code/codex-game-studios/codex-port/new-game.sh ~/code/my-game` and tell me the next steps it prints. Don't commit anything.

Codex only loads `AGENTS.md`, skills, agents and hooks when a session starts. After the script finishes, quit Codex and start it again inside the new folder.

## 4. Add the studio to an existing game

1. Commit your current work. This is optional, but it makes the script's additions easy to review.
2. Run:

   ```bash
   bash ~/code/codex-game-studios/codex-port/add-to-project.sh ~/code/existing-game
   ```

   The script is safe to run more than once:
   - **Never overwrites.** A file the project doesn't have is copied in. A file that exists with different content is left alone, and the template's version is written next to it as `<file>.ccgs-new`.
   - **Appends only studio entries to `.gitignore`.** Those cover local settings and session logs. The original's engine and build rules are not merged, because they could hide files your project tracks on purpose (for example `*.csproj`).
   - **Commits nothing.**
3. **Merge `AGENTS.md` if your project already had one.** Until you do, Codex keeps reading your old file and the studio rules are inactive (the skills still work). The easiest way is to ask Codex:

   > Move the rules from my AGENTS.md into PROJECT-NOTES.md, replace AGENTS.md with AGENTS.md.ccgs-new, run `python -I codex-port/convert_to_codex.py . .`, and delete the .ccgs-new file.

   If the project already had a `CLAUDE.md`, also add the line `@PROJECT-NOTES.md` to it, so Claude Code follows the same rules.

   Handle any other `.ccgs-new` files the same way.
4. Start Codex in the project, trust it, and trust the hooks with `/hooks`.
5. Say "analyze this existing project", or type `$adopt`. It checks your existing code and documents against the studio's pipeline and writes a migration plan to `docs/adoption-plan-<date>.md`.

   These skills are useful next:
   - `$setup-engine` records the engine and version you use.
   - `$reverse-document` writes design documents from existing code.
   - `$project-stage-detect` tells you which phase the project is in.

The studio expects Godot code in `src/`, Unity code in `Assets/` and Unreal code in `Source/`. If your code lives elsewhere, the adoption plan will say so; then you decide whether to move it or point the configuration at it.

## 5. Daily use

**Talk normally.** Codex sees every skill's description and starts the matching one on its own: "give me some game ideas" starts `brainstorm`, "what should I do next?" starts `help`. To force a specific skill, name it ("use brainstorm") or type `$name`. `/skills` lists them all. All 74 skills can start automatically; see `skills.toml` in section 8 to change that.

**Questions come as numbered options.** The original studio used Claude's question cards. In Codex you get a short question, numbered options and a recommendation. Reply with a number or in your own words. Codex waits for your answer; a turn that ends without one is not an answer.

**Typical path through a project:**

| Phase | Typical skills |
|---|---|
| Concept | `$start`, `$brainstorm`, `$setup-engine`, `$prototype` |
| Systems design | `$art-bible`, `$map-systems`, `$design-system`, `$design-review`, `$review-all-gdds` |
| Technical setup | `$create-architecture`, `$architecture-decision`, `$create-control-manifest`, `$test-setup` |
| Pre-production | `$create-epics`, `$create-stories`, `$ux-design`, `$vertical-slice` |
| Production | `$sprint-plan`, `$story-readiness`, `$dev-story`, `$code-review`, `$story-done`, `$sprint-status` |
| Polish and QA | `$qa-plan`, `$smoke-check`, `$playtest-report`, `$perf-profile`, `$team-polish` |
| Release | `$release-checklist`, `$launch-checklist`, `$patch-notes`, `$changelog` |
| Any time | `$help`, `$gate-check`, `$scope-check`, `$estimate`, `$bug-report`, `$settings` |

`$gate-check` decides whether the project is ready to move to the next phase. `team-*` skills (`$team-combat`, `$team-narrative`, `$team-ui` and others) run a whole department on one feature.

**Sessions and memory.** The studio keeps its checkpoint in `production/session-state/active.md`, and the session-start hook loads it automatically. After `/new` or a crash, just continue. Ask "where were we?" if you want a summary.

## 6. Models and escalation

Every skill and agent in the original studio is rated by difficulty. The port maps those ratings to Codex models in `codex-port/model_tiers.toml`:

| Tier | Original | Default model (reasoning) | Used by |
|---|---|---|---|
| top | set in `[overrides]` | `gpt-6-astra` (xhigh) | `technical-director` (in Claude Code, `PROJECT-NOTES.md` pins it to Fable) |
| heavy | opus, plus architecture skills via `[overrides]` | `gpt-6-astra` (high) | `creative-director`, `producer`; skills `$gate-check`, `$architecture-review`, `$review-all-gdds`, `$create-architecture`, `$architecture-decision`, `$map-systems` |
| standard | sonnet, plus agents that followed the session model | `gpt-6.1-sol` (high) | the other 46 agents |
| light | haiku | `gpt-6-luna` (high) | `$help`, `$onboard`, `$project-stage-detect`, `$scope-check`, `$sprint-status` |

A Codex skill cannot switch the model, so the port handles each tier differently:

- **Agents** are pinned to their tier's model.
- **Light skills** are handed to `ccgs-light-runner`, an agent on the fast model. It returns the result; if it needs a decision, the question comes back to you.
- **Heavy skills** check the session model. If you aren't on the heavy model, Codex mentions once that you can switch with `/model`, then continues.
- **All other skills** run in your session, on your session's model.

**Architecture work.** System architecture, technical decisions and system decomposition shape every later system and are costly to undo, so they count as heavy. `PROJECT-NOTES.md` also asks both tools to remind you once to switch to the strongest model (Fable in Claude Code, `gpt-6-astra` in Codex) before that kind of work and before phase-gate reviews.

**Cost tip.** Most of the work happens in the main session, so your default model drives most of the cost. To spend less, run day to day on `gpt-6.1-sol` and switch to `gpt-6-astra` with `/model` when a heavy skill asks.

**Escalation.** An agent that can't finish, or isn't confident in its result, returns a report starting with `BLOCKED:` instead of something that only looks finished. Codex then works up the ladder and tells you each time it escalates:

1. `ccgs-escalation` (`gpt-6-astra`, high)
2. `ccgs-escalation-max` (`gpt-6-astra`, xhigh)
3. Codex stops and asks you, explaining what each level tried.

Codex also escalates when a result is clearly unusable: tests still fail, it fails its acceptance criteria, or it contradicts the design. A level that is not stronger than the agent's own model is skipped: heavy agents (astra at high) go straight to level 2, and `technical-director` (astra at xhigh) goes straight to you. Each step is escalated at most once per level. Questions for you and creative decisions are never escalated; they go straight to you.

**Two attempts, then ask.** Escalation never retries a fix that has already failed twice. Any single problem gets at most two attempts in total; after that the agent returns `BLOCKED: two attempts failed` and Codex asks you. This rule lives in `PROJECT-NOTES.md` (section 7), together with two others: name the deliverable in one sentence before starting a fix, and stop to check with you after a long stretch of implementation work with no edits.

To change any of this, edit `model_tiers.toml`, then regenerate (section 9):
- **Change a tier's model or reasoning:** edit `[tiers.*]`.
- **Change the escalation order:** edit `[escalation] ladder`.
- **Move a single agent or skill to another tier:** add it to `[overrides]`, for example `"game-designer" = "heavy"`.

Model names must be ones your Codex account offers; `/model` lists them.

## 7. Automation mode and creative decisions

`modes.automation` in `project.yaml` controls how often Codex stops to ask:

| Mode | Behaviour |
|---|---|
| `collaborative` | Every decision is yours, and every file write is approved first. |
| `guided` (template default) | Codex asks about major decisions (engine, core mechanics, scope, anything costly to undo). It decides minor ones itself and tells you what it chose. It asks before creating new files and updates existing ones after a short summary. |
| `autonomous` | Codex decides everything except the categories in `modes.automation_always_ask`, and logs every decision to `production/session-logs/decision-log.md`. |

Change the mode by saying "set automation to collaborative" (Codex uses `$settings`), or edit `project.yaml`. `$start` asks for a mode during onboarding, so pick `guided` again there if that's what you want.

**Director reviews run at phase gates only.** The template sets `modes.review_mode: lean`: the creative director, producer and technical director review at `$gate-check` phase gates, and per-step director reviews are skipped. Because the value is set in `project.yaml`, the rigor answer in `$start` no longer changes it; use `$settings modes.review_mode=full` (every step) or `solo` (no director reviews) to change it.

The template also sets `modes.workflow: full`: every design document needs all eight sections, every architecture decision gets an ADR, and the phase-gate panel has all four directors (creative, technical, producer, art). With `minimal` the panel is the producer alone; with `standard` it is the technical director and producer. Documentation depth (`docs.density`) and QA level (`qa.level`) are separate settings and stay at their defaults.

**Creative decisions are always yours.** The template adds four categories to `modes.automation_always_ask`:
- `art_and_visuals`
- `story_and_narrative`
- `player_facing_text`
- `music_and_audio`

The original only checks that list in autonomous mode, so `PROJECT-NOTES.md` makes these four ask in every mode. They cover:
- **Art and visuals:** art style, how characters and places look, palette, UI look, effects.
- **Story and narrative:** plot, characters, world and lore, quests, endings, tone.
- **Player-facing text:** dialogue, item and skill text, UI copy, tutorials, store page.
- **Music and audio:** music direction, sound palette, voice.

Technical work on approved content follows the normal rules. That includes file formats, import settings, and wiring an approved line or sound into the game.

Subagents can't talk to you. When they hit one of these decisions, they return it as a question.

## 8. Configuration reference

| File | Controls |
|---|---|
| `codex-port/model_tiers.toml` | Tier → model and reasoning; escalation ladder; per-agent and per-skill overrides |
| `codex-port/skills.toml` | `implicit_invocation = "all"` lets Codex start every skill automatically. `"upstream"` restores the original, where `$dev-story`, `$story-done`, `$hotfix` and `$day-one-patch` only run when you type them. |
| `codex-port/preset/project-notes.md` | Starting content for `PROJECT-NOTES.md` in a freshly built template (the creative-decisions and retry rules) |
| `codex-port/preset/project-modes.yaml` | Default `modes:` block for a freshly built template's `project.yaml` |
| `project.yaml` | Engine, automation mode, always-ask categories, review intensity and other studio settings. Change it with `$settings`, or edit it directly. |
| `project.local.yaml` | Your personal overrides of `project.yaml`. Git ignores it. |
| `PROJECT-NOTES.md` | Your own standing rules for this project, followed by both Codex and Claude Code. |

**Where to put your own rules:**

| Kind of rule | Put it in |
|---|---|
| Personal habits for every project ("reply in Chinese") | `~/.codex/AGENTS.md` |
| Short rules for this project | `PROJECT-NOTES.md` |
| Long or detailed rules | A separate file, plus one line in `PROJECT-NOTES.md` saying when to read it |
| Rules for certain files only | A file in `.claude/rules/` with a `paths:` header |
| Project settings | `project.yaml`, or `$settings` |
| Things that must never happen | `.codex/rules/` or a hook. `AGENTS.md` is guidance; rules and hooks are enforced. |

Codex reads at most 32 KiB of `AGENTS.md` by default. The generated file is about 24 KiB including your notes, so keep `PROJECT-NOTES.md` short. The notes sit near the top of `AGENTS.md`, so they survive even if it grows past the limit.

**After you edit `PROJECT-NOTES.md`:** Claude Code picks the change up in its next session. Codex reads a copy, so regenerate (section 9). Until you do, a session-start hook notices the change and tells Codex to read `PROJECT-NOTES.md` directly.

## 9. Regenerating the Codex layer

After you edit `model_tiers.toml`, `skills.toml` or anything in `.claude/`, run this from the project root:

```bash
python -I codex-port/convert_to_codex.py . .
```

It rewrites only generated files:
- `AGENTS.md` (its Project notes block is copied from `PROJECT-NOTES.md`, which is never overwritten)
- `.agents/skills/`
- `.codex/agents/`
- `.codex/hooks.json`
- `.codex/hooks/codex-hook.sh`
- `.codex/rules/ccgs.rules`
- `README-CODEX.md`

Your code, design documents, `production/` and `project.yaml` are not touched. If you point the converter at an existing, non-empty folder other than the source, it refuses to run.

Change settings in the template to affect future games. Change them in a game project to affect only that game.

## 10. Hooks and safety rules

| Event | What runs |
|---|---|
| Session start | Loads the session checkpoint and recent commits, and detects gaps in the project |
| Before a shell command | Checks `git commit` and `git push` (for example, blocks a commit that includes a broken JSON data file) |
| After a file edit | Validates assets (for example JSON syntax) and flags edited skills |
| Compaction, stop, subagent start/stop | Saves session state and logs agent activity |

Codex edits files with `apply_patch`, while the original hooks expect Claude's `file_path` input. `.codex/hooks/codex-hook.sh` translates between the two, so the original hook scripts run unchanged.

`.codex/rules/ccgs.rules` forbids these commands:
- `rm -rf` (in every flag spelling)
- `git push --force`
- `git reset --hard`
- `git clean -f`
- `sudo`
- `chmod 777`

To check a command against the rules:

```bash
codex execpolicy check --rules .codex/rules/ccgs.rules git reset --hard
```

If your Codex build doesn't load project rules, copy the file to `~/.codex/rules/`.

## 11. Updating from upstream (maintainers)

1. Download the new version of Claude Code Game Studios.
2. Build a fresh template from it. This also applies the presets, drops upstream's `.github/`, and moves upstream's README, CHANGELOG and similar files into `upstream/`:

   ```bash
   python -I codex-port/convert_to_codex.py <upstream-folder> <new-folder>
   ```

3. Copy `README.md`, `README.zh-CN.md`, `guide/` and `LICENSE` from this repository into the new folder.
4. Compare the two folders, then commit the new one.

Existing game projects can follow upstream's `UPGRADING.md` (in `upstream/`) to update `.claude/`, then regenerate in place.

## 12. Troubleshooting

| Symptom | Fix |
|---|---|
| `Filename too long` from git on Windows | `git config --global core.longpaths true` (the scripts set it per project) |
| Hooks never run | Type `/hooks` and trust them. Make sure `bash` is on `PATH`, and start Codex from the project root. |
| Codex ignores the studio rules | Start Codex in the project root. If `AGENTS.md.ccgs-new` exists, merge it (section 4). |
| A skill doesn't start automatically | Name it ("use sprint-plan") or type `$sprint-plan`. Check `skills.toml`. |
| An agent can't be spawned | Check that `multi_agent` is `true` in `codex features list`. Otherwise Codex plays the role itself by reading `.claude/agents/<name>.md`. |
| A model name is rejected | Your account may not offer it. Change `model_tiers.toml` and regenerate. |
| The converter says Python is too old | It needs Python 3.11+ for `tomllib`. |

## 13. Differences from the original

| Original (Claude Code) | This port (Codex) |
|---|---|
| `/skill-name` | `$skill-name`, or ask in plain language |
| Question cards (`AskUserQuestion`) | Numbered options in chat; Codex waits for your reply |
| Subagents via the `Agent` tool | Codex custom agents in `.codex/agents/`. If that fails, Codex plays the role itself. |
| Per-skill `model:` | Agents pinned per tier, light skills delegated, heavy skills recommend `/model` |
| No escalation | `BLOCKED:` → astra high → astra xhigh → ask the user |
| Collaborative mode by default | Guided mode, with creative decisions always yours |
| Four skills manual-only | All skills can start automatically (configurable) |
| Folder `CLAUDE.md` files load automatically | Listed in `AGENTS.md`'s path-scoped rules table; Codex reads them before editing those folders |
| Status line, desktop notifications, agent teams | Not available in Codex |
| Project rules in `CLAUDE.md` | Shared `PROJECT-NOTES.md`: Codex copies it into `AGENTS.md`, Claude Code imports it |
