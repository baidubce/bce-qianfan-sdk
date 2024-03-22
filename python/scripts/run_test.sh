#!/bin/bash
set -xe

poetry run coverage run -m pytest -v -r A --full-trace qianfan/tests/chat_completion_test.py::test_generate 
poetry run coverage report --omit="qianfan/tests/*"
