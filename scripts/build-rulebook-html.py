#!/usr/bin/env python3
"""Regenerate the text of the rulebook's web chapters from the LaTeX sources.

manual.tex (English) and manual-<lang>.tex are the single authoritative source of the rules. The web
chapters docs/_chapters/<lang>-read-NN.html carry their own page furniture (front matter, sidebar,
chapter label, previous/next links); this script rewrites only the chapter's title and its text,
<h1>…</h1> and <div class="prose">…</div>, so the web rules say what the PDFs say. Do not edit
the chapter text in those files by hand: edit the .tex and rerun this script.

It reuses the converter of scripts/build-adventure-html.py (pandoc for the running text) and
renders the rulebook's own blocks in the markup the chapters already use: \\section* as
<h3 id="section-N">, rpgtable as a scrolling table with column headers, and \\RPGEngravedPanel as
an engraved panel with its image. Requires pandoc and Pillow, like the adventure's generator.
"""
import argparse
import html
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("adventure_html", ROOT / "scripts" / "build-adventure-html.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

LANGUAGES = A.LANGUAGES
CHAPTERS = 13


def source(lang):
    return ROOT / ("manual.tex" if lang == "en" else f"manual-{lang}.tex")


class RulebookConverter(A.Converter):
    def __init__(self, lang):
        super().__init__(lang, {})
        self.section = 0

    def table(self, body):
        body = re.sub(r"\\hline", "", body)
        rows = [r.strip() for r in re.split(r"\\\\", body) if r.strip()]
        head, rows_html = None, []
        for r in rows:
            cells = [c.strip() for c in re.split(r"(?<!\\)&", r)]
            if all(c.startswith("\\rpghead") for c in cells):
                head = [self.inline(re.sub(r"^\\rpghead\{(.*)\}$", r"\1", c, flags=re.S)) for c in cells]
            else:
                rows_html.append("<tr>" + "".join(f"<td>{self.inline(c)}</td>" for c in cells) + "</tr>")
        thead = ("<thead><tr>" + "".join(f'<th scope="col"><strong>{c}</strong></th>' for c in head) + "</tr></thead>") if head else ""
        return self.block(f'<div class="table-scroll"><table>{thead}<tbody>{"".join(rows_html)}</tbody></table></div>')

    def sections(self, s):
        def heading(title):
            self.section += 1
            return self.block(f'<h3 id="section-{self.section}">{self.inline(title)}</h3>')
        return A.replace_macro(s, r"section\*", 1, heading)

    def panels(self, s):
        def panel(title, image, text):
            name = Path(image).name
            paras = [p for p in re.split(r"\\par(?![a-zA-Z])\s*(?:\\(?:small|med|big)skip)?|\n\s*\n", text) if p.strip()]
            body = "".join(f"<p>{self.inline(p)}</p>" for p in paras)
            return self.block(f'<aside class="engraved-panel"><img src="../../assets/{name}" alt="" loading="lazy">'
                              f'<div class="panel-copy"><h4>{self.inline(title)}</h4>{body}</div></aside>')
        return A.replace_macro(s, "RPGEngravedPanel", 3, panel)

    def notes(self, s):
        # The web chapters show the rpgnote boxes as ordinary paragraphs.
        return re.sub(r"\\begin\{rpgnote\}(\[[^\]]*\])?|\\end\{rpgnote\}", "\n\n", s)

    def convert(self, tex):
        return super().convert(self.panels(self.sections(tex)))


def symbols(s):
    # Paragraph breaks first: clean() drops \smallskip with its space, which would glue a following
    # word to \par.
    s = re.sub(r"\\par\\(?:small|med|big)skip\s*", "\n\n", s)
    s = re.sub(r"\\par(?![a-zA-Z])\s*", "\n\n", s)
    # Comparison signs written as maths ("$\geq 4$", "$\leq 2$") become plain text, so pandoc adds no
    # three-per-em spaces around them.
    s = re.sub(r"\$\\([lg]eq)\s*([^$]*)\$", lambda m: ("≤" if m.group(1) == "leq" else "≥") + " " + m.group(2).strip(), s)
    # "$\sim$" is the "about" sign before a percentage: \textasciitilde, not "~", which LaTeX and pandoc
    # read as a no-break space.
    for a, b in (("$\\uparrow$", "↑"), ("$\\downarrow$", "↓"), ("$\\sim$", "\\textasciitilde{}"),
                 ("\\textquoteright{}", "’"), ("\\textquoteright", "’")):
        s = s.replace(a, b)
    return s


def chapters(tex):
    body = tex.split("\\RPGStartMainMatter", 1)[1]
    body = re.split(r"\\RPGBackCover\w*", body, maxsplit=1)[0]
    starts = list(re.finditer(r"\\RPGChapter\{", body))
    if len(starts) != CHAPTERS:
        raise SystemExit(f"expected {CHAPTERS} \\RPGChapter, found {len(starts)}")
    out = []
    for k, m in enumerate(starts):
        (title,), j = A.take_args(body, m.end() - 1, 1)
        end = starts[k + 1].start() if k + 1 < len(starts) else len(body)
        out.append((title, body[j:end]))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("langs", nargs="*", default=list(LANGUAGES))
    a = ap.parse_args()
    for lang in a.langs:
        tex = symbols(source(lang).read_text(encoding="utf-8"))
        for n, (title, chunk) in enumerate(chapters(tex), start=1):
            conv = RulebookConverter(lang)
            prose = conv.convert(A.clean(chunk)).strip()
            # Tight lists, as the chapters had them: pandoc wraps each item of a loose list in <p>.
            prose = re.sub(r"<li>\s*<p>(.*?)</p>\s*</li>", r"<li>\1</li>", prose, flags=re.S)
            # Bare {…} groups in the LaTeX become attribute-less spans: they carry nothing.
            while re.search(r"<span>([^<]*)</span>", prose):
                prose = re.sub(r"<span>([^<]*)</span>", r"\1", prose)
            text = re.sub(r"<[^>]+>", "", prose)
            leftover = re.findall(r"\\[A-Za-z]+|HHBLOCK\d+X", text)
            if leftover:
                sys.exit(f"{lang} chapter {n}: unconverted LaTeX {sorted(set(leftover))}")
            page = ROOT / "docs" / "_chapters" / f"{lang}-read-{n:02d}.html"
            s = page.read_text(encoding="utf-8")
            start = s.index('<div class="prose">') + len('<div class="prose">')
            end = s.index('</div><nav class="chapter-nav"', start)
            s = s[:start] + prose.replace("\n", "") + s[end:]
            h1 = conv.inline(A.clean(title))
            s = re.sub(r"<h1>.*?</h1>", lambda m: f"<h1>{h1}</h1>", s, count=1)
            page.write_text(s, encoding="utf-8")
        print(f"{lang}: {CHAPTERS} chapters")


if __name__ == "__main__":
    main()
