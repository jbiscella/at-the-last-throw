#!/usr/bin/env python3
"""Generate the web edition of the prologue "The Path of Debts" from its LaTeX sources.

adventure/path-of-debts-<lang>.tex is the single authoritative source. This script writes
docs/<lang>/adventures/the-bell-of-hollow-hearth/prologue.html, one page per language: the
prologue belongs to that adventure. The generated pages must not be edited by hand.

It reuses the converter of scripts/build-adventure-html.py (pandoc for the running text, the
rpgnote stat boxes) and adds what only the prologue has: the "At the table" boxes (rpgexample)
and the dice icons, drawn as inline SVG with labels for screen readers. Requires pandoc and
Pillow, like the adventure's generator.
"""
import argparse
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("adventure_html", ROOT / "scripts" / "build-adventure-html.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

LANGUAGES = A.LANGUAGES
SOURCE_SLUG = "path-of-debts"
ADVENTURE = "the-bell-of-hollow-hearth"

# Pip centres of a d6 face, as in the LaTeX \DadoPips (unit square, y upwards).
PIPS = {
    1: [(.5, .5)],
    2: [(.27, .73), (.73, .27)],
    3: [(.25, .75), (.5, .5), (.75, .25)],
    4: [(.27, .27), (.27, .73), (.73, .27), (.73, .73)],
    5: [(.25, .25), (.25, .75), (.75, .25), (.75, .75), (.5, .5)],
    6: [(.28, .22), (.28, .5), (.28, .78), (.72, .22), (.72, .5), (.72, .78)],
}


def die_svg(n, kept, label):
    pips = "".join(f'<circle cx="{x * 10:g}" cy="{(1 - y) * 10:g}" r="0.95"/>' for x, y in PIPS[n])
    cls = "pd-die" if kept else "pd-die pd-dropped"
    return (f'<svg class="{cls}" viewBox="0 0 10 10" role="img" aria-label="{html.escape(label, quote=True)}">'
            f'<rect x="0.5" y="0.5" width="9" height="9" rx="1.6"/>{pips}</svg>')


TARGET_SVG = ('<svg class="pd-icon pd-target" viewBox="0 0 10 10" aria-hidden="true">'
              '<circle cx="5" cy="5" r="4.4"/><circle cx="5" cy="5" r="2.4"/><circle class="pd-fill" cx="5" cy="5" r="0.8"/></svg>')


def mark_svg(success, label):
    shape = ('<polyline points="0.8,6.5 3.8,9.5 9.2,2.5"/>' if success
             else '<line x1="1.5" y1="9.5" x2="8.5" y2="2.5"/><line x1="1.5" y1="2.5" x2="8.5" y2="9.5"/>')
    cls = "pd-success" if success else "pd-failure"
    return (f'<svg class="pd-icon pd-mark {cls}" viewBox="0 0 10 10" role="img" '
            f'aria-label="{html.escape(label, quote=True)}">{shape}</svg>')


class PrologueConverter(A.Converter):
    def __init__(self, lang, ui):
        super().__init__(lang, ui)
        self.icons = []

    def icon(self, svg):
        self.icons.append(svg)
        return f"PDICON{len(self.icons) - 1}X"

    def dice(self, s):
        labels = self.ui["prologue_icons"]
        s = re.sub(r"\\Dado(\*?)\{([1-6])\}", lambda m: self.icon(die_svg(
            int(m.group(2)), not m.group(1),
            (labels["dropped"] if m.group(1) else labels["kept"]).format(n=m.group(2)))), s)
        s = re.sub(r"\\Bersaglio(?![A-Za-z])", lambda m: self.icon(TARGET_SVG), s)
        s = re.sub(r"\\Riuscita(?![A-Za-z])", lambda m: self.icon(mark_svg(True, labels["success"])), s)
        s = re.sub(r"\\Fallita(?![A-Za-z])", lambda m: self.icon(mark_svg(False, labels["failure"])), s)
        s = re.sub(r"\\Su(?![A-Za-z])", "↑", s)
        s = re.sub(r"\\Giu(?![A-Za-z])", "↓", s)
        return s

    def examples(self, s):
        pat = re.compile(r"\\begin\{rpgexample\}")
        while True:
            m = pat.search(s)
            if not m:
                return s
            (title,), j = A.take_args(s, m.end(), 1)
            end = s.index("\\end{rpgexample}", j)
            paras = [p for p in re.split(r"\n\s*\n", s[j:end]) if p.strip()]
            body = "".join(f"<p>{self.inline(p)}</p>" for p in paras)
            box = (f'<aside class="pd-table"><h3 class="pd-table-title">{self.inline(title)}</h3>{body}</aside>')
            s = s[:m.start()] + self.block(box) + s[end + len("\\end{rpgexample}"):]

    def convert(self, tex):
        out = super().convert(self.examples(self.dice(tex)))
        for n, svg in enumerate(self.icons):
            out = out.replace(f"PDICON{n}X", svg)
        return out


def chapters(tex):
    body = tex.split("\\RPGStartMainMatter", 1)[1].split("\\SentieroBackCover", 1)[0]
    starts = list(re.finditer(r"\\RPGChapter\{", body))
    if len(starts) != 12:
        raise SystemExit(f"expected 12 \\RPGChapter, found {len(starts)}")
    out = []
    for k, m in enumerate(starts):
        (title,), j = A.take_args(body, m.end() - 1, 1)
        end = starts[k + 1].start() if k + 1 < len(starts) else len(body)
        out.append((title, body[j:end]))
    return out


def running_title(tex):
    m = re.search(r"\\RPGSetRunningTitle\{([^{}]*)\}", tex)
    if not m:
        raise SystemExit("no \\RPGSetRunningTitle")
    return m.group(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, default=ROOT / "adventure")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs")
    ap.add_argument("langs", nargs="*", default=list(LANGUAGES))
    a = ap.parse_args()
    data = json.loads((ROOT / "docs/_data/hollow_hearth.json").read_text(encoding="utf-8"))
    for lang in a.langs:
        tex = (a.source_dir / f"{SOURCE_SLUG}-{lang}.tex").read_text(encoding="utf-8")
        title = running_title(tex)
        parts, toc = [], []
        for k, (ch_title, chunk) in enumerate(chapters(tex), start=1):
            conv = PrologueConverter(lang, data[lang])
            heading = conv.inline(A.clean(ch_title))
            body = conv.convert(A.clean(chunk))
            leftover = re.findall(r"\\[A-Za-z]+|HHBLOCK\d+X|PDICON\d+X", re.sub(r"<[^>]+>", "", body))
            if leftover:
                sys.exit(f"{lang} chapter {k}: unconverted LaTeX {sorted(set(leftover))}")
            parts.append(f'<section class="pd-chapter" id="ch-{k}">\n<h2>{heading}</h2>\n{body}</section>\n')
            toc.append({"id": f"ch-{k}", "title": html.unescape(re.sub(r"<[^>]+>", "", heading))})
        front = ["---", 'layout: "hollow_hearth"', f'lang: "{lang}"', 'kind: "adventure_prologue"',
                 f"title: {json.dumps(title, ensure_ascii=False)}", f"chapter_title: {json.dumps(title, ensure_ascii=False)}",
                 f'permalink: "/{lang}/adventures/{ADVENTURE}/prologue.html"',
                 f"chapters: {json.dumps(toc, ensure_ascii=False)}",
                 f'generated_from: "adventure/{SOURCE_SLUG}-{lang}.tex"', "---"]
        out = a.out_dir / lang / "adventures" / ADVENTURE / "prologue.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(front) + "\n" + A.tidy("".join(parts)), encoding="utf-8")
        print(f"{lang}: {out.relative_to(a.out_dir)} ({len(toc)} chapters)")


if __name__ == "__main__":
    main()
