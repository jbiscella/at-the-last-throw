#!/usr/bin/env bash
# Build an adventure's print PDFs and publish them to docs/downloads/.
#
#   scripts/build-adventure-pdfs.sh [slug]      (default slug: hollow-hearth)
#
# Run it inside the pinned container, like every other print build step:
#   docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/work -w /work at-the-last-throw-tex:tl2024 \
#     scripts/build-adventure-pdfs.sh
#
# Each adventure/<slug>-<lang>.tex is typeset from the repository root with two XeLaTeX passes
# (the second resolves the contents and page references). The build stops on a TeX error, an
# overfull line or a missing glyph, then copies build/<slug>-<lang>.pdf to
# docs/downloads/<slug>-<lang>.pdf. Run scripts/build-adventure-print-art.sh first whenever a
# PNG original changed.
set -euo pipefail
cd "$(dirname "$0")/.."
slug=${1:-hollow-hearth}
mkdir -p build

for source in adventure/"${slug}"-*.tex; do
  job=$(basename "$source" .tex)
  for pass in 1 2; do
    if ! xelatex -interaction=nonstopmode -halt-on-error -output-directory=build "$source" \
        >"build/${job}.console.log" 2>&1; then
      echo "XeLaTeX failed on ${source} (log: build/${job}.log):" >&2
      grep -A3 '^!' "build/${job}.log" | head -n 12 >&2 || tail -n 20 "build/${job}.console.log" >&2
      exit 1
    fi
  done
  if grep -E 'Overfull \\hbox|Missing character:' "build/${job}.log"; then
    echo "Review the typesetting of ${source}" >&2
    exit 1
  fi
  cp "build/${job}.pdf" "docs/downloads/${job}.pdf"
  echo "docs/downloads/${job}.pdf: $(pdfinfo "build/${job}.pdf" | awk '/^Pages:/{print $2}') pages"
done
