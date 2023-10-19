#!/bin/bash
set -x

poetry run coverage run -m pytest -v -r A --continue-on-collection-errors --full-trace qianfan
poetry run coverage report --omit="qianfan/tests/*"
