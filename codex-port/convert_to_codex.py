"""Build a Codex version of Claude Code Game Studios.

    python -I convert_to_codex.py <upstream-checkout> <new-folder>   # fresh copy
    python -I codex-port/convert_to_codex.py . .                     # regenerate in place

The output is a full copy of the upstream repository plus a Codex layer:

    AGENTS.md                      CLAUDE.md for Codex, imports inlined, plus a
                                   Claude-to-Codex vocabulary table
    .agents/skills/<name>/         one thin wrapper skill per upstream skill; it
                                   points at .claude/skills/<name>/SKILL.md, which
                                   stays the single source of truth
    .codex/agents/<name>.toml      one Codex custom agent per upstream agent, on the
                                   model its difficulty tier maps to (model_tiers.toml)
    .codex/hooks.json              the upstream hooks, run through an adapter
    .codex/hooks/codex-hook.sh     that adapter (from overlay/)
    .codex/rules/ccgs.rules        the upstream deny list as Codex rules (overlay/)
    README-CODEX.md                usage notes (overlay/)

Upstream files are copied, never modified, so the result still works in Claude
Code too. An existing, non-empty output folder is never deleted or overwritten;
regenerating in place rewrites only the files listed above (AGENTS.md keeps its
"Project notes" block).
"""

import json
import re
import shutil
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
OVERLAY = HERE / "overlay"


# --- frontmatter --------------------------------------------------------------

def split_frontmatter(text):
    """Return (dict of top-level single-line keys, body) for a --- block."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    block = text[3:end].strip("\n")
    body = text[end + 4:].lstrip("\n")
    meta = {}
    key = None
    for line in block.splitlines():
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key = m.group(1)
            meta[key] = m.group(2).strip()
        elif key and line.startswith((" ", "\t")):
            meta[key] = (meta[key] + "\n" + line).strip()
    return meta, body


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        inner = value[1:-1]
        if value[0] == '"':
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return inner.replace('\\"', '"')
        return inner.replace("''", "'")
    return value


def parse_list(value):
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    return [unquote(v) for v in value.split(",") if v.strip()]


def yaml_str(s):
    return json.dumps(s, ensure_ascii=False)


def toml_multiline(s):
    if "'''" not in s:
        return "'''\n" + s + "'''"
    esc = s.replace("\\", "\\\\").replace('"""', '\\"\\"\\"')
    return '"""\n' + esc + '"""'


# --- text helpers ---------------------------------------------------------------

def slash_to_dollar(text, skill_names):
    """`/dev-story` -> `$dev-story` for upstream skill names, outside paths/URLs."""
    alt = "|".join(sorted((re.escape(n) for n in skill_names), key=len, reverse=True))
    pattern = re.compile(r"(?<![\w./:$-])/(" + alt + r")(?![\w/.-]*\w)(?![\w-])")
    return pattern.sub(r"$\1", text)


def demote_headings(md, levels=1):
    out, fence = [], False
    for line in md.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
        if not fence and re.match(r"^#{1,5} ", line):
            line = "#" * levels + line
        out.append(line)
    return "\n".join(out)


# --- model tiers ----------------------------------------------------------------

class Tiers:
    """Maps an upstream Claude tier (opus/sonnet/haiku/inherit) to a Codex model."""

    def __init__(self, path):
        cfg = tomllib.loads(path.read_text(encoding="utf-8"))
        self.tiers = cfg["tiers"]
        self.mapping = cfg.get("mapping", {})
        self.overrides = cfg.get("overrides", {})
        self.ladder = cfg.get("escalation", {}).get("ladder", [])
        for name, tier in list(self.mapping.items()) + list(self.overrides.items()):
            if tier != "session" and tier not in self.tiers:
                sys.exit(f"model_tiers.toml: '{name}' maps to unknown tier '{tier}'")
        for tier in self.ladder:
            if tier not in self.tiers:
                sys.exit(f"model_tiers.toml: escalation ladder names unknown tier '{tier}'")

    def escalation_for(self, tier):
        """Escalation agents to try, in order, after an agent on `tier` is BLOCKED."""
        current = self.tiers.get(tier) if tier else None
        return [f"ccgs-{t}" for t in self.ladder if self.tiers[t] != current]

    def tier_for(self, name, upstream_model):
        """Tier name, or None when the item should run on the session model."""
        tier = self.overrides.get(name) or self.mapping.get(upstream_model or "inherit", "session")
        return None if tier == "session" else tier

    def toml_lines(self, tier):
        if tier is None:
            return ""
        t = self.tiers[tier]
        return (
            f"model = {json.dumps(t['model'])}\n"
            f"model_reasoning_effort = {json.dumps(t['reasoning_effort'])}\n"
        )


