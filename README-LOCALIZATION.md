# At the Last Throw — English / Italian LaTeX editions

## Builds

The two editions deliberately use the same `rpgmanual.sty`, `rpgcover.sty`, `illustrated-panel.sty`, and shared interior artwork:

- English: `xelatex -halt-on-error manual.tex` (run twice for the contents page).
- Italian: `xelatex -halt-on-error -jobname=manual-it manual-it.tex` (run twice for the contents page).

Requirements: XeLaTeX with the same packages and fonts required by the original v5 theme, plus `pdfpages` and `tocloft` for the Italian edition; `PyMuPDF` for the optional automated regression check.

## Localisation boundaries

- `manual.tex`: frozen original English v5 source, **unchanged**.
- `manual-it.tex`: Italian rules from the supplied Italian PDF; shared component macros.
- `rpgmanual.sty`, `rpgcover.sty`, `illustrated-panel.sty`: same files for both editions.
- `assets/cover-front-it.png`, `assets/cover-back-it.png`: supplied Italian covers unchanged.
- `assets/cover-front-it.pdf`, `assets/cover-back-it.pdf`: lossless PDF wrappers required by `pdfpages` to position those raster covers exactly on A4.
- The seven illustrated internal panels reuse the shared engraved assets.

The Italian table of contents and attribution text are localized independently. Italian-specific type spacing uses 1.06 line spread and 3pt paragraph spacing, versus the unchanged English baseline. This allows the Italian content to reflow without introducing English regressions.

**Editorial limitation:** the Italian covers contain text baked into the provided images; editing that text requires replacing the PNGs or creating editable LaTeX text overlays. The interior and contents are editable LaTeX.

## Tested output

- English: 16 pages. Every rendered page of the rebuilt English edition was compared at 72 dpi against the original published `at-the-last-throw-editorial-v5.pdf`: **zero differing pixels on all 16 pages**.
- Italian: 16 pages, 13 chapters, 12 tables, 7 engraved illustrated panels, Italian cover and back cover. Both covers occupy exactly one page.
- The Italian LaTeX build completed with no overfull/underfull boxes and no errors.
- Source-to-output Italian lexical comparison (normalizing accent composition, case and punctuation) found >99% word-token overlap; the few n-gram differences mostly arise from automatic hyphenation or content ordering in multi-column tables.

This checks visual regression and typesetting, **not a line-by-line editorial proof** of the Italian rules. The exported 16-page contact sheet (`italian-contact-final.png`) is included for inspection.

## Repeatable QA

Run `python verify_layout.py` after compiling both editions. The script compares the English rebuild to the frozen v5 baseline and checks the Italian PDF's page count and required chapter headings. It deliberately keeps page counts editable only as a documented expected result, not a requirement that future translations match English pagination.


## Cover correction (2026-11-14)

The Italian edition uses `\RPGFrontCover` with the same editable cartouche/
transparent illustration as English, and `\RPGBackCoverItalian` with the same
engraved background, typography and barcode panel as the English back cover.
The supplied Italian original PNGs remain in assets for historical reference only.
The English source and PDF remain unchanged from the v5 baseline.

Validated: English 16/16 pages visually identical at 72 dpi, Italian interior
pages 2–15 unchanged from the first localized build, and XeLaTeX reports no
overfull boxes for the corrected Italian build.
