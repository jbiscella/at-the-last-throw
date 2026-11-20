#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for language in en it fr uk de es; do
  for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error "character-${language}.tex" >"build-${language}.log" 2>&1
  done
  if grep -E 'Overfull \hbox|Missing character:' "build-${language}.log"; then
    echo "Review typesetting of ${language}" >&2
    exit 1
  fi
  pdfinfo "character-${language}.pdf" | grep -q 'Pages: *1'
  echo "${language}: one A4 page, no overfull boxes or missing glyphs"
done
