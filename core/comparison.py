#!/usr/bin/env python3
"""
核心比对逻辑模块
"""

import subprocess
import json
import os
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


def get_base_dir() -> Path:
    """获取基础目录，支持打包后的场景"""
    # 优先检查 __file__ 指向的位置（模块在解压后的位置）
    base = Path(__file__).parent.parent
    if (base / "data").exists():
        return base

    # PyInstaller _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        meipass = Path(sys._MEIPASS)
        if (meipass / "data").exists():
            return meipass

    # exe 所在目录（standalone/onefile 输出目录）
    exe_dir = Path(sys.executable).parent
    if (exe_dir / "data").exists():
        return exe_dir

    # 开发环境 fallback
    return base


DATA_DIR = get_base_dir() / "data"
DEMORAW_DIR = DATA_DIR / "demoraw"
CHECKDATA_DIR = DATA_DIR / "checkdata"


@dataclass
class TestResult:
    """单条测试结果"""
    case_id: str
    input_val: str
    expected_text: str
    actual_text: str
    expected_hex: str
    actual_hex: str
    status: str  # PASS, FAIL
    hex_match: bool
    text_match: bool
    diff_info: Optional[Dict] = None  # HEX diff信息


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


def run_single_exe(exe_path: str, input_text: str, timeout: int = 5) -> Dict:
    """
    运行单个EXE并获取输出
    Returns: {"hex": str, "text": str, "stderr": str, "returncode": int, "error": str or None}
    """
    try:
        if not os.path.exists(exe_path):
            return {
                "hex": "", "text": "", "stderr": "",
                "returncode": -1, "error": f"文件不存在: {exe_path}"
            }

        proc = subprocess.run(
            [exe_path],
            input=(input_text + "\n").encode("utf-8"),
            capture_output=True,
            timeout=timeout,
            cwd=str(Path(exe_path).parent),
        )
        raw_output = proc.stdout
        return {
            "hex": raw_output.hex() if raw_output else "",
            "text": raw_output.decode("gbk", errors="replace").strip(),
            "stderr": proc.stderr.decode("utf-8", errors="replace").strip(),
            "returncode": proc.returncode,
            "error": None
        }
    except subprocess.TimeoutExpired:
        return {"hex": "", "text": "[超时]", "stderr": "", "returncode": -1, "error": "Timeout"}
    except Exception as ex:
        return {"hex": "", "text": f"[错误: {str(ex)}]", "stderr": "", "returncode": -1, "error": str(ex)}


def analyze_hex_diff(hex1: str, hex2: str) -> Optional[Dict]:
    """
    分析两个HEX字符串的差异
    Returns: {"pos": int, "char_pos": int, "expected_char": str, "actual_char": str} or None
    """
    if hex1 == hex2:
        return None

    # 转换为字节进行比较
    bytes1 = bytes.fromhex(hex1) if hex1 else b''
    bytes2 = bytes.fromhex(hex2) if hex2 else b''

    min_len = min(len(bytes1), len(bytes2))
    for i in range(min_len):
        if bytes1[i] != bytes2[i]:
            # 找到差异位置
            char_pos = 0
            for j in range(i):
                if bytes1[j] >= 0x80:
                    char_pos += 1
                char_pos += 1

            # 提取差异字符（尝试用GBK解码）
            expected_char = ""
            actual_char = ""
            try:
                start = max(0, i - 2)
                end = min(len(bytes1), i + 3)
                expected_char = bytes1[start:end].decode('gbk', errors='replace')
                actual_char = bytes2[start:end].decode('gbk', errors='replace')
            except:
                expected_char = hex(bytes1[i]) if i < len(bytes1) else ""
                actual_char = hex(bytes2[i]) if i < len(bytes2) else ""

            return {
                "byte_pos": i,
                "char_pos": char_pos,
                "expected_hex": hex(bytes1[i]) if i < len(bytes1) else "",
                "actual_hex": hex(bytes2[i]) if i < len(bytes2) else "",
                "expected_char": expected_char,
                "actual_char": actual_char
            }

    # 一个是另一个的前缀
    if len(bytes1) != len(bytes2):
        longer = bytes2 if len(bytes2) > len(bytes1) else bytes1
        shorter_len = min(len(bytes1), len(bytes2))
        return {
            "byte_pos": shorter_len,
            "char_pos": shorter_len,
            "expected_hex": f"(长度{len(bytes1)})",
            "actual_hex": f"(长度{len(bytes2)})",
            "expected_char": f"[输出长度差异: 期望{len(bytes1)}字节 vs 实际{len(bytes2)}字节]",
            "actual_char": ""
        }

    return None


