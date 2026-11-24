#!/usr/bin/env python3
"""Generate the web edition of the prologue "The Path of Debts" from its LaTeX sources.

adventure/path-of-debts-<lang>.tex is the single authoritative source. This script writes
docs/<lang>/adventures/the-bell-of-hollow-hearth/prologue/01-04.html: the prologue belongs to that
adventure and reads like its sections. 01-03 are the story (chapters I-IV, V-VIII, IX-XI), 04 is
"For the Narrator", which reveals the adventure's secrets. The generated pages must not be edited
by hand.

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
# Pages of the web edition: the story in three parts, then the Narrator's chapter on its own page.
PARTS = ((1, 2, 3, 4), (5, 6, 7, 8), (9, 10, 11), (12,))
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
        # The arrows say "keep the highest / lowest"; screen readers get the words, except where the
        # text already spells them out in brackets (the legend).
        s = re.sub(r"\\Su(?![A-Za-z])(?=(\\ )?\s*\()", "↑", s)
        s = re.sub(r"\\Giu(?![A-Za-z])(?=(\\ )?\s*\()", "↓", s)
        s = re.sub(r"\\Su(?![A-Za-z])", lambda m: self.icon(self.arrow("↑", labels["keep_high"])), s)
        s = re.sub(r"\\Giu(?![A-Za-z])", lambda m: self.icon(self.arrow("↓", labels["keep_low"])), s)
        return s

    @staticmethod
    def arrow(glyph, words):
        return f'<span aria-hidden="true">{glyph}</span><span class="visually-hidden"> ({html.escape(words)})</span>'

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


def hook(lang):
    """Title and anchor of the adventure's hook section, where its read-aloud arrival is."""
    tex = (ROOT / "adventure" / f"hollow-hearth-{lang}.tex").read_text(encoding="utf-8")
    titles = re.findall(r"\\subsection\{([^{}]*)\}\\label\{([^{}]*)\}", tex)
    if len(titles) < 4:
        raise SystemExit(f"{lang}: hook section not found in the adventure")
    return titles[3]


def url(lang, path):
    return "{{ '/' | relative_url }}" + f"{lang}/adventures/{ADVENTURE}/{path}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, default=ROOT / "adventure")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs")
    ap.add_argument("langs", nargs="*", default=list(LANGUAGES))
    a = ap.parse_args()
    data = json.loads((ROOT / "docs/_data/hollow_hearth.json").read_text(encoding="utf-8"))
    for lang in a.langs:
        ui = data[lang]
        tex = (a.source_dir / f"{SOURCE_SLUG}-{lang}.tex").read_text(encoding="utf-8")
        title = running_title(tex)
        hook_title, hook_id = hook(lang)
        chapters_html, titles = {}, {}
        for k, (ch_title, chunk) in enumerate(chapters(tex), start=1):
            conv = PrologueConverter(lang, ui)
            heading = conv.inline(A.clean(ch_title))
            body = conv.convert(A.clean(chunk))
            leftover = re.findall(r"\\[A-Za-z]+|HHBLOCK\d+X|PDICON\d+X", re.sub(r"<[^>]+>", "", body))
            if leftover:
                sys.exit(f"{lang} chapter {k}: unconverted LaTeX {sorted(set(leftover))}")
            if k == 11:  # the closing note sends the Narrator to the adventure's hook: link it
                name = conv.inline(A.clean(hook_title))
                if body.count(name) != 1:
                    sys.exit(f"{lang}: the hook '{hook_title}' is not named once in chapter 11")
                body = body.replace(name, f'<a href="{url(lang, "read/01.html")}#{hook_id}">{name}</a>')
            chapters_html[k], titles[k] = (heading, body), html.unescape(re.sub(r"<[^>]+>", "", heading))
        c = ui["catalog"]
        labels = [f'{c["prologue_part"]} {n}' for n in (1, 2, 3)] + [titles[12]]
        parts = [{"key": f"{n:02d}", "label": labels[n - 1], "first": titles[PARTS[n - 1][0]]} for n in range(1, 5)]
        for n, members in enumerate(PARTS, start=1):
            narrator = n == 4
            html_parts = []
            for k in members:
                heading, body = chapters_html[k]
                h2 = "" if narrator else f"<h2>{heading}</h2>\n"
                html_parts.append(f'<section class="pd-chapter" id="ch-{k}">\n{h2}{body}</section>\n')
            kicker = c["narrator_only"] if narrator else f'{c["prologue_part"]} {n} {c["prologue_of"]} 3'
            prev = ({"url": f"/{lang}/adventures/{ADVENTURE}/index.html", "label": ui["back"]} if n == 1 else
                    {"url": f"/{lang}/adventures/{ADVENTURE}/prologue/03.html", "label": labels[2]} if narrator else
                    {"url": f"/{lang}/adventures/{ADVENTURE}/prologue/{n - 1:02d}.html", "label": labels[n - 2]})
            nxt = ({"url": f"/{lang}/adventures/{ADVENTURE}/read/01.html", "label": ui["prepare"]} if n >= 3 else
                   {"url": f"/{lang}/adventures/{ADVENTURE}/prologue/{n + 1:02d}.html", "label": labels[n]})
            heading_title = titles[12] if narrator else title
            front = ["---", 'layout: "hollow_hearth"', f'lang: "{lang}"', 'kind: "adventure_prologue"',
                     f'part: "{n:02d}"', f"part_kicker: {json.dumps(kicker, ensure_ascii=False)}",
                     f"title: {json.dumps(labels[n - 1] + ' · ' + title, ensure_ascii=False)}",
                     f"chapter_title: {json.dumps(heading_title, ensure_ascii=False)}",
                     f'permalink: "/{lang}/adventures/{ADVENTURE}/prologue/{n:02d}.html"',
                     f"chapters: {json.dumps([] if narrator else [{'id': f'ch-{k}', 'title': titles[k]} for k in members], ensure_ascii=False)}",
                     f"parts: {json.dumps(parts, ensure_ascii=False)}",
                     f"prev: {json.dumps(prev, ensure_ascii=False)}", f"next: {json.dumps(nxt, ensure_ascii=False)}",
                     f'generated_from: "adventure/{SOURCE_SLUG}-{lang}.tex"', "---"]
            out = a.out_dir / lang / "adventures" / ADVENTURE / "prologue" / f"{n:02d}.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("\n".join(front) + "\n" + A.tidy("".join(html_parts)), encoding="utf-8")
        print(f"{lang}: prologue/01-04.html")


if __name__ == "__main__":
    main()
