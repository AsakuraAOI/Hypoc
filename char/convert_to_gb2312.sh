#!/bin/bash
# 将文件或字符串转换为GB2312编码的便捷脚本

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/convert_to_gb2312.py"

convert_to_gb2312() {
    local input="$1"
    local output="$2"

    if [ -z "$input" ]; then
        echo "Usage: convert_to_gb2312.sh <input_file> [output_file]" >&2
        return 1
    fi

    if [ ! -f "$input" ]; then
        echo "Error: File not found: $input" >&2
        return 1
    fi

    if [ -z "$output" ]; then
        python "$PYTHON_SCRIPT" "$input"
    else
        python "$PYTHON_SCRIPT" "$input" "$output"
    fi
}

# 直接调用时
if [ -z "$1" ]; then
    echo "Usage: convert_to_gb2312.sh <input_file> [output_file]" >&2
    exit 1
fi

convert_to_gb2312 "$1" "$2"
