# License

This repository is dual-licensed by file type.

| What | Files | License |
|---|---|---|
| **Content**: rules text, translations, artwork, built PDFs | `manual*.tex`, `assets/`, release PDFs | [CC BY-SA 4.0](LICENSES/CC-BY-SA-4.0.txt) |
| **Code**: the publishing system and tooling | `*.sty`, `Makefile`, `Dockerfile`, `scripts/`, `.github/` | [0BSD](LICENSES/0BSD.txt) |

Documentation (`*.md`) is CC BY-SA 4.0.

## Using the content

Anyone may share, adapt and sell the content, including printed books and PDFs, provided they:

- credit it as follows and indicate whether they made changes:

  > *At the Last Throw* by Jacopo Biscella, licensed under CC BY-SA 4.0
  > (https://creativecommons.org/licenses/by-sa/4.0/). Source: https://github.com/jbiscella/at-the-last-throw

- release adaptations (translations, expansions, modified rules or art) under CC BY-SA 4.0 or a
  [compatible license](https://creativecommons.org/compatiblelicenses).

The code has no conditions and needs no attribution.

## Fonts

The built PDFs embed the fonts below. All of them permit commercial use and embedding in PDFs,
so the books can be sold in print or as PDFs without buying font licenses.

| Font | Used for | License |
|---|---|---|
| FreeSerif (GNU FreeFont) | body text, Cyrillic | GPL-3.0-or-later with the FreeFont font exception |
| Cinzel Decorative Bold | cover titles | SIL Open Font License 1.1 |
| IM Fell English Roman and SC | cover subtitles and text | SIL Open Font License 1.1 |
| Computer Modern (AMS Type 1) | arrow and math symbols | SIL Open Font License 1.1 |

Under the FreeFont font exception, embedding FreeSerif in a document does not make the document GPL-licensed.
The fonts' licenses therefore do not affect the CC BY-SA 4.0 license of the content.

No font files are stored in this repository. The fonts are installed from TeX Live and Debian at build time, and
distributing the compiled PDFs requires no separate font license files. If font files are ever added to the
repository, add their license texts to `LICENSES/` and keep their copyright notices unmodified.
