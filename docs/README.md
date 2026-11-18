# At the Last Throw — Jekyll site

This is a Jekyll source tree for GitHub Pages (`docs/` on `main`). It preserves the previously approved static HTML presentation **without changing the PDF assets**.

- `en/`, `it/`, `fr/`, `uk/`: editable Jekyll landing/download pages.
- `_chapters/`: 52 Jekyll collection entries, one for each chapter, with preserved permalinks.
- `_layouts/default.html`: common page template.
- `_data/chrome.json`: page metadata, head, navigation and footer captured from the approved HTML to guarantee output equivalence. (A future refactor could consolidate this into locale-aware includes.)
- `_config.yml`, `Gemfile`: GitHub Pages/Jekyll configuration.
- `assets/`, `downloads/`: unchanged static assets and PDFs.

Build locally with Ruby, Bundler and `bundle exec jekyll build --source docs --destination _site`. For GitHub Pages configure **Settings → Pages → Deploy from branch → main /docs**. Do not add `.nojekyll`: it prevents Jekyll processing.

The comparison script verifies all page content and static asset hashes against the approved HTML release. Real Jekyll runtime verification remains pending until a Jekyll build environment is available.
