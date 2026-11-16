#!/usr/bin/env bash
# Pixel-compare two PDFs page by page (default 72 dpi, as in the project's QA reports).
# Usage: scripts/compare-pdf.sh BASELINE.pdf CANDIDATE.pdf [DPI]
# If DIFF_DIR is set, a diff image (changes highlighted in red) is written there
# for every page that differs, named <candidate>-page-NN.png.
# Exit status: 0 = identical, 1 = differences found, 2 = usage/tool error.
set -euo pipefail
[ $# -ge 2 ] || { echo "usage: $0 BASELINE.pdf CANDIDATE.pdf [DPI]" >&2; exit 2; }
base=$1 cand=$2 dpi=${3:-72} diff_dir=${DIFF_DIR:-}
for t in pdfinfo pdftoppm compare; do command -v "$t" >/dev/null || { echo "missing tool: $t" >&2; exit 2; }; done
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
pages() { pdfinfo "$1" | awk '/^Pages:/{print $2}'; }
pb=$(pages "$base") pc=$(pages "$cand")
name=$(basename "$cand" .pdf)
status=0
[ "$pb" = "$pc" ] || { echo "page count differs: $base=$pb $cand=$pc"; status=1; }
pdftoppm -r "$dpi" -png "$base" "$tmp/a"
pdftoppm -r "$dpi" -png "$cand" "$tmp/b"
[ -z "$diff_dir" ] || mkdir -p "$diff_dir"
mapfile -t a_pages < <(ls "$tmp"/a-*.png)
mapfile -t b_pages < <(ls "$tmp"/b-*.png)
changed=0
n=$(( pb < pc ? pb : pc ))
for ((i=0; i<n; i++)); do
  out=null:
  [ -z "$diff_dir" ] || out=$(printf '%s/%s-page-%02d.png' "$diff_dir" "$name" $((i+1)))
  px=$(compare -metric AE "${a_pages[$i]}" "${b_pages[$i]}" "$out" 2>&1 || true)
  px=${px%% *}
  if [ "$px" != "0" ]; then
    echo "  page $((i+1)): $px differing pixels"; changed=$((changed+1))
  elif [ "$out" != null: ]; then
    rm -f "$out"
  fi
done
echo "$name: $changed of $n compared pages differ from $(basename "$base") at ${dpi} dpi"
[ "$changed" -eq 0 ] || status=1
exit $status
