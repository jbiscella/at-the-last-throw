#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ImageMagick 7 installs `magick`; ImageMagick 6 only `convert`.
if command -v magick >/dev/null 2>&1; then IM=magick; else IM=convert; fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

# check SOURCE PAGES: builds SOURCE.tex, rejects typesetting problems and checks the page count,
# then typesets the words without the artwork and counts, page by page, the text pixels that
# land on the artwork's dark engraved lines (rules, frames, checkboxes).
check() {
  local source=$1 pages=$2
  for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error "${source}.tex" >"build-${source}.log" 2>&1
  done
  if grep -E 'Overfull \\hbox|Missing character:|Font shape .* undefined' "build-${source}.log"; then
    echo "Review typesetting of ${source}" >&2
    exit 1
  fi
  pdfinfo "${source}.pdf" | grep -q "Pages: *${pages}\$"

  for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error -output-directory="$work" -jobname="text-${source}" \
      "\\def\\SheetTextOnly{1}\\input{${source}.tex}" >"$work/text-${source}.log" 2>&1
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

# Pregenerated Protagonists of The Bell of Hollow Hearth, one page each (pregens/hollow-hearth-*.tex).
for language in en it fr uk de es; do
  check "hollow-hearth-pregens-${language}" 4
done