def run_preset_comparison(user_exe: str, problem: str) -> List[TestResult]:
    """预设模式：运行用户EXE与预设期望输出比对"""
    # Load demo output JSON
    demo_json_path = DEMORAW_DIR / f"{problem}-demo_output.json"
    if not demo_json_path.exists():
        return []

    with open(demo_json_path, "r", encoding="utf-8") as f:
        demo_data = json.load(f)

    # Load checkdata
    checkdata_path = CHECKDATA_DIR / f"{problem}.txt"
    inputs = []

    if checkdata_path.exists():
        with open(checkdata_path, "r", encoding="utf-8") as f:
            raw_text = f.read()
        inputs = parse_checkdata(raw_text)
    else:
        for tc in demo_data.get("test_cases", []):
            inputs.append((tc.get("case_id", ""), tc.get("input_text", "")))

    results = []
    for case_id, input_val in inputs:
        # Run user exe
        exe_result = run_single_exe(user_exe, input_val)
        actual_text = exe_result["text"]
        actual_hex = exe_result["hex"]

        # Find expected output
        expected_text = ""
        expected_hex = ""
        for tc in demo_data.get("test_cases", []):
            if tc.get("case_id") == case_id:
                expected_hex = tc.get("output_hex", "")
                expected_text = tc.get("output_text", "").strip()
                break

        text_match = (actual_text == expected_text)
        hex_match = (actual_hex == expected_hex)
        status = "PASS" if text_match else "FAIL"

        # Analyze hex diff
        diff_info = None
        if not hex_match:
            diff_info = analyze_hex_diff(expected_hex, actual_hex)

        results.append(TestResult(
            case_id=case_id,
            input_val=input_val,
            expected_text=expected_text,
            actual_text=actual_text,
            expected_hex=expected_hex,
            actual_hex=actual_hex,
            status=status,
            hex_match=hex_match,
            text_match=text_match,
            diff_info=diff_info
        ))

    return results


def run_custom_comparison(demo_exe: str, user_exe: str, checkdata_content: str) -> List[TestResult]:
    """自定义模式：用demo输出作为期望值与user exe输出比对"""
    inputs = parse_checkdata(checkdata_content)

    results = []
    for case_id, input_val in inputs:
        # Run demo exe to get expected output
        demo_result = run_single_exe(demo_exe, input_val)
        expected_text = demo_result["text"]
        expected_hex = demo_result["hex"]

        # Run user exe to get actual output
        user_result = run_single_exe(user_exe, input_val)
        actual_text = user_result["text"]
        actual_hex = user_result["hex"]

        text_match = (actual_text == expected_text)
        hex_match = (actual_hex == expected_hex)
        status = "PASS" if text_match else "FAIL"

        # Analyze hex diff
        diff_info = None
        if not hex_match:
            diff_info = analyze_hex_diff(expected_hex, actual_hex)

        results.append(TestResult(
            case_id=case_id,
            input_val=input_val,
            expected_text=expected_text,
            actual_text=actual_text,
            expected_hex=expected_hex,
            actual_hex=actual_hex,
            status=status,
            hex_match=hex_match,
            text_match=text_match,
            diff_info=diff_info
        ))

    return results
