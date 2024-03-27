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
    echo "sync github repo to iCode repo usage:"
    echo "  $0 [-f <func_call>] [-r <path_reg>] [-p <param_dict>]"
    echo ""
    echo "options:"
    echo "  -f function_call"
    echo "  -r path_reg"
    echo "  -p param_dict"
    echo "  -a QIANFAN_ACCESS_KEY"
    echo "  -s QIANFAN_SECRET_KEY"
    echo "  -k KEYWORDS_DICT"
    echo ""
    echo "Example:"
    echo "  $0 -f test_reg -r datasets"
}

function get_config(){
  param=$1
  value=$(sed -E '/^#.*|^ *$/d' "$env_file" | awk -F "${param}=" "/${param}=/{print \$2}" | tail -n1)
  echo "$value"
}

function check_param() {
    if [ -z "$1" ]; then
        usage
        exit
    fi
}

function parse_param() {
    while getopts :f:r:p:a:s:k:h opt; do
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
            a)
                check_param "$OPTARG"
                QIANFAN_ACCESS_KEY="$OPTARG"
            ;;
            s)
                check_param "$OPTARG"
                QIANFAN_SECRET_KEY="$OPTARG"
            ;;
            k)
                check_param "$OPTARG"
                KEYWORDS_DICT="$OPTARG"
            ;;
            \h)
                usage
                exit
            ;;
            \?)
                usage
                exit
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