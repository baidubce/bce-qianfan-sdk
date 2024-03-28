#!/bin/bash
set -e

declare func_call=
declare reg=
declare params=
declare root_dir=
declare env_file=
declare ENV_DICT=
declare KEYWORDS_DICT=


function usage() {
    echo "cookbook test usage:"
    echo "  $0 [-f <func_call>] [-r <path_reg>] [-p <param_dict>]"
    echo ""
    echo "options:"
    echo "  -f function_call"
    echo "  -r path_reg"
    echo "  -p param_dict"
    echo "  -n ENV_DICT idx to use"
    echo "  -k KEYWORDS_DICT idx to use"
    echo ""
    echo "Example:"
    echo "  $0 -r datasets"
    echo "  $0 -f test_datasets -n 2"
}

function get_config(){
  param=$1
  param_n=$2

  if [[ -z "$param_n" ]]; then
    param_n=1
  fi

  value=$(sed -E '/^#.*|^ *$/d' "$env_file" | awk -F "${param}=" "/${param}=/{print \$2}" | sed -n "${param_n}p")
  echo "$value"
}

function check_param() {
    if [ -z "$1" ]; then
        usage
        exit
    fi
}

function parse_param() {
    while getopts :f:r:p:n:k opt; do
        case $opt in
            f)
                func_call="$OPTARG"
            ;;
            r)
                reg="$OPTARG"
            ;;
            p)
                params="$OPTARG"
            ;;
            n)
                  ENV_DICT=$(get_config ENV_DICT $OPTARG)
            ;;
            k)
                  KEYWORDS_DICT=$(get_config KEYWORDS_DICT $OPTARG)
            ;;
            \?)
                usage
                exit 1
            ;;
        esac
    done
    if  [[ -z "$ENV_DICT"  || -z "$KEYWORDS_DICT" ]]; then
      echo "ENV_DICT or KEYWORDS_DICT isn't set"
      exit 1
    fi

    if [[ ! -z $reg && -z $func_call ]]; then
      func_call="test_reg"
    fi

    if [[ ! -z $reg && $func_call != "test_reg" ]]; then
      echo "only test_reg supports -r"
    fi

    if [[ ! -z $params && $func_call != "test_reg" ]]; then
      echo "only test_reg supports -p"
      exit 1
    fi

    if [ ! -z $func_call ]; then
      func_call="::$func_call"
    fi

}

function load_env(){
  ENV_DICT=$(get_config ENV_DICT)
  KEYWORDS_DICT=$(get_config KEYWORDS_DICT)
}

################################
## main
################################
root_dir=$(dirname "$0")/../..
root_dir=$(realpath "$root_dir")
env_file="$root_dir/.env"

load_env

parse_param "$@"

cd "$root_dir"/python/test_CI || exit 1
poetry run coverage run -m  pytest  -o log_cli=true -o log_cli_level=INFO -v -r A --full-trace  test_ntbk.py"$func_call" --env "$ENV_DICT" --keywords "$KEYWORDS_DICT" --root-dir "$root_dir" --reg "$reg" --params "$params"