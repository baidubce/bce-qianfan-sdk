#!/bin/bash
set -e

# build wheel
make clean
poetry build
mkdir output
mv dist/* output
rm -rf dist
cp src/scripts/release_agile.sh ./output

# build docs
make doc
mv build/docs/_build/ ./output/docs
rm -rf build