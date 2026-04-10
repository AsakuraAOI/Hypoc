#!/usr/bin/env python3
"""检测代码/文本是否为GB2312编码的脚本"""

import sys
import os


def is_gb2312(data: bytes) -> bool:
    """
    检测数据是否为GB2312编码

    GB2312规则:
    - ASCII字符: 0x00-0x7F (单字节)
    - 中文汉字: 高字节0xA1-0xF7, 低字节0xA1-0xFE (双字节)
    - 标点符号/日文等扩展: 高字节0xA1-0xF7, 低字节0x00-0xFF
    """
    i = 0
    while i < len(data):
        byte = data[i]

        # ASCII范围 (0x00-0x7F)
        if byte <= 0x7F:
            i += 1
            continue

        # 如果字节 >= 0x80，需要是GB2312的双字节编码
        if i + 1 >= len(data):
            return False

        low_byte = data[i + 1]

        # GB2312高字节范围: 0xA1-0xF7
        # GB2312低字节范围: 0xA1-0xFE
        if 0xA1 <= byte <= 0xF7 and 0xA1 <= low_byte <= 0xFE:
            i += 2
            continue
        else:
            return False

    return True


def check_gb2312_file(filepath: str) -> bool:
    """检测文件编码"""
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
        return is_gb2312(data)
    except Exception as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return False


def check_gb2312_string(text: str) -> bool:
    """检测字符串是否可以被GB2312编码"""
    try:
        # 尝试用GB2312编码
        encoded = text.encode('gb2312')
        # 再解码验证
        decoded = encoded.decode('gb2312')
        return text == decoded
    except (UnicodeEncodeError, UnicodeDecodeError):
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_gb2312.py <string>|<file_path>", file=sys.stderr)
        print("  <string>  - 要检测的字符串")
        print("  <file_path> - 要检测的文件路径 (带 -f 标志)", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == '-f' and len(sys.argv) >= 3:
        # 文件模式
        result = check_gb2312_file(sys.argv[2])
    else:
        # 字符串模式
        result = check_gb2312_string(sys.argv[1])

    if result:
        print("GB2312")
        sys.exit(0)
    else:
        print("NOT_GB2312")
        sys.exit(1)


if __name__ == '__main__':
    main()
