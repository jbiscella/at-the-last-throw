#!/usr/bin/env python3
"""Validate local links and expected multilingual pages in a built Jekyll site."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

LANGUAGES = ("en", "it", "fr", "uk", "de", "es")
CHAPTERS_PER_LANGUAGE = 13
ADVENTURE_SECTIONS = 5

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        key = "href" if tag in ("a", "link") else "src" if tag in ("img", "script", "source") else None
        if key and attrs.get(key):
            self.links.append(attrs[key])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--built", type=Path, required=True)
    args = parser.parse_args()
    root = args.built.resolve()
    if not root.is_dir():
        raise SystemExit(f"Site output directory missing: {root}")

    pages = sorted(root.rglob("*.html"))
    required = {root / "index.html"}
    for lang in LANGUAGES:
        required.add(root / lang / "index.html")
        required.add(root / lang / "downloads.html")
        required.update(root / lang / "read" / f"{n:02d}.html" for n in range(1, CHAPTERS_PER_LANGUAGE + 1))
        required.add(root / lang / "adventures" / "index.html")
        required.add(root / lang / "adventures" / "the-bell-of-hollow-hearth" / "index.html")
        required.update(root / lang / "adventures" / "the-bell-of-hollow-hearth" / "read" / f"{n:02d}.html" for n in range(1, ADVENTURE_SECTIONS + 1))
    missing = sorted(str(p.relative_to(root)) for p in required if not p.is_file())

    broken = []
    for page in pages:
        links = Links()
        links.feed(page.read_text(encoding="utf-8"))
        for url in links.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or url.startswith(("#", "mailto:", "tel:", "data:")):
                continue
            path = unquote(parsed.path)
            if not path:
                continue
            target = root / path.lstrip("/") if path.startswith("/") else page.parent / path
            if path.endswith("/") or not target.suffix:
                target /= "index.html"
            target = target.resolve()
            if not target.is_relative_to(root) or not target.is_file():
                broken.append((str(page.relative_to(root)), url))

    print(f"Generated HTML pages: {len(pages)}")
    print(f"Required pages: {len(required)}, missing: {len(missing)}")
    print(f"Broken local links/assets: {len(broken)}")
    for path in missing[:30]:
        print(f"MISSING: {path}")
    for page, url in broken[:30]:
        print(f"BROKEN: {page} -> {url}")
    if missing or broken:
        raise SystemExit(1)
    print(f"PASS: Jekyll site builds with all {len(LANGUAGES)} languages, {CHAPTERS_PER_LANGUAGE} rule chapters and {ADVENTURE_SECTIONS} adventure sections each, with an adventure catalog per language and valid local links.")

if __name__ == "__main__":
    main()
