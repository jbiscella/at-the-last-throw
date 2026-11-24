#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ImageMagick 7 installs `magick`; ImageMagick 6 only `convert`.
if command -v magick >/dev/null 2>&1; then IM=magick; else IM=convert; fi
work=$(mktemp -d)

# The sheets embed a JPEG copy of the artwork (quality 95, no chroma subsampling): 0.9 MB instead
# of 2.7 MB in each of the 30 PDFs, with no visible difference. The PNG stays the source, and the
# collision test below measures the engraved lines on the PNG.
"$IM" assets/character-background.png -sampling-factor 1x1 -quality 95 -strip assets/character-background.jpg
trap 'rm -rf "$work"' EXIT

# run_xelatex LOG ARGS...: runs XeLaTeX quietly; on failure shows the TeX error from LOG and stops.
run_xelatex() {
  local log=$1; shift
  if ! xelatex "$@" >"$log" 2>&1; then
    echo "XeLaTeX failed (full log: $log):" >&2
    grep -A3 '^!' "$log" | head -n 12 >&2 || tail -n 20 "$log" >&2
    exit 1
  fi
}

# check JOB PAGES [SOURCE [DEFINITIONS]]: builds SOURCE.tex (default JOB.tex) as JOB.pdf after the
# TeX DEFINITIONS, rejects typesetting problems and checks the page count,
# then typesets the words without the artwork and counts, page by page, the text pixels that
# land on the artwork's dark engraved lines (rules, frames, checkboxes).
check() {
  local source=$1 pages=$2 input=${3:-$1} defs=${4:-}
  for pass in 1 2; do
    run_xelatex "build-${source}.log" -interaction=nonstopmode -halt-on-error -jobname="${source}" "${defs}\\input{${input}.tex}"
  done
  if grep -E 'Overfull \\hbox|Missing character:|Font shape .* undefined' "build-${source}.log"; then
    echo "Review typesetting of ${source}" >&2
    exit 1
  fi
  if ! pdfinfo "${source}.pdf" | grep -q "Pages: *${pages}\$"; then
    echo "${source}: expected ${pages} page(s)" >&2
    exit 1
  fi

  for pass in 1 2; do
    run_xelatex "$work/text-${source}.log" -interaction=nonstopmode -halt-on-error -output-directory="$work" \
      -jobname="text-${source}" "${defs}\\def\\SheetTextOnly{1}\\input{${input}.tex}"
  done
  for page in $(seq 1 "$pages"); do
    pdftoppm -r 200 -gray -png -singlefile -f "$page" -l "$page" "$work/text-${source}.pdf" "$work/text-${source}"
    size=$($IM "$work/text-${source}.png" -format '%wx%h' info:)
    $IM "$work/text-${source}.png" -threshold 55% -negate "$work/text-mask.png"
    $IM assets/character-background.png -colorspace Gray -resize "${size}!" -threshold 27% -negate "$work/line-mask.png"
    overlap=$($IM "$work/text-mask.png" "$work/line-mask.png" -compose Multiply -composite -format '%[fx:round(mean*w*h)]' info:)
    if [ "$overlap" -gt 0 ]; then
      echo "${source} page ${page}: ${overlap} text pixels touch the engraved lines" >&2
      exit 1
    fi
  done
  echo "${source}: ${pages} A4 page(s), no overfull boxes, missing glyphs or font substitutions, text clear of the artwork"
}

# Blank sheets, one page each.
for language in en it fr uk de es; do
  check "character-${language}" 1
done

# Pregenerated Protagonists of The Bell of Hollow Hearth: one A4 PDF per character, built from the
# language's data file (pregens/hollow-hearth-<lang>.tex) with only that character printed.
for language in en it fr uk de es; do
  for character in aldren-varr nim-thistledown mara-veyne elyra-ashenveil; do
    check "hollow-hearth-${character}-${language}" 1 "hollow-hearth-pregens-${language}" "\\def\\PregenOnly{${character}}"
  done
done
