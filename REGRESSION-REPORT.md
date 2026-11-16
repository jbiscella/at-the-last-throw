# Ukrainian justification fix — regression report

## Cause and patch

The Ukrainian language was selected before `\begin{document}`. The active language reverted to English at document start, preventing effective Ukrainian word hyphenation and stretching interword spaces.

The Ukrainian source now selects `ukrainian` immediately after `\begin{document}`, enables `\frenchspacing`, and uses `\emergencystretch=1em`, `\tolerance=1000` rather than the previous more permissive settings. No other language source or theme file was modified.

## Validation

All four editions were compiled twice with XeLaTeX.

| Edition | PDF pages | Changed rendered pages relative to preceding baseline | Overfull hbox | Underfull hbox |
|---|---:|---:|---:|---:|
| English | 16 | 0 of 16 | 0 | 0 |
| Italian | 16 | 0 of 16 | 0 | 0 |
| French | 16 | 0 of 16 | 0 | 0 |
| Ukrainian | 16 | 15 of 16 (intentional reflow) | 0 | 0 |

Raster comparisons were conducted on each page at 72 dpi using identical rendering settings. The front cover is unchanged in Ukrainian.

For Ukrainian body pages, measured extracted-space widths greater than 6 pt fell from 23 to 0; the 95th percentile fell from 4.71 pt to 3.44 pt, and maximum from 7.56 pt to 4.98 pt. These are PDF glyph-space measurements, not perceptual typography scores. Chapters remain present; first printed chapter retains page label 1.

A targeted visual inspection was performed on the previously affected creation chapter page and the final narrator page. A full native-language proofread is not included.
