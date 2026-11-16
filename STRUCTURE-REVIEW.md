# Four-language structure verification

## Change

Ukrainian source had collapsed distinct prose items into a single paragraph because LaTeX treats ordinary source line breaks as spaces. The Ukrainian narrator guidance (chapter XIII), skill entries, grimoire properties, enemy definitions and other independent prose statements now have explicit paragraph breaks. Chapter XIII uses a locally adjusted inter-paragraph gap; it is still adjacent to chapter XII to avoid a mostly empty new page.

No game rules, artwork, covers or shared theme settings were changed.

## Automated and rendered checks

| Edition | Physical pages | Chapters | Data tables | Illustrated panels | Overfull warnings | Raster difference versus preceding edition |
|---|---:|---:|---:|---:|---:|---|
| English | 16 | 13 | 12 | 7 | 0 | None (16/16 identical) |
| Italian | 16 | 13 | 12 | 7 | 0 | None (16/16 identical) |
| French | 16 | 13 | 12 | 7 | 0 | None (16/16 identical) |
| Ukrainian | 16 | 13 | 12 | 7 | 0 | Interior reflow, as expected |

All Roman-numbered chapter headings are present on rendered pages, and none is within 105 pt of the bottom trim edge. All copies preserve the numbering system: front cover unnumbered, contents unnumbered in print, first rules chapter printed as page 1, back cover unnumbered.

Ukrainian page 15 (PDF physical page) was visually checked at full resolution: chapter XII and XIII stay together without clipping; chapter XIII has eight separate guidance paragraphs. A standalone page for XIII was rejected because it created an overwhelmingly empty page and grew the PDF to 17 pages.

The normalized Ukrainian PDF token count is unchanged (3,417 tokens in both PDFs); residual ordering differences in PDF text extraction are caused by reflow and running headers, not prose edits.

### Limits

This is a semantic/layout structure review and raster regression check, not native-language linguistic editing or validation of translation correctness. Some independent page compositions, particularly chapters starting later in a page, remain editorial choices rather than technical failures.
