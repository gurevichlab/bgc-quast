#!/usr/bin/env bash
set -euo pipefail

VERSION="$(tr -d '[:space:]' < VERSION.txt)"
NAME="bgc-quast-${VERSION}"

mkdir -p dist

git archive \
  --format=tar.gz \
  --prefix="${NAME}/" \
  -o "dist/${NAME}.tar.gz" \
  HEAD

echo "Created dist/${NAME}.tar.gz"