# --- skills ---------------------------------------------------------------------

LIGHT_RUNNER = "ccgs-light-runner"

SKILL_WRAPPER = """---
name: {name}
description: {description}
---

<!-- Generated by codex-port/convert_to_codex.py; edits here are overwritten. -->

# {name}

{args_line}This is the Codex entry point for the upstream skill
`.claude/skills/{name}/SKILL.md`, which stays the single source of truth.
{tier_note}
1. Read `.claude/skills/{name}/SKILL.md` in full before doing anything else.
2. If it has lines starting with `` !` ``, they are startup commands. Run each
   one from the repository root with `${{CLAUDE_SKILL_DIR}}` = `.claude/skills/{name}`
   and treat the output as the config block the skill says is "resolved above".
{bootstrap}3. Follow the skill exactly, translating Claude Code vocabulary with the
   "Codex compatibility" table in `AGENTS.md`. In particular, every
   `AskUserQuestion` means: ask in chat with numbered options, then stop and
   wait for the user's reply.
"""


def skill_tier_note(name, tier, tiers):
    if tier == "light":
        return f"""
**Model tier: light** ({tiers.tiers['light']['model']}). Unless you are
`{LIGHT_RUNNER}` yourself, or the user asked you to run it directly, delegate:
spawn the custom agent `{LIGHT_RUNNER}` with the skill name `{name}`, the user's
arguments and any approvals the user has already given, then relay its result.
If it comes back with a question for the user, ask it in chat, wait, and finish
the skill yourself with the answer. `{LIGHT_RUNNER}` skips this paragraph and
runs the steps below.
"""
    if tier == "heavy":
        # Heavy skills spawn director agents themselves, so they cannot run inside
        # a subagent (max_depth 1). Recommend the model instead of delegating.
        t = tiers.tiers[tier]
        return f"""
**Model tier: heavy** ({t['model']}, reasoning effort {t['reasoning_effort']}).
If this session runs a different model, tell the user once, before step 1,
that this skill is rated heavy and that `/model` can switch to {t['model']};
then continue on the current model unless they choose to switch.
"""
    # standard / session: run on the session model.
    return ""


POLICY_MARKER = "# Upstream sets disable-model-invocation:"


def convert_skills(src, out, skill_names, tiers, implicit):
    """implicit: "upstream" keeps upstream's $-only skills, "all" lets Codex start any skill."""
    dst_root = out / ".agents" / "skills"
    by_tier = {}
    for skill_md in sorted((src / ".claude" / "skills").glob("*/SKILL.md")):
        name = skill_md.parent.name
        meta, body = split_frontmatter(skill_md.read_text(encoding="utf-8"))
        description = unquote(meta.get("description", f"Upstream skill {name}."))
        description = slash_to_dollar(description, skill_names)
        hint = unquote(meta.get("argument-hint", ""))
        args_line = f"Arguments: `{hint}` (take them from the user's message).\n\n" if hint else ""

        cmds = [m.group(1) for m in re.finditer(r"^!`(.+)`\s*$", body, re.M)]
        bootstrap = ""
        if cmds:
            resolved = [
                c.replace("${CLAUDE_SKILL_DIR}/../../..", ".")
                 .replace("${CLAUDE_SKILL_DIR}/../../", ".claude/")
                 .replace("${CLAUDE_SKILL_DIR}", f".claude/skills/{name}")
                for c in cmds
            ]
            bootstrap = "   At the time of porting these were:\n\n" + "".join(
                f"   ```bash\n   {c}\n   ```\n\n" for c in resolved
            )

        tier = tiers.tier_for(name, unquote(meta.get("model", "")))
        by_tier.setdefault(tier or "session", []).append(name)

        d = dst_root / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "SKILL.md").write_text(
            SKILL_WRAPPER.format(
                name=name,
                description=yaml_str(description),
                args_line=args_line,
                tier_note=skill_tier_note(name, tier, tiers),
                bootstrap=bootstrap,
            ),
            encoding="utf-8",
            newline="\n",
        )
        policy = d / "agents" / "openai.yaml"
        explicit_only = unquote(meta.get("disable-model-invocation", "false")).lower() == "true"
        if explicit_only and implicit != "all":
            policy.parent.mkdir(exist_ok=True)
            policy.write_text(
                POLICY_MARKER + " run it only via $" + name + ".\n"
                "policy:\n  allow_implicit_invocation: false\n",
                encoding="utf-8",
                newline="\n",
            )
        elif policy.exists() and policy.read_text(encoding="utf-8").startswith(POLICY_MARKER):
            policy.unlink()  # ours, from an earlier run with implicit_invocation = "upstream"
            if not any(policy.parent.iterdir()):
                policy.parent.rmdir()
    return by_tier


