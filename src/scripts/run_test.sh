#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace qianfan/tests/service_test.py::test_sdk_console_indicator
poetry run coverage report --omit="qianfan/tests/*"
