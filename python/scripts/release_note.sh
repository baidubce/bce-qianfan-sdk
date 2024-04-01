#!/bin/bash

if [ -z "$1" ] ; then
    echo "Usage: $0 <start> <end>"
    exit 1
fi

tag_json=$(
        curl -L \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $QF_GITHUB_TOKEN " \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        --url "https://api.github.com/repos/$REPO/tags"
)
tag_filter=$(
    echo "$tag_json" | \
    jq "[.[] | select(.name|startswith(\"$1\"))]"
)


if [ "$tag_filter" == "[]" ]; then
  echo "old_tag not find"
  OLD_TAG=$(
      echo "$tag_json" | \
      jq ".[] | .[0].name" | \
      sed 's/\"//g'
  )
else
  OLD_TAG=$(
      echo "$tag_filter" | \
      jq ".[0].name" | \
      sed 's/\"//g'
  )
fi


log_json=$(
    git log \
    --pretty=format:'{%n "title": "%s" %n},' \
    "$OLD_TAG..." | \
    perl -pe 'BEGIN{print "["}; END{print "]\n"}' | \
    perl -pe 's/},]/}]/'
    )

echo '[]' > g.json

# curl 循环获取每页pr信息
n=1
while true; do
    pr_info=$(
        curl -L \
        -H "Accept: application/vnd.github+json" \
        -H "Authorization: Bearer $QF_GITHUB_TOKEN" \
        -H "X-GitHub-Api-Version: 2022-11-28" \
        --url "https://api.github.com/repos/$REPO/pulls?page=$n&per_page=100&state=closed"
        )

    infos=$(
        echo "$pr_info" | \
        jq '[.[] | {num:.number,title:.title,name:.labels[].name}]'
        )


    if [ "$1" == "py" ]; then
    infos=$(
        echo "$pr_info" | \
        jq '[.[] | {num:.number,title:.title,name:.labels[].name,cont:.user.login}]' | \
        jq -c '[.[] | select(.name == "language/python" or .name == "cookbook")]'
        )
    else
    infos=$(
        echo "$pr_info" | \
        jq '[.[] | {num:.number,title:.title,name:.labels[].name,cont:.user.login}]' | \
        jq -c "[.[] | select(.name == \"language/$1\")]"
        )
    fi

    if [ "$infos" != "[]" ]; then
        echo "$infos" > t.json
        ## 合并t.json和g.json，两者都是数组，合并后为新的g.json
        jq -s add g.json t.json > h.json
        mv h.json g.json
    else
        rm t.json
        break
    fi
    n=$((n+1))
#结束
done

# 排序json文件并去重
sorted_json=$(
    cat g.json | \
    jq 'sort_by(.num) | unique_by(.num)' | \
    jq -c '.[] | [.num,.cont]' | \
    sed 's/\"//g' | \
    sed 's/\[//g' | \
    sed 's/\]//g'
    )
echo "$sorted_json" > g.json

echo "## What's Changed" > release_note.md
# 遍历log_json, 获取每个pr的title, 判断title中#[0-9]+是否在g.txt中
for i in $(cat g.json); do
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

echo "release_note.md:\n"
cat release_note.md

rm g.json