# --- agents ---------------------------------------------------------------------

AGENT_FOOTER = """

---
## Running under Codex

You are a Codex subagent of Codex Game Studios, a port of Claude Code Game
Studios. Translate Claude Code vocabulary with the "Codex compatibility" table
in `AGENTS.md`. You cannot talk to the user directly: where these instructions
say to ask the user or call `AskUserQuestion`, return the question with
numbered options to the orchestrating session instead of guessing.
{extra}"""


LIGHT_RUNNER_INSTRUCTIONS = """You run one light-tier Codex Game Studios skill (status checks, formatting,
simple lookups) for the main session, on a fast model.

1. Read `.agents/skills/<skill>/SKILL.md` for the skill you were given and
   follow it, skipping its "Model tier: light" delegation paragraph: you are
   the runner.
2. Translate Claude Code vocabulary with the "Codex compatibility" table in
   `AGENTS.md`.
3. You cannot talk to the user. When the skill needs a user decision, or wants
   to write a file the main session has not said the user approved, stop and
   return: what you found so far, then the question with numbered options (or
   the proposed path and a summary of the content).
4. {blocked}
5. Otherwise return the skill's final output exactly as the user should see it.
"""

BLOCKED_RULE = (
    "If you cannot complete the task, or are not confident the result is correct,"
    " do not guess and do not hand back something that only looks finished."
    " Return a report that starts with `BLOCKED:` and says what blocks you, what"
    " you tried, and what you produced so far. The main session will retry the"
    " step on a stronger model. A question for the user is not BLOCKED: return"
    " it as a question."
)

ESCALATION_INSTRUCTIONS = """You take over a Codex Game Studios step that a weaker agent could not finish.
You run on a stronger model ({model}, reasoning effort {effort}).

The main session gives you: the role or skill, the original task, the
`BLOCKED:` report or what was wrong with the result, and the files involved.

1. If you were given a role, read `.claude/agents/<role>.md` and act as that
   role, with all of its rules. If you were given a skill, read
   `.agents/skills/<skill>/SKILL.md` and follow it, skipping any "Model tier"
   delegation paragraph: you are the runner.
2. Start from the failure report. Check the work already done before reusing
   it, and do not repeat an approach that already failed.
3. Translate Claude Code vocabulary with the "Codex compatibility" table in
   `AGENTS.md`, and follow its "Project notes". You cannot talk to the user:
   return any question for the user, with numbered options, instead of
   deciding it.
4. {blocked}
"""


def light_runner_toml(tiers):
    toml = (
        "# Generated by convert_to_codex.py: runs light-tier skills on a fast model.\n"
        f"name = {json.dumps(LIGHT_RUNNER)}\n"
        'description = "Runs a light-tier Codex Game Studios skill (status, help, '
        'lookups) on a fast model and returns its output."\n'
        'sandbox_mode = "workspace-write"\n'
        + tiers.toml_lines("light")
        + "developer_instructions = "
        + toml_multiline(LIGHT_RUNNER_INSTRUCTIONS.format(blocked=BLOCKED_RULE))
        + "\n"
    )
    tomllib.loads(toml)
    return toml


