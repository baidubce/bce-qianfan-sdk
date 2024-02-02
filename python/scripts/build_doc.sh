#!/bin/bash

set -ex

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")
ROOTPATH="${SCRIPTPATH}/../../"
OUTPUT_PATH="${PWD}/output"
DOCS_PATH="${OUTPUT_PATH}/docs_tmp"

sphinx-apidoc -f -F -M -o "${DOCS_PATH}" -t "${ROOTPATH}/docs/template" "${SCRIPTPATH}/../qianfan" "*test*"
cp "${ROOTPATH}/README.md" "${DOCS_PATH}"
cp -r "${ROOTPATH}/docs" "${DOCS_PATH}"
make -C "${DOCS_PATH}" html
mv "${DOCS_PATH}" "${OUTPUT_PATH}/docs"
rm -rf "${DOCS_PATH}"