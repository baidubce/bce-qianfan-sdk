#!/bin/bash
set -e

SCRIPT=$(readlink -f -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOTPATH="${SCRIPTPATH}/../../"
OUTPUT_PATH="${PWD}/output"

# build wheel
make clean
poetry build
mkdir -p "${OUTPUT_PATH}"
mv dist/* "${OUTPUT_PATH}"
rm -rf dist
