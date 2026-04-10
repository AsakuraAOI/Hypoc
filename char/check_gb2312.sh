#!/bin/bash
# 检测字符串或文件是否为GB2312编码的便捷脚本

check_gb2312() {
    local content="$1"
    local result

    result=$(python "$(dirname "$0")/check_gb2312.py" "$content" 2>/dev/null)
    if [ "$result" = "GB2312" ]; then
        return 0
    else
        return 1
    fi
}

check_gb2312_file() {
    local filepath="$1"
    local result

    result=$(python "$(dirname "$0")/check_gb2312.py" -f "$filepath" 2>/dev/null)
    if [ "$result" = "GB2312" ]; then
        return 0
    else
        return 1
    fi
}

# 直接调用时
if [ -z "$1" ]; then
    echo "Usage: check_gb2312.sh <string>"
    echo "       check_gb2312.sh -f <file_path>"
    exit 1
fi

if [ "$1" = "-f" ]; then
    check_gb2312_file "$2"
else
    check_gb2312 "$1"
fi
