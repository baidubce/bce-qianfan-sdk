#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace qianfan/tests/trainer_test.py::test_ppt_with_sft
poetry run coverage report --omit="qianfan/tests/*"
