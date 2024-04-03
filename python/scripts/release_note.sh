#!/bin/bash

declare QF_GITHUB_TOKEN=
declare REPO=
declare OLD_TAG=

function curl_json() {  # curl获取github数据,json格式
  target=$1
  json_path=$2
  if [ $target == "pulls" ];then
    arg="&state=closed"
  else
    arg='&state=all'
  fi
  echo "[]" > $json_path
  n=1
  while true; do
      infos=$(
          curl -L \
          -H "Accept: application/vnd.github+json" \
          -H "Authorization: Bearer $QF_GITHUB_TOKEN" \
          -H "X-GitHub-Api-Version: 2022-11-28" \
          --url "https://api.github.com/repos/$REPO/$target?page=$n&per_page=100$arg"
          )

      # 提取json特定字段,并过滤得到非空包含"language"labels的数组
      infos=$(
          echo "$infos" | \
          jq -c '[.[] | {num:.number,title:.title,name:[.labels[].name],cont:.user.login}]' | \
          # 数组长度大于0
          jq -c '[.[] | select(.name|length>0)]' | \
          # 判断数组里是否有string元素以"language"开头
          jq -c '[.[] | select(.name[]|startswith("language"))]'
          )
    #  合并json到目标文件
      if [ "$infos" != "[]" ]; then
          echo "$infos" > t.json
          jq -s add $json_path t.json > h.json
          mv h.json $json_path
      else
          rm t.json
          break
      fi
      n=$((n+1))
  #结束
  done
}

function get_tag() {
  language=$1
  tag_json=$(
      curl -L \
      -H "Accept: application/vnd.github+json" \
      -H "Authorization: Bearer $QF_GITHUB_TOKEN " \
      -H "X-GitHub-Api-Version: 2022-11-28" \
      --url "https://api.github.com/repos/$REPO/tags"
  )
  tag_filter=$(
      echo "$tag_json" | \
      jq "[.[] | select(.name|startswith(\"$language\"))]"
  )
  if [ "$tag_filter" != "[]" ]; then  # 判断tag_filter是否为空, 非空则使用tag_filter，否则使用tag_json
    tag_json=$tag_filter
  else
    echo "old_tag not find"
  fi

  OLD_TAG=$(
      echo "$tag_json" | \
      jq ".[0].name" | \
      sed 's/\"//g'
  )
}

###################
#####main
###################

if [[ -z "$QF_GITHUB_TOKEN"  || -z "$REPO" ]]; then
  echo "QF_GITHUB_TOKEN or REPO is empty"
  exit 1
fi
if [ -z "$1" ] ; then
    echo "Usage: $0 language"
    echo "example: $0 js"
    echo "language: js|py|java|go"
    exit 1
fi

get_tag $1

# 获取json格式的git log
log_json=$(
    git log \
    --pretty=format:'{%n "title": "%s" %n},' \
    "$OLD_TAG..." | \
    perl -pe 'BEGIN{print "["}; END{print "]\n"}' | \
    perl -pe 's/},]/}]/'
    )

# 获取github的pulls和issues数据
curl_json pulls pulls.json
curl_json issues issues.json

# 过滤pr和issue数据
if [ "$1" == "py" ]; then
    pr_infos=$( cat pulls.json | \
    jq -c '[.[] | select(.name[]|contains("python") or contains("cookbook"))]' )
else
    pr_infos=$( cat pulls.json | \
    jq -c "[.[] | select(.name[]|contains(\"$1\"))]" )
fi
echo "$pr_infos" > pulls.json

# 获取最新issue的编号
issues_infos=$( cat issues.json | \
jq -c '[.[] | select(.name[]|contains("release note"))]' | \
jq -c "[.[] | select(.name[]|contains(\"$1\"))]" | \
jq '.[0] | .num'
)

# 排序pr编号并去重
sorted_json=$(
    cat pulls.json | \
    jq 'sort_by(.num) | unique_by(.num)' | \
    jq -c '.[] | [.num,.cont]' | \
    sed 's/\"//g' | \
    sed 's/\[//g' | \
    sed 's/\]//g'
    )
echo "$sorted_json" > pulls.json

echo "## What's Changed" > release_note.md
if [ "$issues_infos" != "null" ]; then
  echo "### Release note (#$issues_infos)" >> release_note.md
fi
# 遍历log_json, 获取每个pr的title, 判断title中#[0-9]+是否在g.txt中
for i in $(cat pulls.json); do
    if [ -z $i ]; then
        break
    fi

    line=$(echo "$i" | sed 's/,/ /g')
    num=$(echo "$line" | awk '{print $1}')
    author=$(echo "$line" | awk '{print $2}')

    title=$(
        echo "$log_json" | \
        jq ".[] | if (.title|contains(\"#$num\")) then .title else empty end"
    )
    # 判断title非空白字符,去除 \"
    if [ -n "$title" ]; then
        echo "* $title  @$author" | sed 's/\"//g' >> release_note.md
    fi
done
echo "" >> release_note.md
echo "**Full Changelog**: https://github.com/$REPO/compare/$OLD_TAG...$NEW_TAG" >> release_note.md

echo "release_note.md:"
cat release_note.md

rm pulls.json issues.json