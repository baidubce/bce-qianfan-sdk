#!/bin/bash

set -e

sphinx-apidoc -f -F -M -o build/docs -t python/qianfan/docs python/qianfan "*test*"
cp README.md build/docs
cp -r docs build/docs
cd build/docs
make html
