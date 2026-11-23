# At the Last Throw — build the four editions.
#
#   make docker            build all editions inside the pinned TeX Live 2024 container
#                          (reproduces the released PDFs exactly; see Dockerfile)
#   make                   build all editions with the local TeX install into build/
#   make en|it|fr|uk       build a single edition with the local TeX install
#   make baselines         download the latest release PDFs into baseline/ (needs gh)
#   make check             pixel-compare build/*.pdf against baseline/*.pdf
#   make docker-check      same, using the tools inside the container
#   make docker-adventure  adventure print art and PDFs into docs/downloads/ (pinned container)
#   make docker-sheets     blank and pregenerated character sheets, with their checks (pinned container)
#   make site              build the Jekyll site into build/site/ (ruby:3.3 container) and check its links
#   make site-serve        serve the site with live reload on port 4000 (ruby:3.3 container)
#   make page-counts       compare the page count of every PDF in docs/downloads/ with REF (origin/main)
#   make deps              verify that the local toolchain has every package/font needed
#   make update-baselines  copy build/*.pdf into baseline/ (local only)
#   make clean             remove build/
#
# Each edition is compiled twice: TikZ overlays on the covers use remembered page
# positions, and the table of contents needs a second pass.

EDITIONS := manual manual-it manual-fr manual-uk manual-de manual-es
BASELINE_EDITIONS := manual manual-it manual-fr manual-uk
BUILD    := build
BASELINE := baseline
XELATEX  := xelatex -interaction=nonstopmode -halt-on-error -output-directory=$(BUILD)
IMAGE    := at-the-last-throw-tex:tl2024
# Adventure slug for docker-adventure (sources adventure/<slug>-<lang>.tex).
SLUG     := hollow-hearth
DPI      := 72
# Set DIFF_DIR=build/diff to also write a highlighted diff image for every changed page.
DIFF_DIR :=
# Release to download baselines from; empty means the latest release.
BASELINE_TAG :=

DOCKER_RUN = docker run --rm -u $$(id -u):$$(id -g) -v "$(CURDIR)":/work -w /work

