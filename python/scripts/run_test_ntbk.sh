#!/bin/bash


function get_config()
{
  param=$1
  value=$(sed -E '/^#.*|^ *$/d' "$env_file" | awk -F "${param}=" "/${param}=/{print \$2}" | tail -n1)
  echo "$value"
}

func_call=$1
reg=$2
params=$3

root_dir=$(dirname $0)/../..
root_dir=$(realpath "$root_dir")
env_file="$root_dir/.env"

QIANFAN_ACCESS_KEY=$(get_config QIANFAN_ACCESS_KEY)
QIANFAN_SECRET_KEY=$(get_config QIANFAN_SECRET_KEY)
KEYWORDS_DICT=$(get_config KEYWORDS_DICT)
args="--ak $QIANFAN_ACCESS_KEY --sk $QIANFAN_SECRET_KEY --keywords $KEYWORDS_DICT --root-dir $root_dir "

if [ -z "$QIANFAN_ACCESS_KEY" ] || [ -z "$QIANFAN_SECRET_KEY" ] || [[ -z "$KEYWORDS_DICT" ]]; then
  echo "QIANFAN_ACCESS_KEY QIANFAN_SECRET_KEY or KEYWORDS_DICT isn't set"
  exit 1
fi

if [ ! -z $func_call ]; then
  echo "test $func_call"
  func_call="::$func_call"
fi

if [ ! -z $reg ]; then
  echo "test $reg"
  args="$args --reg $reg"
fi

if [ ! -z $params ]; then
  echo "test $params"
  args="$args --params $params"
fi

#echo "$args"
cd "$root_dir"/python/test_CI || exit 1
poetry run coverage run -m  pytest -v -r A --full-trace  test_ntbk.py"$func_call" --ak "$QIANFAN_ACCESS_KEY" --sk "$QIANFAN_SECRET_KEY" --keywords "$KEYWORDS_DICT" --root-dir "$root_dir" --reg "\"$reg\"" --params "$params"