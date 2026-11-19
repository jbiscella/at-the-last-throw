# Reproducible build environment for "At the Last Throw".
#
# Reproduces the released PDFs pixel-for-pixel (verified 2026-11-16,
# all 4 editions x 16 pages identical at 72 dpi). They were produced with
# TeX Live 2024 binaries (xdvipdfmx 20240305) and the Debian FreeSerif fonts.
#
# Packages that affect line breaking are pinned. If Debian drops one of these
# versions, the image build fails; bump the pin, rebuild, then run `make check`
# and review any reported differences before accepting them.
#
#   make docker        # build image + all editions into build/
#   make check         # compare build/*.pdf with baseline/ (see make baselines)
FROM debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    HOME=/tmp

RUN apt-get update && apt-get install -y --no-install-recommends \
      texlive-binaries=2024.20240313.70630+ds-6 \
      texlive-base=2024.20250309-1 \
      texlive-xetex=2024.20250309-1 \
      texlive-latex-recommended \
      texlive-fonts-recommended \
      texlive-latex-extra=2024.20250309-2 \
      texlive-pictures \
      texlive-fonts-extra=2024.20250309-2 \
      texlive-lang-english \
      texlive-lang-italian \
      texlive-lang-french \
      texlive-lang-german \
      texlive-lang-spanish \
      texlive-lang-cyrillic=2024.20250309-1 \
      fonts-freefont-otf=20211204+svn4273-2 \
      fonts-freefont-ttf=20211204+svn4273-2 \
      make poppler-utils imagemagick \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /work
