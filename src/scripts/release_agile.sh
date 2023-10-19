#!/bin/bash
set -x

echo "Current branch: ${AGILE_COMPILE_BRANCH}"

if [[ "${AGILE_COMPILE_BRANCH}" != release* ]]; then
    echo "Not a release branch, exiting"
    exit 1
fi

VER=$(echo ${AGILE_COMPILE_BRANCH} | sed 's/release-//')

if [[ ${VER} != ${VERSION} ]]; then
    echo "The release branch mismatch the expected version, exiting"
    exit 1
fi

# upload to pypi
poetry publish --build ./qianfan-${VER}-py3-none-any.whl -u__token__ -p${TOKEN}