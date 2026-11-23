#!/usr/bin/env bash
# Compare the page count of every published PDF (docs/downloads/*.pdf, every language) with the
# same file at a git reference.
#
#   scripts/check-page-counts.sh [ref]      (default ref: origin/main)
#
# Prints one line per PDF and exits 1 if any count changed, so a change cannot go unnoticed.
# A changed count may be intended (new content, a new layout): explain each one in the pull
# request. A one-page growth also moves every later page, so re-check the page references that
# cite that PDF (AGENTS.md, "Manual page references"). Needs git and pdfinfo (poppler-utils),
# both on the host and in the pinned container.
set -euo pipefail
cd "$(dirname "$0")/.."
ref=${1:-origin/main}
tmp=$(mktemp)
trap 'rm -f "$tmp"' EXIT

pages() { pdfinfo "$1" 2>/dev/null | awk '/^Pages:/{print $2}'; }

changed=0
printf '%-44s %6s %6s\n' "docs/downloads/" "$ref" "now"
for file in $(git ls-files 'docs/downloads/*.pdf'); do
  now=$(pages "$file")
  if git cat-file -e "${ref}:${file}" 2>/dev/null; then
    git show "${ref}:${file}" >"$tmp"
    before=$(pages "$tmp")
  else
    before="new"
  fi
  mark=""
  if [ "$before" != "new" ] && [ "$before" != "$now" ]; then
    mark="  CHANGED"
    changed=1
  fi
  printf '%-44s %6s %6s%s\n' "${file#docs/downloads/}" "$before" "$now" "$mark"
done

if [ "$changed" -ne 0 ]; then
  echo "Page counts changed against ${ref}: explain each change in the pull request." >&2
  exit 1
fi
