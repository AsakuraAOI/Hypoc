"""
外部工具比对逻辑：get_input_data + txt_compare
"""

import re
import json
import tempfile
import os
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


def locate_tools(base_dir: str) -> tuple:
    """
    查找 get_input_data.exe 和 txt_compare.exe。
    优先读 config.json，其次检查 tools/ 目录。
    找不到时抛出 FileNotFoundError。
    """
    # 1. 读 config.json
    config_file = Path(base_dir) / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            gid = cfg.get("get_input_data", "")
            tc = cfg.get("txt_compare", "")
            if gid and tc and Path(gid).exists() and Path(tc).exists():
                return gid, tc
        except Exception:
            pass

    # 2. fallback: tools/ 目录
    tools = Path(base_dir) / "tools"
    gid = tools / "get_input_data.exe"
    tc = tools / "txt_compare.exe"
    if gid.exists() and tc.exists():
        return str(gid), str(tc)

    raise FileNotFoundError("未找到 get_input_data.exe / txt_compare.exe，请点击「配置工具」进行配置")


def save_tools_config(base_dir: str, gid_path: str, tc_path: str):
    """将工具路径保存到 config.json"""
    config_file = Path(base_dir) / "config.json"
    # 保留已有其他配置项
    cfg = {}
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
    cfg["get_input_data"] = gid_path
    cfg["txt_compare"] = tc_path
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def parse_data_file(data_file: str) -> List[str]:
    """解析数据文件，返回所有 case_id 列表（按顺序）"""
    with open(data_file, "r", encoding="gbk", errors="replace") as f:
        content = f.read()
    ids = re.findall(r'\[([^\]]+)\]', content)
    return ids


def group_case_ids(case_ids: List[str]) -> Dict[str, List[str]]:
    """
    按前缀分组。
    例：['4-b1-01','4-b1-02','4-b2-01'] →
        {'4-b1-': ['4-b1-01','4-b1-02'], '4-b2-': ['4-b2-01']}
    如果只有一组，key 为 '全部'。
    """
    groups: Dict[str, List[str]] = {}
    for cid in case_ids:
        m = re.match(r'^(.*?)\d+$', cid)
        prefix = m.group(1) if m else cid
        groups.setdefault(prefix, []).append(cid)
    if len(groups) == 1:
        key = list(groups.keys())[0]
        return {"全部": groups[key]}
    return groups


def _build_tc_args(tc_params: Optional[Dict[str, Any]]) -> List[str]:
    """根据用户选择的 txt_compare 参数构建命令行列表"""
    if not tc_params:
        return []
    args = []
    p = tc_params

    if p.get("trim") and p["trim"] != "none":
        args += ['--trim', p["trim"]]
    if p.get("lineskip", 0) > 0:
        args += ['--lineskip', str(p["lineskip"])]
    if p.get("lineoffset", 0) != 0:
        args += ['--lineoffset', str(p["lineoffset"])]
    if p.get("ignore_blank"):
        args.append('--ignore_blank')
    if p.get("ignore_linefeed"):
        args.append('--ignore_linefeed')
    if p.get("max_diff", 0) > 0:
        args += ['--max_diff', str(p["max_diff"])]
    if p.get("max_line", 0) > 0:
        args += ['--max_line', str(p["max_line"])]

    return args


def run_case_via_pipe(gid_exe: str, data_file: str, case_id: str,
                      target_exe: str, timeout: int = 120) -> bytes:
    """
    两步法：先用 get_input_data 提取输入字节，再作为 stdin 传给 target_exe。
    避免 Windows 上 Popen 管道 EOF 不可靠的问题。
    """
    # Step 1: 提取输入
    try:
        r1 = subprocess.run(
            [gid_exe, data_file, f'[{case_id}]'],
            capture_output=True, timeout=5
        )
        input_bytes = r1.stdout
    except Exception:
        input_bytes = b''

    # Step 2: 运行目标 EXE
    try:
        r2 = subprocess.run(
            [target_exe],
            input=input_bytes,
            capture_output=True,
            timeout=timeout,
            cwd=str(Path(target_exe).parent)
        )
        return r2.stdout
    except subprocess.TimeoutExpired:
        return "[超时]\r\n".encode("gbk")


