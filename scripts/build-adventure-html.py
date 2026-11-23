#!/usr/bin/env python3
"""Generate the web edition of "The Bell of Hollow Hearth" from its LaTeX sources.

adventure/hollow-hearth-<lang>.tex is the single authoritative source. This script
writes docs/<lang>/adventure/read/01-05.html; those files must not be edited
by hand. Requires pandoc (used for the running text only).

Page split: 01 = opening chapter, 02-04 = the three scene chapters (\\RPGChapter),
05 = the Narrator's quick reference (\\section*, or the last \\subsection).
"""
import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = ("en", "it", "fr", "de", "es", "uk")
SECTION_KEYS = ("prepare", "village", "wood", "tower", "reference")
SOURCE_SLUG = "hollow-hearth"
WEB_ASSETS = "/assets/" + SOURCE_SLUG + "/"
MAPS = ("map-village", "map-forest", "map-ground", "map-upper")
ENGRAVINGS = ("tower",)


def group_end(s, i):
    """s[i] == '{'; return the index just after the matching '}'."""
    depth = 0
    for j in range(i, len(s)):
        c = s[j]
        if c == "\\":
            continue
        if c == "{" and (j == 0 or s[j - 1] != "\\"):
            depth += 1
        elif c == "}" and s[j - 1] != "\\":
            depth -= 1
            if depth == 0:
                return j + 1
    raise ValueError(f"unbalanced group at {i}: {s[i:i + 80]!r}")


def take_args(s, i, n):
    """Read n mandatory {..} arguments starting at s[i] (skipping blanks/optional [..])."""
    args = []
    for _ in range(n):
        while i < len(s) and s[i] in " \t\n":
            i += 1
        if s[i] == "[":
            i = s.index("]", i) + 1
            while s[i] in " \t\n":
                i += 1
        end = group_end(s, i)
        args.append(s[i + 1:end - 1])
        i = end
    return args, i


def replace_macro(s, name, nargs, fn):
    out, i = [], 0
    pat = re.compile(r"\\" + name + r"(?![A-Za-z])")
    while True:
        m = pat.search(s, i)
        if not m:
            out.append(s[i:])
            return "".join(out)
        args, end = take_args(s, m.end(), nargs)
        out.append(s[i:m.start()])
        out.append(fn(*args))
        i = end


