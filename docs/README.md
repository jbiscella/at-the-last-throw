# At the Last Throw — Jekyll site

Jekyll sources for GitHub Pages (`docs/` on `main`), including four languages and the standalone downloadable PDFs.

- `en/`, `it/`, `fr/`, `uk/`: editable landing/download pages.
- `_chapters/`: 52 Jekyll collection entries (13 chapters per language).
- `_layouts/default.html`: shared layout.
- `_data/chrome.json`: shared page chrome and navigation.
- `_config.yml`, `Gemfile`: Jekyll configuration.
- `assets/`, `downloads/`: illustrations and PDFs.

Build locally with Ruby, Bundler and `bundle exec jekyll build --source docs --destination _site`. For GitHub Pages configure **Settings → Pages → Deploy from branch → main /docs**. Do not add `.nojekyll`.

On pull requests affecting the site, GitHub Actions builds with Jekyll and checks that all four language editions have 13 readable chapters, a homepage and downloads page, and that local links and assets resolve. The former SHA-256 comparison against the one-time static HTML migration baseline has been removed: future legitimate content and layout changes do not require updating a frozen baseline.
