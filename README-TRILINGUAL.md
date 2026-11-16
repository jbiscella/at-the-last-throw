# At the Last Throw — trilingual LaTeX edition

Build with XeLaTeX **twice per edition** (TikZ uses remembered page positions for cover overlays):

- `xelatex -interaction=nonstopmode -halt-on-error manual.tex` (twice) — English
- `xelatex -interaction=nonstopmode -halt-on-error manual-it.tex` (twice) — Italian
- `xelatex -interaction=nonstopmode -halt-on-error manual-fr.tex` (twice) — French

The English and Italian source files and shared artwork are unchanged from the pinned bilingual editorial v2. French-only material is in `manual-fr.tex`, plus a French back-cover macro in `rpgcover.sty`. The English and Italian rebuilt PDFs are pixel-identical to their pinned baselines.

## Quality assurance

`python verify_trilingual.py` compares all 16 pages for English and Italian raster regressions, counts French chapters, tables, panels, validates A4 page count, and compares the full Italian body word sequence against the original Italian source PDF.

Italian textual check: 4,007 source tokens, 3,996 initially matched; eight compound words were split in PDF extraction (e.g. `peggiorano` → `peggio rano`) and one repeated `Famiglia / Caratteristica / Esempi` heading was removed when the race table was consolidated. After accounting for these formatting-only differences, no content-token discrepancy remains. Punctuation and typographical equivalence are not verified word-for-word.

## French layout review

16 A4 pages; 13 chapters; 12 tables; seven illustrated panels. All pages rasterized and visually reviewed, including covers. There remains purposeful white space at the end of page 7 to avoid splitting the introduction and table of the following chapter. No LaTeX overfull boxes observed. The French edition is a translation draft and should receive native-speaker linguistic proofreading before publication.
