#!/bin/bash
set -e

SCRIPT=$(realpath "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOTPATH="${SCRIPTPATH}/../../"
OUTPUT_PATH="${PWD}/output"

# build wheel
make clean
poetry build
mkdir "${OUTPUT_PATH}"
mv dist/* "${OUTPUT_PATH}"
rm -rf dist

# build docs
make doc
# mv build/docs/_build/ ./output/docs
# rm -rf build