#!/usr/bin/env bash
# Add Codex Game Studios to an existing game project.
#
#   bash <template>/codex-port/add-to-project.sh <existing-project-folder>
#
# Never overwrites or deletes anything in the project:
#   - a file the project does not have is copied in;
#   - a file that already exists with different content is left alone, and the
#     template's version is written next to it as <file>.ccgs-new;
#   - .gitignore only gets the studio's local/session entries appended.
# It commits nothing. Re-running it is safe.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: bash add-to-project.sh <existing-project-folder>" >&2
  exit 1
fi

template="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ ! -f "$template/AGENTS.md" ] || [ ! -d "$template/.claude/skills" ]; then
  echo "add-to-project.sh: $template is not a Codex Game Studios template" >&2
  exit 1
fi
if [ ! -d "$1" ]; then
  echo "add-to-project.sh: $1 does not exist (for a brand-new game use new-game.sh)" >&2
  exit 1
fi
target="$(cd "$1" && pwd)"
case "$target/" in
  "$template"/*)
    echo "add-to-project.sh: the project cannot be the template or inside it" >&2
    exit 1
    ;;
esac

if git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  is_git=1
  if [ -z "${CCGS_NEW_GAME:-}" ] && [ -n "$(git -C "$target" status --porcelain 2>/dev/null | head -1)" ]; then
    echo "Note: the project has uncommitted changes. Nothing will be overwritten,"
    echo "      but committing first makes this step easy to review and undo."
    echo
  fi
else
  is_git=0
fi

added=0
same=0
conflicts=()

# Repository-only files (READMEs, guides, upstream's repo docs and CI, and the
# framework's own skill test suite) are not part of a game project.
while IFS= read -r -d '' f; do
  rel="${f#./}"
  case "$rel" in
    README.md|README.zh-CN.md|LICENSE|.gitignore|.gitattributes|src/.gitkeep) continue ;;
    upstream/*|guide/*) continue ;;
    production/session-state/*|production/session-logs/*|.claude/agent-memory/*)
      case "${rel##*/}" in .gitkeep) ;; *) continue ;; esac ;;
  esac
  dest="$target/$rel"
  if [ ! -e "$dest" ]; then
    mkdir -p "$(dirname "$dest")"
    cp "$template/$rel" "$dest"
    added=$((added + 1))
  elif cmp -s "$template/$rel" "$dest"; then
    same=$((same + 1))
  else
    cp "$template/$rel" "$dest.ccgs-new"
    conflicts+=("$rel")
  fi
done < <(cd "$template" && find . \( -path ./.git -o -path ./.github \
           -o -path "./CCGS Skill Testing Framework" \) -prune -o -type f -print0)

# MIT attribution for the copied framework.
if [ ! -e "$target/.claude/CCGS-LICENSE.txt" ]; then
  cp "$template/LICENSE" "$target/.claude/CCGS-LICENSE.txt"
fi

# Studio-only ignore entries. Upstream's engine and build rules are not merged:
# they could hide files this project tracks on purpose (e.g. *.csproj).
ignore_lines=(
  ".claude/settings.local.json"
  "CLAUDE.local.md"
  "project.local.yaml"
  "production/session-logs/"
  "production/session-state/"
  ".scratch/"
  ".claude/agent-memory/"
  "docs/consistency-failures.md"
  "*.ccgs-new"
)
missing=()
for line in "${ignore_lines[@]}"; do
  grep -qxF -- "$line" "$target/.gitignore" 2>/dev/null || missing+=("$line")
done
if [ ${#missing[@]} -gt 0 ]; then
  {
    [ -s "$target/.gitignore" ] && [ -n "$(tail -c1 "$target/.gitignore")" ] && echo
    echo
    echo "# === Codex Game Studios: local and session files ==="
    printf '%s\n' "${missing[@]}"
  } >> "$target/.gitignore"
fi

[ "$is_git" = 1 ] && git -C "$target" config core.longpaths true

echo "Codex Game Studios added to: $target"
echo "  new files copied:        $added"
echo "  already identical:       $same"
echo "  .gitignore lines added:  ${#missing[@]}"
if [ ${#conflicts[@]} -gt 0 ]; then
  echo
  echo "These files already existed and were NOT changed. The template's version"
  echo "is next to each one as <file>.ccgs-new; merge them, then delete the .ccgs-new:"
  printf '  %s\n' "${conflicts[@]}"
  for c in "${conflicts[@]}"; do
    if [ "$c" = "AGENTS.md" ]; then
      echo
      echo "  AGENTS.md matters most: until it is merged, Codex reads your old file"
      echo "  and the studio rules are inactive. Move your own rules into the"
      echo "  \"Project notes\" block of AGENTS.md.ccgs-new, then replace AGENTS.md with it."
    fi
  done
fi
[ "$is_git" = 0 ] && { echo; echo "Note: not a git repository. The hooks expect git; run 'git init' in the project."; }
if [ -n "${CCGS_NEW_GAME:-}" ]; then
  step3='Say what game you want to make, or type $start.'
else
  step3='Say "analyze this existing project", or type $adopt for a migration plan.'
fi
cat <<EOF

Next:
  1. Start Codex in the project folder:   cd "$target" && codex
  2. Trust the project, then type /hooks and trust the project hooks.
  3. $step3
EOF
