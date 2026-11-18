# Jekyll conversion: full HTML preservation audit

## Result

| Check | Result |
|---|---|
| Original HTML files | 61 |
| Jekyll-converted page sources | 61 (9 regular pages + 52 chapter collection pages) |
| HTML output reconstructed from layout + page data | **61/61 SHA-256 identical** |
| Original static assets excluding `.nojekyll` | **26/26 SHA-256 identical** |
| Local links and referenced assets | **1,792 checked; 0 unresolved** |
| PDF binaries | Unchanged (included in asset hashing) |
| Desktop/mobile browser screenshots | **Not verified**: browser navigation blocked by host policy |
| Actual Jekyll command execution | **Not verified**: Jekyll gem absent, RubyGems network unavailable |

The output reconstruction follows the very small Jekyll default layout by substituting `site.data.chrome[page.chrome_key].before`, page HTML content and `.after` without normalization. This is stronger than DOM-only parity, but **does not replace an end-to-end Jekyll build**.

## Jekyll architecture

- `docs/_layouts/default.html` is the Liquid page layout.
- `docs/_data/chrome.json` preserves exact per-page document head/navigation/footer so the HTML can be reconstructed without redesign.
- `docs/_chapters/` is a Jekyll collection (52 chapters) with explicit legacy-compatible permalinks.
- Localized landing and download pages use Jekyll front matter.
- `docs/assets/` and `docs/downloads/` retain the approved files.
- `docs/.nojekyll` is intentionally absent.

**Tradeoff:** Chrome metadata is retained per page rather than fully normalized into locale-specific Liquid includes. This avoids any change to approved HTML and provides a safe baseline for future refactoring; it is not the final level of Jekyll template reuse.

## Deployment checks still needed

1. Run `bundle install` and `bundle exec jekyll build --source docs --destination _site` in a machine with RubyGems access.
2. Compare `_site/` files to `reference-sha256.json` (HTML bytes can differ if Liquid or Jekyll introduces whitespace; in that case compare DOM and rendered screens).
3. Perform desktop/mobile screenshot comparisons on the actual Jekyll output.
4. Deploy with GitHub Pages configured for `main` / `docs` after tests succeed.

The original static HTML baseline is **not** included in the deployment package; the checksums are retained for regression testing.
