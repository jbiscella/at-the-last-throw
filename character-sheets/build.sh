#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

# ImageMagick 7 installs `magick`; ImageMagick 6 only `convert`.
if command -v magick >/dev/null 2>&1; then IM=magick; else IM=convert; fi
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT

for language in en it fr uk de es; do
  for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error "character-${language}.tex" >"build-${language}.log" 2>&1
  done
  if grep -E 'Overfull \\hbox|Missing character:|Font shape .* undefined' "build-${language}.log"; then
    echo "Review typesetting of ${language}" >&2
    exit 1
  fi
  pdfinfo "character-${language}.pdf" | grep -q 'Pages: *1'

  # Collision test: typeset the words without the artwork, then count text pixels
  # that land on the artwork's dark engraved lines (rules, frames, checkboxes).
  for pass in 1 2; do
    xelatex -interaction=nonstopmode -halt-on-error -output-directory="$work" -jobname="text-${language}" \
      "\\def\\SheetTextOnly{1}\\input{character-${language}.tex}" >"$work/text-${language}.log" 2>&1
  done
  pdftoppm -r 200 -gray -png -singlefile "$work/text-${language}.pdf" "$work/text-${language}"
  size=$($IM "$work/text-${language}.png" -format '%wx%h' info:)
  $IM "$work/text-${language}.png" -threshold 55% -negate "$work/text-mask.png"
  $IM assets/character-background.png -colorspace Gray -resize "${size}!" -threshold 27% -negate "$work/line-mask.png"
  overlap=$($IM "$work/text-mask.png" "$work/line-mask.png" -compose Multiply -composite -format '%[fx:round(mean*w*h)]' info:)
  if [ "$overlap" -gt 0 ]; then
    echo "${language}: ${overlap} text pixels touch the engraved lines" >&2
    exit 1
  fi
  echo "${language}: one A4 page, no overfull boxes, missing glyphs or font substitutions, text clear of the artwork"
done