def escalation_toml(tiers, tier, is_last):
    t = tiers.tiers[tier]
    blocked = (
        "If you still cannot finish, return `BLOCKED:` with what you tried; this is"
        " the last automatic level, so the main session will ask the user."
        if is_last else BLOCKED_RULE
    )
    instructions = ESCALATION_INSTRUCTIONS.format(
        model=t["model"], effort=t["reasoning_effort"], blocked=blocked
    )
    toml = (
        "# Generated by convert_to_codex.py: escalation level for BLOCKED steps.\n"
        f'name = "ccgs-{tier}"\n'
        f'description = "Retries a step another agent returned as BLOCKED, on'
        f' {t["model"]} ({t["reasoning_effort"]}). Spawn only to escalate."\n'
        'sandbox_mode = "workspace-write"\n'
        + tiers.toml_lines(tier)
        + f"developer_instructions = {toml_multiline(instructions)}\n"
    )
    tomllib.loads(toml)
    return toml


def convert_agents(src, out, skill_names, tiers):
    dst = out / ".codex" / "agents"
    dst.mkdir(parents=True, exist_ok=True)
    (dst / f"{LIGHT_RUNNER}.toml").write_text(light_runner_toml(tiers), encoding="utf-8", newline="\n")
    for i, tier in enumerate(tiers.ladder):
        (dst / f"ccgs-{tier}.toml").write_text(
            escalation_toml(tiers, tier, i == len(tiers.ladder) - 1), encoding="utf-8", newline="\n"
        )
    roster = []
    for agent_md in sorted((src / ".claude" / "agents").glob("*.md")):
        meta, body = split_frontmatter(agent_md.read_text(encoding="utf-8"))
        name = unquote(meta.get("name", agent_md.stem))
        description = unquote(meta.get("description", ""))
        tools = set(parse_list(meta.get("tools", "")))
        disallowed = set(parse_list(meta.get("disallowedTools", "")))
        skills = parse_list(meta.get("skills", ""))

        writes = bool(tools & {"Write", "Edit", "MultiEdit", "NotebookEdit"}) or not tools
        bash = ("Bash" in tools or not tools) and "Bash" not in disallowed
        sandbox = "workspace-write" if (writes or bash) else "read-only"

        extra = ["- " + BLOCKED_RULE]
        if not writes:
            extra.append("- Upstream gives this role no file-writing tools: do not edit files.")
        if not bash:
            extra.append(
                "- Upstream gives this role no Bash: use the shell only to read and"
                " search files, never to build, run, install, or change git state."
            )
        if skills:
            extra.append(
                "- Preloaded skills: read "
                + ", ".join(f"`.claude/skills/{s}/SKILL.md`" for s in skills)
                + " before starting."
            )
        if unquote(meta.get("memory", "")) == "project":
            extra.append(
                f"- Your memory file is `.claude/agent-memory/{name}/MEMORY.md`. Read it"
                " first if it exists and record durable lessons there (see"
                " `.claude/rules/agent-memory.md`)."
            )
        instructions = slash_to_dollar(body.rstrip(), skill_names) + AGENT_FOOTER.format(
            extra=("\n" + "\n".join(extra) + "\n") if extra else ""
        )

        tier = tiers.tier_for(name, unquote(meta.get("model", "")))
        toml = (
            f"# Generated from .claude/agents/{agent_md.name} by convert_to_codex.py.\n"
            f"name = {json.dumps(name, ensure_ascii=False)}\n"
            f"description = {json.dumps(description, ensure_ascii=False)}\n"
            f'sandbox_mode = "{sandbox}"\n'
            + tiers.toml_lines(tier)
            + f"developer_instructions = {toml_multiline(instructions)}\n"
        )
        tomllib.loads(toml)  # fail loudly on anything Codex could not parse
        (dst / f"{name}.toml").write_text(toml, encoding="utf-8", newline="\n")
        roster.append((name, description, tier or "session"))
    return roster


