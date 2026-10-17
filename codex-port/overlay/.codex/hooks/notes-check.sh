#!/usr/bin/env bash
# Codex SessionStart hook (port only): warn when PROJECT-NOTES.md has changed
# since convert_to_codex.py copied it into AGENTS.md. Its stdout becomes context,
# so Codex follows the edited rules before the copy is regenerated.
#
# Run through codex-hook.sh, which changes to the repository root first.

[ -f PROJECT-NOTES.md ] && [ -f AGENTS.md ] || exit 0

stamp=$(sed -n 's/.*<!-- project-notes-sha256: \([0-9a-f]*\) -->.*/\1/p' AGENTS.md | head -1)
[ -n "$stamp" ] || exit 0

# Hash without CR, matching convert_to_codex.py, so a CRLF checkout is not a change.
if command -v sha256sum >/dev/null 2>&1; then
  now=$(tr -d '\r' < PROJECT-NOTES.md | sha256sum | cut -d' ' -f1)
elif command -v shasum >/dev/null 2>&1; then
  now=$(tr -d '\r' < PROJECT-NOTES.md | shasum -a 256 | cut -d' ' -f1)
else
  exit 0
fi

[ "$now" = "$stamp" ] && exit 0

cat <<'EOF'
=== PROJECT-NOTES.md has changed since AGENTS.md was generated ===
Read PROJECT-NOTES.md now and follow it. Where it differs from the "Project notes"
copy in AGENTS.md, PROJECT-NOTES.md wins. Tell the user once that running
`python -I codex-port/convert_to_codex.py . .` refreshes the copy.
EOF
