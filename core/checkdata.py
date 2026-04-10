#!/usr/bin/env python3
"""
Checkdata解析模块
"""

from typing import List, Tuple


def parse_checkdata(content: str) -> List[Tuple[str, str]]:
    """
    解析checkdata文件
    格式: [case_id]\ninput_lines...\n[case_id]\n...
    Returns: [(case_id, input_text), ...]
    """
    inputs = []
    lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('[') and line.endswith(']'):
            case_id = line[1:-1]
            i += 1
            input_lines = []
            while i < len(lines):
                next_line = lines[i].strip()
                if next_line.startswith('[') and next_line.endswith(']'):
                    i -= 1
                    break
                if next_line:
                    input_lines.append(next_line)
                i += 1
            inputs.append((case_id, '\n'.join(input_lines)))
        else:
            i += 1
    return inputs


def build_checkdata_content(entries: List[Tuple[str, str]]) -> str:
    """
    从检查点条目生成checkdata格式内容
    entries: [(case_id, input_text), ...]
    """
    lines = []
    for case_id, input_val in entries:
        if case_id:
            lines.append(f"[{case_id}]")
            if input_val:
                lines.append(input_val)
    return "\n".join(lines)