def prepare_custom_comparison(
    data_file: str,
    case_ids: List[str],
    user_exe: str,
    gid_exe: str,
    tc_exe: str,
    demo_output_file: Optional[str] = None,
    demo_exe: Optional[str] = None,
    tc_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, callable]:
    """
    准备自定义比对：生成临时文件，返回 txt_compare 命令行和清理函数。

    Returns: (cmd_string, cleanup_fn)
      cmd_string: 完整的 txt_compare 命令行（供 PTY 执行）
      cleanup_fn: 调用以删除临时文件
    """
    act_fd, actual_path = tempfile.mkstemp(suffix='.txt')
    os.close(act_fd)

    cleanup_expected = False
    expected_path = None

    with open(actual_path, 'wb') as act_f:
        for cid in case_ids:
            out = run_case_via_pipe(gid_exe, data_file, cid, user_exe)
            act_f.write(out)

    if demo_output_file:
        expected_path = demo_output_file
    else:
        exp_fd, expected_path = tempfile.mkstemp(suffix='.txt')
        os.close(exp_fd)
        cleanup_expected = True
        with open(expected_path, 'wb') as exp_f:
            for cid in case_ids:
                out = run_case_via_pipe(gid_exe, data_file, cid, demo_exe)
                exp_f.write(out)

    tc_args = _build_tc_args(tc_params)
    cmd_parts = [
        tc_exe,
        '--file1', actual_path,
        '--file2', expected_path,
        '--display', 'detailed'
    ] + tc_args

    def cleanup():
        if os.path.exists(actual_path):
            os.unlink(actual_path)
        if cleanup_expected and expected_path and os.path.exists(expected_path):
            os.unlink(expected_path)

    return subprocess.list2cmdline(cmd_parts), cleanup


def run_external_comparison(
    data_file: str,
    case_ids: List[str],
    user_exe: str,
    gid_exe: str,
    tc_exe: str,
    demo_output_file: Optional[str] = None,
    demo_exe: Optional[str] = None,
    tc_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    运行所有 case，对比，返回 txt_compare 的 stdout 文本（用于 CLI 模式）。
    """
    cmd, cleanup = prepare_custom_comparison(
        data_file, case_ids, user_exe, gid_exe, tc_exe,
        demo_output_file, demo_exe, tc_params
    )
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120, shell=True)
        output = result.stdout.decode('gbk', errors='replace')
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr.decode('gbk', errors='replace')
        return output
    finally:
        cleanup()


def prepare_preset_comparison(
    data_file: str,
    case_ids: List[str],
    user_exe: str,
    gid_exe: str,
    tc_exe: str,
    expected_hex_map: Dict[str, str],
    tc_params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, callable]:
    """
    准备预设比对：生成临时文件，返回 txt_compare 命令行和清理函数。

    Returns: (cmd_string, cleanup_fn)
    """
    act_fd, actual_path = tempfile.mkstemp(suffix='.txt')
    exp_fd, expected_path = tempfile.mkstemp(suffix='.txt')
    os.close(act_fd)
    os.close(exp_fd)

    with open(actual_path, 'wb') as act_f, open(expected_path, 'wb') as exp_f:
        for cid in case_ids:
            out = run_case_via_pipe(gid_exe, data_file, cid, user_exe)
            act_f.write(out)
            hex_str = expected_hex_map.get(cid, "")
            if hex_str:
                exp_f.write(bytes.fromhex(hex_str))

    tc_args = _build_tc_args(tc_params)
    cmd_parts = [
        tc_exe,
        '--file1', actual_path,
        '--file2', expected_path,
        '--display', 'detailed'
    ] + tc_args

    def cleanup():
        if os.path.exists(actual_path):
            os.unlink(actual_path)
        if os.path.exists(expected_path):
            os.unlink(expected_path)

    return subprocess.list2cmdline(cmd_parts), cleanup


def run_preset_external_comparison(
    data_file: str,
    case_ids: List[str],
    user_exe: str,
    gid_exe: str,
    tc_exe: str,
    expected_hex_map: Dict[str, str],
    tc_params: Optional[Dict[str, Any]] = None,
) -> str:
    """
    预设模式：期望输出从 JSON 的 output_hex 还原，实际输出通过 get_input_data | user_exe 生成。
    返回 txt_compare stdout 文本（用于 CLI 模式）。
    """
    cmd, cleanup = prepare_preset_comparison(
        data_file, case_ids, user_exe, gid_exe, tc_exe,
        expected_hex_map, tc_params
    )
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120, shell=True)
        output = result.stdout.decode('gbk', errors='replace')
        if result.stderr:
            output += "\n[stderr]\n" + result.stderr.decode('gbk', errors='replace')
        return output
    finally:
        cleanup()