SHARED := rpgmanual.sty rpgcover.sty illustrated-panel.sty $(wildcard assets/*)
PDFS   := $(EDITIONS:%=$(BUILD)/%.pdf)

# Toolchain fingerprint: the XeTeX version and the FreeSerif files fontconfig sees.
# PDFs depend on a stamp named after it, so switching between the local toolchain
# and the container (or upgrading either) rebuilds instead of reusing stale output.
TOOLCHAIN_ID := $(shell { xelatex --version 2>/dev/null | head -n 1; fc-list FreeSerif file 2>/dev/null | sort; } | cksum | cut -d ' ' -f 1)
STAMP        := $(BUILD)/.toolchain-$(TOOLCHAIN_ID)

# A failed XeLaTeX pass must not leave a PDF behind that a retry would accept.
.DELETE_ON_ERROR:

.PHONY: all en it fr uk de es docker docker-image docker-shell docker-check docker-adventure docker-sheets site site-serve page-counts check baselines \
        deps update-baselines clean

all: $(PDFS)

en: $(BUILD)/manual.pdf
it: $(BUILD)/manual-it.pdf
fr: $(BUILD)/manual-fr.pdf
uk: $(BUILD)/manual-uk.pdf
de: $(BUILD)/manual-de.pdf
es: $(BUILD)/manual-es.pdf

$(STAMP): | $(BUILD)
	@rm -f $(BUILD)/.toolchain-*; touch $@

$(BUILD)/%.pdf: %.tex $(SHARED) $(STAMP) | $(BUILD)
	@echo "== $< (pass 1)"; $(XELATEX) $< >/dev/null || { tail -n 30 $(BUILD)/$*.log; exit 1; }
	@echo "== $< (pass 2)"; $(XELATEX) $< >/dev/null || { tail -n 30 $(BUILD)/$*.log; exit 1; }
	@grep -c 'Overfull' $(BUILD)/$*.log | xargs -I{} echo "   $*: {} overfull box warning(s), $$(pdfinfo $@ | awk '/^Pages:/{print $$2}') pages"

$(BUILD):
	mkdir -p $@

docker-image:
	docker build -t $(IMAGE) .

# Runs as the calling user so build/ is not owned by root. Always recompiles (-B):
# a rebuilt image can change the layout without changing the XeTeX version.
docker: docker-image | $(BUILD)
	$(DOCKER_RUN) $(IMAGE) make -B all

# Adventures: the print JPEGs from the PNG originals, then the PDFs (scripts/build-adventure-*.sh).
docker-adventure: docker-image
	$(DOCKER_RUN) $(IMAGE) scripts/build-adventure-print-art.sh $(SLUG)
	$(DOCKER_RUN) $(IMAGE) scripts/build-adventure-pdfs.sh $(SLUG)

# Character sheets: builds them in character-sheets/ and checks every page; copying them to
# docs/downloads/ is a separate, deliberate step.
docker-sheets: docker-image
	$(DOCKER_RUN) -w /work/character-sheets $(IMAGE) ./build.sh

# The website, built like GitHub Pages does (github-pages gem from docs/Gemfile.lock) in the
# official ruby:3.3 image; the gems are cached in the jekyll-gems volume.
JEKYLL_RUN = docker run --rm -v "$(CURDIR)/docs":/srv/site:ro -v jekyll-gems:/gems -e BUNDLE_PATH=/gems -e BUNDLE_FROZEN=true -w /srv/site
site: | $(BUILD)
	mkdir -p $(BUILD)/site
	$(JEKYLL_RUN) -v "$(CURDIR)/$(BUILD)/site":/out ruby:3.3 sh -c 'bundle install --quiet && bundle exec jekyll build --destination /tmp/site && cp -r /tmp/site/. /out && chown -R $(shell id -u):$(shell id -g) /out'
	python3 scripts/check-jekyll-site.py --built $(BUILD)/site

site-serve:
	$(JEKYLL_RUN) -p 4000:4000 -p 35729:35729 ruby:3.3 sh -c 'bundle install --quiet && bundle exec jekyll serve --host 0.0.0.0 --livereload --destination /tmp/site'

REF ?= origin/main
page-counts:
	scripts/check-page-counts.sh $(REF)

docker-shell: docker-image
	$(DOCKER_RUN) -it $(IMAGE) bash

docker-check: docker-image
	$(DOCKER_RUN) $(IMAGE) make check BASELINE=$(BASELINE) DIFF_DIR=$(DIFF_DIR) DPI=$(DPI)

# Compares whatever is already in build/; it never rebuilds, so a failed
# `make docker` cannot be silently replaced by a local-toolchain build.
check:
	@for e in $(BASELINE_EDITIONS); do \
	  [ -f $(BUILD)/$$e.pdf ] || { echo "missing $(BUILD)/$$e.pdf - run 'make docker' or 'make' first"; exit 2; }; \
	  [ -f $(BASELINE)/$$e.pdf ] || { echo "missing $(BASELINE)/$$e.pdf - run 'make baselines' first"; exit 2; }; \
	done
	@rc=0; for e in $(BASELINE_EDITIONS); do \
	  DIFF_DIR=$(DIFF_DIR) scripts/compare-pdf.sh $(BASELINE)/$$e.pdf $(BUILD)/$$e.pdf $(DPI) || rc=1; \
	done; exit $$rc

baselines:
	mkdir -p $(BASELINE)
	gh release download $(BASELINE_TAG) --pattern 'manual*.pdf' --dir $(BASELINE) --clobber
	@ls $(BASELINE)

deps:
	@scripts/check-deps.sh

update-baselines:
	@for e in $(BASELINE_EDITIONS); do [ -f $(BUILD)/$$e.pdf ] || { echo "missing $(BUILD)/$$e.pdf"; exit 2; }; done
	@mkdir -p $(BASELINE); for e in $(EDITIONS); do cp -v $(BUILD)/$$e.pdf $(BASELINE)/$$e.pdf; done

clean:
	rm -rf $(BUILD)