class Converter:
    def __init__(self, lang, ui):
        self.lang, self.ui = lang, ui
        self.blocks = []

    # ---- placeholders -------------------------------------------------
    def block(self, html_text):
        self.blocks.append(html_text)
        return f"\n\nHHBLOCK{len(self.blocks) - 1}X\n\n"

    # ---- inline LaTeX -> HTML via pandoc ------------------------------
    def inline(self, tex):
        tex = tex.strip()
        if not tex:
            return ""
        out = pandoc(tex)
        out = re.sub(r"^<p>(.*)</p>$", r"\1", out.strip(), flags=re.S)
        return out.strip()

    # ---- figures --------------------------------------------------------
    def figure(self, name, caption_html, alt_text):
        w, h = Image.open(ROOT / "docs" / WEB_ASSETS.strip("/") / f"{name}.webp").size
        src = "{{ '" + WEB_ASSETS + name + ".webp' | relative_url }}"
        img = (f'<img width="{w}" height="{h}" alt="{html.escape(alt_text, quote=True)}" '
               f'loading="lazy" src="{src}"/>')
        cap = f"<figcaption>{caption_html}</figcaption>" if caption_html else ""
        if name in MAPS:
            label = html.escape(self.ui["view"], quote=True)
            return f'<figure class="hh-map"><a aria-label="{label}" href="{src}">{img}</a>{cap}</figure>'
        cls = "hh-engraving" if name in ENGRAVINGS else "hh-portrait"
        return f'<figure class="{cls}">{img}{cap}</figure>'

    def text_of(self, html_text):
        return html.unescape(re.sub(r"<[^>]+>", "", html_text)).strip()

    def graphics(self, s):
        """\\includegraphics{assets/x.png} (or the .jpg print copy) followed by its caption group(s)."""
        pat = re.compile(r"\\includegraphics(\[[^\]]*\])?\{assets/(?:[\w-]+/)?([\w-]+)\.(?:png|jpg)\}")
        out, i = [], 0
        while True:
            m = pat.search(s, i)
            if not m:
                out.append(s[i:])
                return "".join(out)
            name, j = m.group(2), m.end()
            caps = []
            while True:
                k = j
                while k < len(s) and (s[k] in " \t\n" or s.startswith("\\par", k) or s.startswith("\\vspace", k)):
                    if s.startswith("\\vspace", k):
                        _, k = take_args(s, k + len("\\vspace"), 1)
                    elif s.startswith("\\par", k):
                        k += 4
                    else:
                        k += 1
                if k < len(s) and s[k] == "{":
                    end = group_end(s, k)
                    caps.append(s[k + 1:end - 1])
                    j = end
                else:
                    break
            caps_html = [self.inline(c) for c in caps]
            caption = " — ".join(c for c in caps_html if c)
            # A layout command after the caption (\vspace, removed by clean()) leaves an empty group.
            alt = " — ".join(t for t in (self.text_of(c) for c in caps_html) if t) or name
            out.append(s[i:m.start()])
            out.append(self.block(self.figure(name, caption, alt)))
            i = j

    # ---- tables ---------------------------------------------------------
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
        thead = ("<thead><tr>" + "".join(f"<th>{c}</th>" for c in head) + "</tr></thead>") if head else ""
        return self.block(f'<div class="table-scroll"><table>{thead}<tbody>{"".join(rows_html)}</tbody></table></div>')

    def tables(self, s):
        for env in ("tabularx", "rpgtable"):
            pat = re.compile(r"\\begin\{" + env + r"\}")
            while True:
                m = pat.search(s)
                if not m:
                    break
                nargs = 2 if env == "tabularx" else 1
                _, j = take_args(s, m.end(), nargs)
                end = s.index("\\end{" + env + "}", j)
                s = s[:m.start()] + self.table(s[j:end]) + s[end + len("\\end{" + env + "}"):]
        return s

    # ---- stat boxes -----------------------------------------------------
    def notes(self, s):
        pat = re.compile(r"\\begin\{rpgnote\}(\[[^\]]*\])?")
        while True:
            m = pat.search(s)
            if not m:
                return s
            end = s.index("\\end{rpgnote}", m.end())
            inner = s[m.end():end]
            paras = [p for p in re.split(r"\\par(?![a-zA-Z])|\n\s*\n", inner) if p.strip()]
            body = "".join(f"<p>{self.inline(p)}</p>" for p in paras if self.inline(p))
            s = s[:m.start()] + self.block(f'<aside class="hh-stat">{body}</aside>') + s[end + len("\\end{rpgnote}"):]

    # ---- whole chunk ----------------------------------------------------
    def convert(self, tex):
        s = tex
        s = replace_macro(s, "HHSceneMap", 3, lambda n, t, c: self.block(
            self.figure(n, f"<strong>{self.inline(t)}</strong> — {self.inline(c)}",
                        self.text_of(self.inline(t)) + " — " + self.text_of(self.inline(c)))))
        s = replace_macro(s, "HHInlineFigure", 3, lambda n, w, c: self.block(
            self.figure(n, self.inline(c), self.text_of(self.inline(c)))))
        s = replace_macro(s, "HHSceneArt", 2, lambda n, c: self.block(
            self.figure(n, self.inline(c), self.text_of(self.inline(c)) or n)))
        s = self.notes(s)
        s = self.graphics(s)
        s = self.tables(s)
        # layout-only wrappers around figures
        s = re.sub(r"\\begin\{(wrapfigure|minipage)\}(\[[^\]]*\])?(\{[^{}]*\})*", "\n\n", s)
        s = re.sub(r"\\end\{(wrapfigure|minipage)\}", "\n\n", s)
        s = re.sub(r"\\begin\{tabular\}\{@\{\}[^\n]*", "\n\n", s)
        s = re.sub(r"\\end\{tabular\}", "\n\n", s)
        s = re.sub(r"^\s*&\s*$", "\n\n", s, flags=re.M)
        html_out = pandoc(s)
        for n, b in enumerate(self.blocks):
            html_out = re.sub(rf"<p>HHBLOCK{n}X</p>|HHBLOCK{n}X", lambda _m, b=b: b, html_out)
        return tidy(html_out)


