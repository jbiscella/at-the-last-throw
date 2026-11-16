# French editorial fixes — 2026-11-14

Source: the French editorial audit; changes are scoped to `manual-fr.tex` and the French-only `\RPGBackCoverFrench` branch in `rpgcover.sty`.

## Corrected
- Page-break control before **Le Critique**, **Compétences de Savoir**, and **Objets remarquables**.
- Kept the short list after “Au-delà des améliorations mécaniques…” together with its introductory text.
- Kept **Classes**' opening with sufficient content instead of stranding one class after its table.
- Increased the table of contents entries to approximately 10 pt and strengthened its title and credits.
- Improved French-only typographic flow via slight reduction of extra paragraph spacing and line spreading, without changing font size of body text.
- Enlarged and explicitly word-spaced the one-line French back-cover heading.

## Editorial trade-offs
- Page 7 has generous whitespace following Kael rather than moving the next chapter title away from its table.
- Page 3 remains airy after the target-number section because the Critique discussion is kept together on the following page.
- No new illustrations or changes to the rules were made.

## Tests
- French: 16 A4 pages, two XeLaTeX passes, no overfull boxes or compiler errors.
- English and Italian: rebuilt twice from the same project, all 16 pages in each edition match their respective pre-change reference PDF pixel for pixel at 72 dpi.
- Audit was of layout/typesetting; it does not certify French linguistic proofreading.
