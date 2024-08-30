#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace --cache-clear qianfan/tests/trainer_test.py::test_trainer_sft_run
poetry run coverage report --omit="qianfan/tests/*"
