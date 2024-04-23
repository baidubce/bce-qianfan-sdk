#!/bin/bash

set -x

#########
###main
#########

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

cd "${SCRIPTPATH}/../"
export PYTHONPATH="${SCRIPTPATH}/../"

PID=$(ps -ef | grep "\'proxy\', \'-m\'" | awk '{print $2}')
kill -9 "$PID"

nohup poetry run python "${SCRIPTPATH}/../qianfan/tests/utils/mock_server.py" > /tmp/mock_server 2>&1 &
poetry run qianfan proxy -m 8866 > /tmp/proxy_server 2>&1 &
cd "${SCRIPTPATH}/../qianfan/tests/"
poetry run locust > /tmp/locust 2>&1 &

# 等待用户关闭
read -n 1 -p "Press any key to continue..."

PID=$(ps -ef | grep "\'proxy\', \'-m\'" | awk '{print $2}')
kill -9 "$PID"
PID=$(ps -ef | grep "locust" | awk '{print $2}' | head -n 1)
kill -9 "$PID"