# --- hooks ----------------------------------------------------------------------

QUIET_EVENTS = {"Stop", "PreCompact", "PostCompact", "SubagentStart", "SubagentStop"}
DROPPED_EVENTS = {"Notification"}  # no Codex equivalent


def convert_hooks(src, out):
    settings = json.loads((src / ".claude" / "settings.json").read_text(encoding="utf-8"))
    codex = {}
    dropped = []
    for event, groups in settings.get("hooks", {}).items():
        if event in DROPPED_EVENTS:
            dropped.append(event)
            continue
        new_groups = []
        for group in groups:
            matcher = group.get("matcher", "")
            if event in QUIET_EVENTS:
                mode = "quiet"
            elif matcher in ("Write|Edit", "Edit|Write"):
                mode, matcher = "patch", "^(apply_patch|Edit|Write)$"
            elif matcher in ("Bash|PowerShell", "Bash"):
                mode, matcher = "pass", "^Bash$"
            else:
                mode = "pass"
            handlers = []
            for h in group.get("hooks", []):
                m = re.search(r"(\.claude/hooks/[\w.-]+\.sh)", h.get("command", ""))
                if not m:
                    dropped.append(f"{event}: {h.get('command')}")
                    continue
                handlers.append({
                    "type": "command",
                    "command": f"bash .codex/hooks/codex-hook.sh {mode} {m.group(1)}",
                    "timeout": h.get("timeout", 10) + (5 if mode == "patch" else 0),
                })
            if handlers:
                g = {"hooks": handlers}
                if matcher:
                    g["matcher"] = matcher
                new_groups.append(g)
        if new_groups:
            codex[event] = new_groups
    doc = {
        "description": "Claude Code Game Studios hooks, run under Codex via .codex/hooks/codex-hook.sh",
        "hooks": codex,
    }
    path = out / ".codex" / "hooks.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8", newline="\n")
    return dropped


# --- AGENTS.md ------------------------------------------------------------------

COMPAT = """## Codex compatibility (read first)

This repository is **Claude Code Game Studios** adapted to run in OpenAI Codex.
The skills (`.claude/skills/`), agents (`.claude/agents/`), rules and docs were
written for Claude Code and are kept unchanged as the source of truth. When they
use Claude Code vocabulary, do this instead:

| Upstream text says | In Codex |
|---|---|
| `/name` (`/start`, `/dev-story`, `/settings ...`) | the skill `$name` (wrappers live in `.agents/skills/`) |
| `AskUserQuestion` (any question/options block) | Ask in chat: one short question, numbered options, your recommendation marked. Then **stop and wait**. A turn that ends without the user's answer is not an answer. |
| `Agent` / `Task` tool, "spawn `subagent_type: X`", "spawn the X agent" | Spawn the Codex custom agent `X` (`.codex/agents/X.toml`) with the prompt the skill specifies. If subagents are unavailable, or the user wants fewer spawns, take the role yourself: read `.claude/agents/X.md`, follow it for that step, then return to the skill. |
| `Read` / `Glob` / `Grep` / `Write` / `Edit` | your normal file reading, searching and `apply_patch` |
| a skill line starting with `` !`command` `` | run that command first; its output is the config the skill calls "resolved above" |
| `${CLAUDE_SKILL_DIR}` | `.claude/skills/<skill-name>` |
| `${CLAUDE_PROJECT_DIR}` | the repository root |
| `CLAUDE.md` | this file. `$setup-engine` still writes the engine choice into `CLAUDE.md`; see "Technology Stack" below. |
| `/clear` | Codex `/new` (then read `production/session-state/active.md`) |
| `model: haiku / sonnet / opus` | see "Model tiers" below: custom agents carry their tier's model; light skills delegate to `ccgs-light-runner`; heavy skills recommend a model switch |
| `maxTurns`, `allowed-tools` | ignore |
| Agent teams (several Claude Code sessions sharing a task list) | not available in Codex; use subagents or one session |
| agent `memory: project` | `.claude/agent-memory/<agent>/MEMORY.md` |
| Claude Code hooks, deny rules | `.codex/hooks.json` and `.codex/rules/ccgs.rules` run the same checks (trust the hooks once with `/hooks`) |

Also:
- Start Codex from the repository root; the hooks use repo-relative paths.
- Never read, print or edit `.env` files (upstream denies this in its settings).
- Path-scoped rules: before you create or edit a file that matches a glob in
  the table under "Path-scoped rules", read that rule file and follow it.
"""


