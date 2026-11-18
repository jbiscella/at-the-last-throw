#!/usr/bin/env python3
"""Check real Jekyll output against the approved static-HTML SHA-256 baseline."""
import argparse
import hashlib
import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

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
    ap = argparse.ArgumentParser()
    ap.add_argument("--built", type=Path, required=True)
    ap.add_argument("--reference", type=Path, required=True)
    args = ap.parse_args()
    expected = json.loads(args.reference.read_text(encoding="utf-8"))
    root = args.built.resolve()
    actual = {
        p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*") if p.is_file()
    }
    mismatches = [p for p, digest in expected.items() if actual.get(p) != digest]
    missing = [p for p in expected if p not in actual]
    unexpected = [p for p in actual if p not in expected and not p.startswith(".")]
    broken = []
    for rel in expected:
        if not rel.endswith(".html") or rel not in actual:
            continue
        page = root / rel
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for url in parser.links:
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or url.startswith(("#", "mailto:", "tel:", "data:")):
                continue
            raw = unquote(parsed.path)
            target = root / raw.lstrip("/") if raw.startswith("/") else page.parent / raw
            if raw.endswith("/"):
                target /= "index.html"
            elif not target.suffix:
                target /= "index.html"
            if not target.is_file():
                broken.append((rel, url))
    print(f"Expected files: {len(expected)}; built files: {len(actual)}")
    print(f"SHA-256 mismatches: {len(mismatches)}; missing: {len(missing)}; extra: {len(unexpected)}")
    print(f"Broken local links: {len(broken)}")
    for title, items in [("Different/missing", mismatches), ("Unexpected", unexpected), ("Broken links", broken)]:
        for item in items[:25]:
            print(f"{title}: {item}")
    if mismatches or unexpected or broken:
        raise SystemExit(1)
    print("PASS: real Jekyll build matches approved HTML and assets byte-for-byte.")

if __name__ == "__main__":
    main()
