#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace qianfan/tests/trainer_test.py
poetry run coverage report --omit="qianfan/tests/*"