NOTES_BEGIN = "<!-- BEGIN PROJECT NOTES: kept when convert_to_codex.py regenerates this file -->"
NOTES_END = "<!-- END PROJECT NOTES -->"
DEFAULT_NOTES = "_Add your own project instructions for Codex here._"


def model_tier_section(tiers, skills_by_tier, roster):
    agents_by_tier = {}
    for name, _, tier in roster:
        agents_by_tier.setdefault(tier, []).append(name)
    agents_by_tier.setdefault("light", []).append(LIGHT_RUNNER)
    for tier in tiers.ladder:
        agents_by_tier.setdefault(tier, []).append(f"ccgs-{tier}")

    def names(items):
        return ", ".join(n if n.startswith("all other") else f"`{n}`" for n in items) if items else "—"

    rows = ""
    for tier in [t for t in tiers.tiers if t not in tiers.ladder] + ["session"] + tiers.ladder:
        if tier == "session":
            model = "the session's model"
        else:
            t = tiers.tiers[tier]
            model = f"`{t['model']}` ({t['reasoning_effort']})"
        agents = agents_by_tier.get(tier, [])
        skills = [f"${s}" for s in skills_by_tier.get(tier, [])]
        if tier == "standard":
            agents = [f"all other agents ({len(agents)})"] if agents else []
            skills_text = "all other skills (they run on the session model)"
        elif agents or skills:
            skills_text = names(skills)
        else:
            continue
        if tier in tiers.ladder:
            ladder = [f"ccgs-{t}" for t in tiers.ladder[tiers.ladder.index(tier) + 1:]]
        else:
            ladder = tiers.escalation_for(None if tier == "session" else tier)
        escalate = " → ".join(f"`{a}`" for a in ladder) + " → ask the user" if ladder else "ask the user"
        rows += f"| **{tier}** | {model} | {names(agents)} | {skills_text} | {escalate} |\n"

    escalation = ""
    if tiers.ladder:
        escalation = f"""
### Escalation when an agent is stuck

Agents return a report starting with `BLOCKED:` when they cannot finish or are
not confident in the result. When that happens, or when an agent's result is
clearly unusable (fails its acceptance criteria, tests still fail, contradicts
the spec or the user's decisions):

1. Retry the step with the next agent in the "If BLOCKED" column above, in
   order. Give it the role or skill, the original task, the failure report (and
   any earlier escalation reports), and the files involved.
2. Tell the user in one line each time you escalate, e.g. "game-designer got
   stuck on the economy formula; retrying on ccgs-escalation."
3. If the last level is also BLOCKED, stop and tell the user what each level
   tried and what is still blocking, with options for how to proceed.
4. Escalate each step at most once per level. Questions for the user and the
   creative decisions in "Project notes" are never escalated: they go to the
   user.
5. If you (the main session) are stuck on a step after a real attempt and the
   session model is weaker than the ladder, hand that step to the ladder the
   same way.
"""
    return (
        "\n## Model tiers\n\n"
        "Upstream rates every skill and agent by difficulty; `codex-port/model_tiers.toml`\n"
        "maps the ratings to Codex models. Custom agents run on their tier's model.\n"
        "Skills run in this session, so a skill cannot change the model: light skills\n"
        f"are delegated to `{LIGHT_RUNNER}`, heavy skills ask the user to consider\n"
        "`/model`, and standard skills run on the session model.\n\n"
        "| Tier | Model (effort) | Agents | Skills | If BLOCKED |\n|---|---|---|---|---|\n"
        + rows
        + escalation
    )


