#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace qianfan/tests/trainer_test.py::test_train1
poetry run coverage report --omit="qianfan/tests/*"
