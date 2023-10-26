#!/bin/bash

set -e

sphinx-apidoc -f -F -M -o build/docs -t src/qianfan/docs src/qianfan "*test*"
cp src/qianfan/docs/*.rst build/docs
cd build/docs 
make html