def build_agents_md(src, out, skill_names, roster, rule_rows, tiers, skills_by_tier):
    text = (src / "CLAUDE.md").read_text(encoding="utf-8")

    def inline(match):
        rel = match.group(1).strip()
        p = src / rel
        if "engine-reference" in rel:
            return (
                "Read `docs/engine-reference/<engine>/VERSION.md` for the engine set in"
                " `project.yaml` (or `CLAUDE.md`) before any engine-specific work.\n"
            )
        if not p.exists():
            return f"See `{rel}`."
        return f"<!-- inlined from {rel} -->\n" + demote_headings(p.read_text(encoding="utf-8").strip(), 2) + "\n"

    text = re.sub(r"<!-- ENGINE-REFERENCE-IMPORT.*?-->\n", "", text, flags=re.S)
    text = re.sub(r"^@(\S+)\s*$", inline, text, flags=re.M)

    # The stack is written into CLAUDE.md by $setup-engine; point there instead of
    # freezing a copy that would go stale.
    text = re.sub(
        r"(## Technology Stack\n)(.*?)(?=\n## )",
        r"\1\nThe engine, language and pipeline are configured by `$setup-engine` in\n"
        r"`project.yaml` and in the 'Technology Stack' section of `CLAUDE.md`. Read\n"
        r"them at the start of any engine or code work.\n",
        text,
        flags=re.S,
    )
    text = text.replace("Claude Code subagents", "agents (Codex custom agents)")
    text = text.replace(
        "load only when Claude Code starts here", "load only when Codex starts here"
    )
    text = re.sub(r"^# Claude Code Game Studios", "# Codex Game Studios", text, count=1, flags=re.M)
    text = text.replace("`/clear`", "`/new`")
    text = slash_to_dollar(text, skill_names)

    first_nl = text.index("\n")
    head, rest = text[: first_nl + 1], text[first_nl + 1:]

    rules = "\n## Path-scoped rules\n\n| Rule file | Applies to |\n|---|---|\n" + "".join(
        f"| `{r}` | {', '.join(f'`{g}`' for g in globs)} |\n" for r, globs in rule_rows
    )
    # Names only: each agent's description is in its .codex/agents/<name>.toml and
    # the full role in .claude/agents/<name>.md. Keeps AGENTS.md under Codex's
    # 32 KiB project-doc limit.
    agents = (
        "\n## Agent roster\n\nCustom agents in `.codex/agents/` (full roles in"
        " `.claude/agents/<name>.md`):\n"
        + ", ".join(f"`{n}`" for n, _, _ in roster)
        + "\n"
    )

    target = out / "AGENTS.md"
    preset = HERE / "preset" / "project-notes.md"
    notes = preset.read_text(encoding="utf-8").rstrip("\n") if preset.exists() else DEFAULT_NOTES
    if target.exists():
        old = target.read_text(encoding="utf-8")
        m = re.search(re.escape(NOTES_BEGIN) + r"\n(.*?)\n" + re.escape(NOTES_END), old, re.S)
        if m:
            notes = m.group(1)
    project_notes = f"\n## Project notes\n\n{NOTES_BEGIN}\n{notes}\n{NOTES_END}\n"

    # Project notes go right after the compatibility table: Codex truncates
    # AGENTS.md past project_doc_max_bytes, and the user's rules must survive.
    body = (
        head
        + "\n<!-- Generated by codex-port/convert_to_codex.py. Only the Project notes"
        " block survives regeneration. -->\n\n"
        + COMPAT
        + project_notes
        + "\n"
        + rest.rstrip()
        + "\n"
        + model_tier_section(tiers, skills_by_tier, roster)
        + rules
        + agents
    )
    target.write_text(body, encoding="utf-8", newline="\n")
    return len(body.encode("utf-8"))


def rule_table(src):
    rows = []
    for rule in sorted((src / ".claude" / "rules").glob("*.md")):
        text = rule.read_text(encoding="utf-8")
        globs = re.findall(r'^\s*-\s*"([^"]+)"', text.split("\n---", 1)[0], re.M)
        if globs:
            rows.append((f".claude/rules/{rule.name}", globs))
    # Folder-level CLAUDE.md files (design/, docs/, src/): Claude Code loads them
    # when it works in that folder; Codex does not, so list them as rules too.
    for nested in sorted(src.glob("*/CLAUDE.md")):
        folder = nested.parent.name
        if not folder.startswith(".") and " " not in folder:
            rows.append((f"{folder}/CLAUDE.md", [f"{folder}/**"]))
    return rows


