#!/usr/bin/env bash
# Verify the local toolchain has everything needed to build all four editions.
set -uo pipefail
missing=0
ok()   { printf '  ok       %s\n' "$1"; }
bad()  { printf '  MISSING  %s\n' "$1"; missing=1; }
warn() { printf '  note     %s\n' "$1"; }

echo "Programs"
for p in xelatex kpsewhich fc-list make; do command -v "$p" >/dev/null && ok "$p" || bad "$p"; done
for p in pdfinfo pdftoppm compare; do command -v "$p" >/dev/null && ok "$p (for make check)" || bad "$p (for make check; poppler-utils / imagemagick)"; done

echo "LaTeX packages"
for s in fontspec babel geometry microtype xcolor tikz fancyhdr titlesec tabularx array colortbl \
         tcolorbox enumitem needspace hyperref tocloft xparse etoolbox graphicx; do
  kpsewhich "$s.sty" >/dev/null && ok "$s" || bad "$s.sty"
done

echo "Babel languages"
for l in english italian french ukrainian; do
  kpsewhich "babel-$l.tex" >/dev/null && ok "$l" || bad "babel-$l.tex"
done

echo "Fonts"
[ -n "$(fc-list FreeSerif)" ] && ok "FreeSerif (body, via fontconfig)" || bad "FreeSerif (fonts-freefont-otf)"
for f in CinzelDecorative-Bold.ttf IMFeENsc28P.otf IMFeENrm28P.otf; do
  kpsewhich "$f" >/dev/null && ok "$f (cover)" || bad "$f (cover; texlive-fonts-extra)"
done

echo "Assets"
for a in $(grep -hoE 'assets/[A-Za-z0-9._-]+' ./*.tex ./*.sty | sort -u); do
  [ -f "$a" ] && ok "$a" || bad "$a"
done

ver=$(xelatex --version 2>/dev/null | grep -oE 'TeX Live [0-9]+' | head -1)
echo "TeX distribution: ${ver:-unknown}"
case "$ver" in
  *2024) ;;
  *) warn "the released PDFs were produced with TeX Live 2024; other versions build fine"
     warn "but reflow text, so 'make check' will report differences. Use 'make docker' to reproduce them." ;;
esac
[ "$missing" -eq 0 ] && echo "All build dependencies present." || { echo "Some dependencies are missing."; exit 1; }
