#!/usr/bin/env bash
# Codex adapter for the Claude Code Game Studios hooks in .claude/hooks/.
#
#   bash .codex/hooks/codex-hook.sh <mode> <hook-script>
#
# Codex hooks take the same stdin JSON shape and exit-2-blocks convention as
# Claude Code, so most hooks run unchanged. Three differences are bridged here:
#
#   pass   Run the hook as-is (SessionStart, PreToolUse on Bash).
#   quiet  Run the hook, send its stdout to stderr, always exit 0. For events
#          where Codex parses stdout as a decision (Stop, compaction, subagent
#          events): the upstream hooks print human-readable logs there.
#   patch  Codex edits files with apply_patch, whose tool_input is the patch
#          text, not a file_path. Extract every added/updated/moved file from
#          the patch and run the hook once per file with Claude-shaped input
#          ({"tool_name":"Write","tool_input":{"file_path":...}}), merging the
#          advisory messages into one hook JSON object.

mode="$1"
hook="$2"

root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$root" 2>/dev/null || exit 0
export CLAUDE_PROJECT_DIR="$root"

# A missing hook must never block the agent.
[ -n "$hook" ] && [ -f "$hook" ] || exit 0

case "$mode" in
  pass)
    exec bash "$hook"
    ;;
  quiet)
    bash "$hook" >&2
    exit 0
    ;;
  patch)
    ;;
  *)
    echo "codex-hook.sh: unknown mode '$mode'" >&2
    exit 0
    ;;
esac

input=$(cat)

# An Edit/Write-style payload that already names the file: pass it through.
case "$input" in
  *'"file_path"'*)
    printf '%s' "$input" | bash "$hook"
    exit $?
    ;;
esac

# Decode the JSON-escaped patch just enough to read its file headers. `\\` goes
# through a placeholder first so a Windows path like C:\\new is not split at \n.
paths=$(printf '%s' "$input" \
  | LC_ALL=C awk '{ gsub(/\\\\/, "\002"); gsub(/\\r/, ""); gsub(/\\n/, "\n"); print }' \
  | tr '\002' '/' \
  | LC_ALL=C sed -n -E 's/^\*\*\* (Add File|Update File|Move to): (.*)$/\2/p' \
  | sed 's/[[:space:]]*$//')

[ -n "$paths" ] || exit 0

status=0
msgs=""
while IFS= read -r p; do
  [ -n "$p" ] || continue
  esc=$(printf '%s' "$p" | sed 's/\\/\\\\/g; s/"/\\"/g')
  out=$(printf '{"tool_name":"Write","tool_input":{"file_path":"%s"}}' "$esc" | bash "$hook")
  rc=$?
  [ "$rc" -eq 2 ] && status=2
  [ -n "$out" ] || continue
  # hook_warn (yaml-helper.sh) prints {"systemMessage":"<escaped>",...}; reuse
  # the already-escaped message, or escape plain text ourselves.
  m=$(printf '%s' "$out" | sed -n 's/^{"systemMessage":"\(.*\)","hookSpecificOutput".*$/\1/p' | head -1)
  if [ -z "$m" ]; then
    m=$(printf '%s' "$out" | tr -d '\000-\010\013-\037' \
        | sed 's/\\/\\\\/g; s/"/\\"/g' \
        | awk '{ gsub(/\t/, "\\t"); if (NR > 1) printf "\\n"; printf "%s", $0 }')
  fi
  msgs="${msgs:+$msgs\\n\\n}$m"
done <<EOF
$paths
EOF

if [ -n "$msgs" ]; then
  printf '{"systemMessage":"%s","hookSpecificOutput":{"hookEventName":"PostToolUse","additionalContext":"%s"}}\n' \
    "$msgs" "$msgs"
fi
exit "$status"
