#!/usr/bin/env bash
# Create a new game project from this Codex Game Studios template.
#
#   bash <template>/codex-port/new-game.sh <new-project-folder>
#
# The folder must be new or empty. Runs `git init` (long paths enabled), copies
# the template's .gitignore and .gitattributes, then installs the studio with
# add-to-project.sh. It commits nothing.

set -euo pipefail

if [ $# -ne 1 ]; then
  echo "usage: bash new-game.sh <new-project-folder>" >&2
  exit 1
fi

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template="$(cd "$here/.." && pwd)"
target="$1"

if [ -e "$target" ] && [ -n "$(ls -A "$target" 2>/dev/null)" ]; then
  echo "new-game.sh: $target already exists and is not empty; refusing to touch it." >&2
  echo "             To add the studio to an existing game, use add-to-project.sh." >&2
  exit 1
fi

mkdir -p "$target"
target="$(cd "$target" && pwd)"
case "$target/" in
  "$template"/*)
    echo "new-game.sh: the new project cannot be inside the template folder" >&2
    rmdir "$target" 2>/dev/null || true
    exit 1
    ;;
esac

git -C "$target" init -q
git -C "$target" config core.longpaths true
for f in .gitignore .gitattributes; do
  [ -f "$template/$f" ] && cp "$template/$f" "$target/$f"
done

CCGS_NEW_GAME=1 bash "$here/add-to-project.sh" "$target"
