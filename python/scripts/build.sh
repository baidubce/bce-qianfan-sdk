#!/bin/bash
set -e

# build wheel
make clean
poetry build
mkdir output
mv dist/* output
rm -rf dist

# build docs
cd ..
make doc
mv build/docs/_build/ ./output/docs
rm -rf build