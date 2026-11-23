#!/usr/bin/env bash
# Make the JPEG copies of an adventure's interior illustrations that the print sources include.
#
#   scripts/build-adventure-print-art.sh [slug]      (default slug: hollow-hearth)
#
# Run it inside the pinned container, like every other print build step:
#   docker run --rm -u "$(id -u):$(id -g)" -v "$PWD":/work -w /work at-the-last-throw-tex:tl2024 \
#     scripts/build-adventure-print-art.sh
#
# The full-resolution PNG originals in assets/<slug>/ stay the source. Embedded as PNG, every
# illustration costs about 3 MB of lossless data and each adventure PDF weighed about 36 MB.
# Interior pages are pure white, so flattening the alpha channel onto white changes nothing
# on the page. Same pixel size as the original, quality 92, no chroma subsampling, no metadata.
# The cover overlays (front-overlay, back-overlay) stay PNG: they sit on the parchment cover
# and need their transparency.
set -euo pipefail
cd "$(dirname "$0")/.."
slug=${1:-hollow-hearth}
if command -v magick >/dev/null 2>&1; then IM=magick; else IM=convert; fi

for png in "assets/${slug}"/*.png; do
  name=$(basename "$png" .png)
  case "$name" in *-overlay) continue ;; esac
  "$IM" "$png" -background white -alpha remove -alpha off \
    -sampling-factor 1x1 -quality 92 -strip "assets/${slug}/${name}.jpg"
  echo "assets/${slug}/${name}.jpg"
done