# --- template presets -------------------------------------------------------------

UPSTREAM_META = ["README.md", "CHANGELOG.md", "CONTRIBUTING.md", "SECURITY.md", "UPGRADING.md"]


def apply_project_modes_preset(out):
    """Append preset/project-modes.yaml to a fresh project.yaml that has no modes block."""
    preset = HERE / "preset" / "project-modes.yaml"
    target = out / "project.yaml"
    if not preset.exists() or not target.exists():
        return
    text = target.read_text(encoding="utf-8")
    if re.search(r"^modes:", text, re.M):
        return
    target.write_text(
        text.rstrip("\n") + "\n\n" + preset.read_text(encoding="utf-8"),
        encoding="utf-8",
        newline="\n",
    )


# --- main -----------------------------------------------------------------------

def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    src, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    if not (src / "CLAUDE.md").exists() or not (src / ".claude" / "skills").is_dir():
        sys.exit(f"{src} does not look like a Claude Code Game Studios checkout")

    # Never delete or overwrite a user's project. Two modes only:
    #   new folder   -> copy upstream, then add the Codex layer
    #   src == out   -> regenerate the Codex layer in place (after editing
    #                   model_tiers.toml, or after updating .claude/ from upstream)
    if src == out:
        print(f"Regenerating the Codex layer in {out}")
    elif out.exists() and any(out.iterdir()):
        sys.exit(
            f"{out} already exists and is not empty; refusing to touch it.\n"
            "Pass a new folder to create a fresh copy, or run with the same folder\n"
            "twice (`convert_to_codex.py . .`) to regenerate the Codex layer in place."
        )
    else:
        # .github holds upstream's own CODEOWNERS, funding and issue templates.
        shutil.copytree(src, out, ignore=shutil.ignore_patterns(".git", ".github"), dirs_exist_ok=True)
        # Upstream's repository docs move aside so the template's root README is
        # the Codex one; they stay available under upstream/.
        for name in UPSTREAM_META:
            if (out / name).exists():
                (out / "upstream").mkdir(exist_ok=True)
                shutil.move(out / name, out / "upstream" / name)
        apply_project_modes_preset(out)

    tiers = Tiers(HERE / "model_tiers.toml")
    implicit = tomllib.loads((HERE / "skills.toml").read_text(encoding="utf-8")).get(
        "implicit_invocation", "upstream"
    )
    if implicit not in ("upstream", "all"):
        sys.exit(f"skills.toml: implicit_invocation must be \"upstream\" or \"all\", not {implicit!r}")
    shutil.copytree(OVERLAY, out, dirs_exist_ok=True)

    skill_names = [p.name for p in (src / ".claude" / "skills").iterdir() if (p / "SKILL.md").exists()]
    skills_by_tier = convert_skills(src, out, skill_names, tiers, implicit)
    roster = convert_agents(src, out, skill_names, tiers)
    dropped = convert_hooks(src, out)
    size = build_agents_md(src, out, skill_names, roster, rule_table(src), tiers, skills_by_tier)
    if HERE != (out / "codex-port").resolve():
        shutil.copytree(HERE, out / "codex-port", ignore=shutil.ignore_patterns("__pycache__"),
                        dirs_exist_ok=True)

    n_skills = sum(len(v) for v in skills_by_tier.values())
    print(f"skills: {n_skills}  agents: {len(roster)}  AGENTS.md: {size} bytes")
    print("skill tiers: " + ", ".join(f"{k} {len(v)}" for k, v in skills_by_tier.items()))
    agent_tiers = {}
    for _, _, t in roster:
        agent_tiers[t] = agent_tiers.get(t, 0) + 1
    print("agent tiers: " + ", ".join(f"{k} {v}" for k, v in agent_tiers.items()))
    if size > 32 * 1024:
        print("WARNING: AGENTS.md exceeds Codex's default 32 KiB project_doc_max_bytes")
    for d in dropped:
        print(f"hook not ported: {d}")


if __name__ == "__main__":
    main()
