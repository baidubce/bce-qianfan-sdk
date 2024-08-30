#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace --cache-clear qianfan/tests/finetune_test.py::test_finetune_v2_create_job
poetry run coverage report --omit="qianfan/tests/*"
