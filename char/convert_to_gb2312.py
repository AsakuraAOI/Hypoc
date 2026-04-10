#!/usr/bin/env python3
"""将文件或字符串从任意编码转换为GB2312编码的脚本"""

import sys
import os


def is_valid_utf8(data: bytes) -> bool:
    """验证是否为有效的UTF-8编码"""
    try:
        decoded = data.decode('utf-8')
        reencoded = decoded.encode('utf-8')
        return reencoded == data
    except (UnicodeDecodeError, UnicodeEncodeError):
        return False


def detect_encoding(data: bytes) -> str:
    """
    尝试检测字节数据的原始编码
    常见中文编码: GBK, GB2312, GB18030, UTF-8, BIG5, UTF-16
    """
    # 先尝试UTF-8（最常见，应优先检测）
    if is_valid_utf8(data):
        return 'utf-8'

    # 编码候选列表（按优先级）
    encodings = ['gb18030', 'gbk', 'gb2312', 'big5', 'utf-16']

    for enc in encodings:
        try:
            decoded = data.decode(enc)
            # 尝试验证：用检测到的编码重新编码，看是否能还原
            reencoded = decoded.encode(enc)
            if reencoded == data:
                return enc
        except (UnicodeDecodeError, UnicodeEncodeError):
            continue

    # 如果都失败，尝试GB18030（兼容性最强）
    try:
        data.decode('gb18030')
        return 'gb18030'
    except UnicodeDecodeError:
        return 'latin-1'


def convert_file_to_gb2312(input_path: str, output_path: str = None,
                             source_encoding: str = None) -> bool:
    """
    将文件转换为GB2312编码

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（默认覆盖原文件）
        source_encoding: 源编码（None时自动检测）
    """
    try:
        # 读取原文件
        with open(input_path, 'rb') as f:
            data = f.read()

        # 自动检测源编码
        if source_encoding is None:
            source_encoding = detect_encoding(data)

        print(f"Detected source encoding: {source_encoding}", file=sys.stderr)

        # 解码
        text = data.decode(source_encoding)

        # 转换为GB2312
        result = text.encode('gb2312', errors='strict')

        # 写入目标文件
        if output_path is None:
            output_path = input_path

        # 先写临时文件再替换，防止转换失败损坏原文件
        temp_path = output_path + '.tmp'
        with open(temp_path, 'wb') as f:
            f.write(result)
            f.flush()
            os.fsync(f.fileno())

        os.replace(temp_path, output_path)
        return True

    except UnicodeEncodeError as e:
        print(f"Error: Character cannot be encoded in GB2312: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return False


def convert_string_to_gb2312(text: str, source_encoding: str = 'utf-8') -> bytes:
    """
    将字符串转换为GB2312编码的字节

    Args:
        text: 输入字符串
        source_encoding: 源字符串的编码（默认UTF-8）
    """
    try:
        return text.encode('gb2312', errors='strict')
    except UnicodeEncodeError as e:
        print(f"Error: Character cannot be encoded in GB2312: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python convert_to_gb2312.py <input> [output] [-s source_encoding]", file=sys.stderr)
        print("  <input>           - 输入文件路径")
        print("  [output]         - 输出文件路径（可选，默认覆盖原文件）")
        print("  -s <encoding>    - 指定源编码（可选，默认自动检测）", file=sys.stderr)
        print("", file=sys.stderr)
        print("Examples:", file=sys.stderr)
        print("  python convert_to_gb2312.py file.txt", file=sys.stderr)
        print("  python convert_to_gb2312.py file.txt output.txt", file=sys.stderr)
        print("  python convert_to_gb2312.py file.txt -s utf-8", file=sys.stderr)
        sys.exit(1)

    source_encoding = None
    output_path = None
    input_path = sys.argv[1]

    # 解析参数
    if len(sys.argv) >= 3:
        if sys.argv[2] == '-s':
            if len(sys.argv) < 4:
                print("Error: -s requires an encoding argument", file=sys.stderr)
                sys.exit(1)
            source_encoding = sys.argv[3]
        else:
            output_path = sys.argv[2]
            if len(sys.argv) >= 5 and sys.argv[3] == '-s':
                source_encoding = sys.argv[4]

    if not os.path.isfile(input_path):
        print(f"Error: File not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if convert_file_to_gb2312(input_path, output_path, source_encoding):
        print("SUCCESS", file=sys.stderr)
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