def clean(s):
    """Typographic and layout-only LaTeX that pandoc should not see."""
    s = s.replace("\\textquotesingle{}", "’")
    s = re.sub(r"\\textquotesingle ?", "’", s)
    s = re.sub(r"\\textperiodcentered\\? ?", " · ", s)
    s = s.replace("\\textemdash", "—")
    for a, b in (("$-1$", "−1"), ("$-2$", "−2"), ("$\\le$", "≤"), ("$\\cdot$", "·"), ("$\\geq$", "≥"), ("$\\ge$", "≥")):
        s = s.replace(a, b)
    s = re.sub(r"\\(needspace|Needspace|vspace\*?|hspace\*?|arrayrulecolor|addcontentsline|rowcolors|setlength|color)"
               r"(\{[^{}]*\})+", "{}", s)  # "{}" keeps a following command word separate
    s = re.sub(r"\\renewcommand\{\\arraystretch\}\{[^{}]*\}", "{}", s)
    s = re.sub(r"\\(smallskip|medskip|bigskip|noindent|hfill|centering|raggedright|tightlist|begingroup|endgroup|"
               r"footnotesize|scriptsize|small|normalfont|itshape)(?![A-Za-z]) ?", "", s)
    return s


def tidy(h):
    h = re.sub(r"(^|[\s(\[>«»—–-])’(?=\w)", r"\1‘", h)  # opening single quote
    h = re.sub(r"\n{3,}", "\n\n", h)
    return h.strip() + "\n"


def pandoc(tex):
    r = subprocess.run(["pandoc", "-f", "latex", "-t", "html5", "--wrap=none"],
                       input=tex, capture_output=True, text=True, check=True)
    return r.stdout


def split_pages(tex):
    body = tex.split("\\RPGStartMainMatter", 1)[1].split("\\HHAdventureBackCover", 1)[0]
    chapters = [m.start() for m in re.finditer(r"\\RPGChapter\{", body)]
    if len(chapters) != 4:
        raise SystemExit(f"expected 4 \\RPGChapter, found {len(chapters)}")
    ref = body.find("\\section*{")
    if ref < 0:
        ref = [m.start() for m in re.finditer(r"\\subsection\{", body)][-1]
    bounds = chapters + [ref, len(body)]
    pages = [body[bounds[k]:bounds[k + 1]] for k in range(5)]
    # drop the chapter / reference heading itself; the layout prints the title
    pages = [re.sub(r"^\\(RPGChapter|section\*|subsection)\{[^\n]*?\}(\\label\{[^}]*\})?(\\addcontentsline\{[^}]*\}\{[^}]*\}\{[^}]*\})?", "", p.lstrip())
             for p in pages]
    # a scene map printed just before a chapter belongs to that chapter
    for k in range(4):
        m = re.search(r"(\\HHSceneMap\{[^{}]*\}\{[^{}]*\}\{[^{}]*\})\s*$", pages[k])
        if m:
            pages[k] = pages[k][:m.start()]
            pages[k + 1] = m.group(1) + "\n\n" + pages[k + 1]
    return pages


def front_matter(lang, ui, n):
    sec = f"{n + 1:02d}"
    title = ui[SECTION_KEYS[n]]
    lines = ["---", 'layout: "hollow_hearth"', f'lang: "{lang}"', 'kind: "adventure_chapter"',
             f'section: "{sec}"', f"chapter_title: {json.dumps(title, ensure_ascii=False)}",
             f"title: {json.dumps(title, ensure_ascii=False)}", f'permalink: "/{lang}/adventure/read/{sec}.html"']
    if n > 0:
        lines.append(f'previous: "{n:02d}"')
    if n < 4:
        lines.append(f'next: "{n + 2:02d}"')
    lines.append("generated_from: \"adventure/" + SOURCE_SLUG + "-" + lang + ".tex\"")
    lines.append("---")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-dir", type=Path, default=ROOT / "adventure")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "docs")
    ap.add_argument("langs", nargs="*", default=list(LANGUAGES))
    a = ap.parse_args()
    data = json.loads((ROOT / "docs/_data/hollow_hearth.json").read_text(encoding="utf-8"))
    for lang in a.langs:
        tex = (a.source_dir / f"{SOURCE_SLUG}-{lang}.tex").read_text(encoding="utf-8")
        for n, chunk in enumerate(split_pages(tex)):
            conv = Converter(lang, data[lang])
            body = conv.convert(clean(chunk))
            leftover = re.findall(r"\\[A-Za-z]+|HHBLOCK\d+X", re.sub(r"<[^>]+>", "", body))
            if leftover:
                sys.exit(f"{lang} page {n + 1:02d}: unconverted LaTeX {sorted(set(leftover))}")
            out = a.out_dir / lang / "adventure" / "read" / f"{n + 1:02d}.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(front_matter(lang, data[lang], n) + body, encoding="utf-8")
        print(f"{lang}: 5 pages written")


if __name__ == "__main__":
    main()
