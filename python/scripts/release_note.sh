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

if [ "$1" == "python" ] ; then
    tag_json=$(
        echo "$tag_json" | \
        jq '[.[] | select(.name|startswith("py"))]'
    )
else
    tag_json=$(
        echo "$tag_json" | \
        jq "[.[] | select(.name|startswith(\"$1\"))]"
    )
fi

old_tag=$(
    echo "$tag_json" | \
    jq ".[1].name" | \
    sed 's/\"//g'
)

echo "old_tag: $old_tag"

log_json=$(
    git log \
    --pretty=format:'{%n "title": "%s",%n "author": "%an" %n},' \
    "$old_tag..." | \
    perl -pe 'BEGIN{print "["}; END{print "]\n"}' | \
    perl -pe 's/},]/}]/'
    )

if [ -f g.txt ]; then
    rm g.txt
    echo "remove g.txt"
fi
touch g.txt

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


    if [ "$1" == "python" ]; then
    infos=$(
        echo "$pr_info" | \
        jq '[.[] | {num:.number,title:.title,name:.labels[].name}]' | \
        jq '.[] | if (.name == "language/python" or .name == "cookbook") then .num else empty end'
        )
    else
    infos=$(
        echo "$pr_info" | \
        jq '[.[] | {num:.number,title:.title,name:.labels[].name}]' | \
        jq ".[] | if (.name == \"language/$1\") then .num else empty end"
        )
    fi

    if [ -z "$infos" ]; then
    break
    else
    echo "$infos" >> g.txt
    fi
    n=$((n+1))
#结束
done

if [ -f release_note.md ]; then
    rm release_note.md
    echo "remove release_note.md"
fi

touch release_note.md

# 遍历log_json, 获取每个pr的title, 判断title中#[0-9]+是否在g.txt中
for i in $(cat g.txt | sort | uniq); do
    if [ -z $i ]; then
        break
    fi
    title=$(
        echo "$log_json" | \
        jq ".[] | if (.title|contains(\"#$i\")) then .title else empty end"
    )
    author=$(
        echo "$log_json" | \
        jq ".[] | if (.title|contains(\"#$i\")) then .author else empty end"
    )
    # 判断title非空白字符,去除 \"
    if [ -n "$title" ]; then
        echo "* $title  @$author" | sed 's/\"//g' >> release_note.md
    fi
done
rm g.txt