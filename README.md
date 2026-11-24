# At the Last Throw

A tabletop RPG rulebook in six languages, typeset with XeLaTeX in an engraved, historical-manual style.

| Edition | Source | Title |
|---|---|---|
| English | `manual.tex` | At the Last Throw |
| Italian | `manual-it.tex` | All'ultimo tiro |
| French | `manual-fr.tex` | Au dernier lancer |
| Ukrainian | `manual-uk.tex` | Останній кидок |
| German | `manual-de.tex` | Der letzte Wurf |
| Spanish | `manual-es.tex` | La última tirada |

**Download the PDFs** from [Releases](https://github.com/jbiscella/at-the-last-throw/releases).
Each edition is 16 A4 pages. The French and Ukrainian editions are translation drafts that have not yet had a native-speaker proofread.

## Quick start

All you need is Docker and GNU Make.

```sh
make docker       # build the pinned TeX Live 2024 image, then all four editions into build/
make baselines    # download the latest release PDFs into baseline/ (needs the gh CLI)
make docker-check # pixel-compare build/ against baseline/
```

The first `make docker` takes about two minutes and creates a local image of about 2.5 GB.
Nothing is pushed to a registry.

## Requirements and tested versions

### Reference environment (Docker, recommended)

This environment reproduces the released PDFs **pixel-for-pixel**: all 4 editions × 16 pages were
identical at 72 dpi when last verified on 2026-11-16. It is defined in the [`Dockerfile`](Dockerfile).

| Component | Version |
|---|---|
| Base image | Debian 13.7 "trixie" (`debian:trixie-slim`, pinned by digest) |
| TeX Live (Debian packages) | 2024.20250309 (`texlive-binaries` 2024.20240313.70630+ds-6) |
| XeTeX | 3.141592653-2.6-0.999996 |
| xdvipdfmx | 20240305 |
| LaTeX kernel / L3 layer | 2024-11-01 PL2 / 2025-01-18 |
| FreeSerif (`fonts-freefont-otf` **and** `fonts-freefont-ttf`) | 20211204+svn4273-2 |
| Cinzel Decorative, IM Fell English | from `texlive-fonts-extra` 2024.20250309-2 |
| GNU Make | 4.4.1 |
| poppler-utils (`pdfinfo`, `pdftoppm`) | 25.03.0 |
| ImageMagick (`compare`) | 7.1.1-43 |
| Host: Docker Engine | tested with 29.5.0; any recent version should work |

LaTeX packages as loaded in the reference build:

| Package | Version | | Package | Version |
|---|---|---|---|---|
| fontspec | 2024/05/11 v2.9e | | tabularx | 2023/12/11 v2.12a |
| babel | 2025/02/14 v25.4 | | array | 2024/10/17 v2.6g |
| microtype | 2025/02/11 v3.2a | | colortbl | 2024/07/06 v1.0i |
| geometry | 2020/01/02 v5.9 | | needspace | 2010/09/12 v1.3d |
| tikz / pgf | 2023-01-15 (3.1.10) | | enumitem | 2025/02/06 v3.11 |
| tcolorbox | 2024/10/22 | | hyperref | 2024-11-05 |
| titlesec | 2025/01/04 v2.17 | | graphicx | 2021/09/16 v1.2d |
| fancyhdr | 2025/02/07 v5.2 | | tocloft | 2017/08/31 v2.3i |
| xcolor | 2024/09/29 v3.02 | | xparse | 2024-08-16 |
| etoolbox | 2025/02/11 v2.5l | | | |

Babel languages: english, italian, french, ukrainian.

### Local toolchain (without Docker)

```sh
make deps   # checks programs, packages, babel languages, fonts and assets
make        # all editions;  or: make en | it | fr | uk
```

| Component | Tested version | Result |
|---|---|---|
| Debian 12.13 "bookworm", `texlive-full` 2022.20230122-3 | XeTeX 0.999994, xdvipdfmx 20211117 | All editions build with no errors and no overfull boxes, but **line breaks differ** from the releases: 14 of 16 pages per edition change, and the Ukrainian edition runs to 17 pages. |

Minimum Debian/Ubuntu packages: `texlive-xetex texlive-latex-recommended texlive-latex-extra
texlive-fonts-recommended texlive-fonts-extra texlive-pictures texlive-lang-english
texlive-lang-italian texlive-lang-french texlive-lang-cyrillic fonts-freefont-otf fonts-freefont-ttf make`.
`make check` also needs `poppler-utils` and `imagemagick`.

Use the Docker build for anything that has to match the released PDFs. Any TeX Live other than 2024, or a
different set of FreeSerif files, changes the layout. Both FreeSerif packages are required: XeTeX resolves the
family through fontconfig and the releases use the OTF regular and italic with the TTF bold and bold italic.

## Make targets

| Target | Effect |
|---|---|
| `make docker` | Build the image (if needed) and all editions into `build/`. |
| `make` / `make en` `it` `fr` `uk` | Build with the local TeX installation. |
| `make baselines` | Download the latest release PDFs into `baseline/`. `BASELINE_TAG=v0.1.0` selects a release. |
| `make check` / `make docker-check` | Compare `build/` with `baseline/` at 72 dpi; non-zero exit if any page differs. Never rebuilds. `DIFF_DIR=build/diff` writes images with the changes highlighted in red. |
| `make update-baselines` | Copy `build/*.pdf` into `baseline/` (local only). |
| `make docker-shell` | Open a shell inside the build environment. |
| `make clean` | Remove `build/`. |
| `make docker-adventure` | In the pinned container: the adventure's print JPEGs from its PNG originals, then its six PDFs into `docs/downloads/` (`SLUG=hollow-hearth`). |
| `make docker-sheets` | In the pinned container: the blank and pregenerated character sheets in `character-sheets/`, with their typesetting and collision checks. |
| `make site` | Build the website from `docs/` in the official `ruby:3.3` image with the GitHub Pages gems, into `build/site/`, then check every page and local link. |
| `make site-serve` | Serve the website with live reload at http://localhost:4000/ (from a Chromebook's Linux container: http://penguin.linux.test:4000/). |
| `make page-counts` | Compare the page count of every PDF in `docs/downloads/`, in every language, with `REF` (default `origin/main`); non-zero exit if any changed. |

Each edition is compiled twice: the TikZ cover overlays use remembered page positions and the
contents page needs a second pass.

## Workflow on GitHub

- **Pull requests:** CI builds both the PR and its base branch in the reference environment and compares them
  page by page. The check fails if any page changes. The job summary lists the changed pages, and the
  `diff-images` artifact shows them highlighted. If the change is intended, add the label
  `expected-layout-change` and the check no longer blocks. The built PDFs are in the `pdfs` artifact.
- **Releases:** push a tag such as `v0.2.0`. CI builds the four editions and publishes them as a GitHub
  Release, which becomes the new baseline for `make baselines`.

## Repository layout

```
manual*.tex                 one source per edition
rpgmanual.sty               page layout, typography, chapters, tables
rpgcover.sty                front and back covers
illustrated-panel.sty       engraved illustration panels
assets/                     artwork (PNG)
Dockerfile, Makefile        build environment and targets
scripts/                    compare-pdf.sh, check-deps.sh
.github/workflows/          CI and releases
```

Editorial and QA history up to the first release: [README-LOCALIZATION.md](README-LOCALIZATION.md),
[README-TRILINGUAL.md](README-TRILINGUAL.md), [EDITORIAL-CHANGES.md](EDITORIAL-CHANGES.md),
[FRENCH-EDITORIAL-CHANGES.md](FRENCH-EDITORIAL-CHANGES.md), [STRUCTURE-REVIEW.md](STRUCTURE-REVIEW.md),
[REGRESSION-REPORT.md](REGRESSION-REPORT.md). Those documents mention `verify_trilingual.py` and
`verify_layout.py`, which are not part of this repository. `make check` replaces their raster comparison,
but not their chapter, table and word counts.

## License

Content (rules text, translations, artwork, PDFs) is licensed under [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt).
Adaptations, including new translations, must use the same license.
Code (`.sty` files, build tooling, CI) is licensed under [0BSD](LICENSES/0BSD.txt).
The embedded fonts (FreeSerif, Cinzel Decorative, IM Fell English, Computer Modern) all allow commercial use and
PDF embedding. See [LICENSE.md](LICENSE.md) for details.
