#!/bin/bash

set -ex

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOTPATH="${SCRIPTPATH}/../../"
OUTPUT_PATH="${PWD}/output"

sphinx-apidoc -f -F -M -o "${OUTPUT_PATH}" -t "${SCRIPTPATH}/../qianfan/docs" "${SCRIPTPATH}/../qianfan" "*test*"
cp "${ROOTPATH}/README.md" "${OUTPUT_PATH}"
cp -r "${ROOTPATH}/docs" "${OUTPUT_PATH}"
make -C "${OUTPUT_PATH}" html
