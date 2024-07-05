#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace --cache-clear qianfan
poetry run coverage report --omit="qianfan/tests/*"
