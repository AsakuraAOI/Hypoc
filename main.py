import flet as ft
from flet import Padding
import subprocess
import json
import os
from pathlib import Path


class Theme:
    BG_LIGHT = "#F5F5F5"
    BG_GLASS = "rgba(0, 0, 0, 0.05)"
    BORDER_GLASS = "rgba(0, 0, 0, 0.15)"
    TEXT_PRIMARY = "#1A1A1A"
    TEXT_SECONDARY = "#666666"
    ACCENT = "#2563EB"
    ACCENT_HOVER = "#1D4ED8"
    SUCCESS = "#22C55E"
    ERROR = "#EF4444"


def glass_card(content, padding=20):
    return ft.Container(
        content=content,
        padding=padding,
        border_radius=20,
        bgcolor=Theme.BG_GLASS,
        border=ft.Border.all(1, Theme.BORDER_GLASS),
        blur=20,
    )


def page_header(title: str, subtitle: str = ""):
    return ft.Column([
        ft.Text(title, size=32, weight=ft.FontWeight.W_700, color=Theme.TEXT_PRIMARY),
        ft.Text(subtitle, size=14, color=Theme.TEXT_SECONDARY),
    ], spacing=4)


def main(page: ft.Page):
    page.title = "HyperField Lite"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0

    # State
    exe_path = [""]  # Using list to allow mutation in nested function
    problem_select = ft.Dropdown()
    results_container = ft.ListView(expand=True, spacing=8, padding=10)
    status_text = ft.Text("", color=Theme.TEXT_SECONDARY, size=13)
    is_running = [False]
    exe_name = ft.Text("未选择文件", color=Theme.TEXT_SECONDARY, size=14)
    current_results = [{}]

    # File picker
    file_picker = ft.FilePicker()

    # Hardcoded problem list (maps to demo_output.json in data/demoraw)
    DATA_DIR = Path(__file__).parent / "data"
    demoraw_dir = DATA_DIR / "demoraw"
    checkdata_dir = DATA_DIR / "checkdata"

    PROBLEMS = [
        "3-b5", "3-b7", "3-b8", "3-b9",
        "3-b10", "3-b12-1", "3-b13-1", "3-b13-2",
        "4-b1", "4-b2", "4-b3",
        "4-b5", "4-b6", "4-b7", "4-b8", "4-b9",
        "4-b10", "4-b11", "4-b12", "4-b13", "4-b14",
        "5-b8", "5-b9", "5-b10",
        "5-b15", "5-b16", "5-b17", "5-b18",
        "6-b1", "6-b2", "6-b3",
    ]

    problems = [ft.dropdown.Option(name, name) for name in PROBLEMS]

    # UI Elements
    problem_dropdown = ft.Dropdown(
        options=problems if problems else [ft.dropdown.Option("未找到问题", "none")],
        value=problems[0].key if problems else "none",
        border_color=Theme.BORDER_GLASS,
        color=Theme.TEXT_PRIMARY,
        bgcolor=Theme.BG_GLASS,
        border_radius=12,
        height=50,
        width=300,
    )

    async def pick_exe_click(e):
        if is_running[0]:
            return
        result = await file_picker.pick_files(
            dialog_title="选择 EXE 文件",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["exe"],
        )
        if result and len(result) > 0:
            import os
            # Get full path - os.path.abspath handles short path names
            exe_path[0] = os.path.abspath(result[0].path)
            exe_name.value = result[0].name
            exe_name.update()

    def run_comparison(e):
        if is_running[0]:
            return
        if not exe_path[0]:
            status_text.value = "请先选择 EXE 文件"
            status_text.color = Theme.ERROR
            status_text.update()
            return

        problem = problem_dropdown.value
        if not problem or problem == "none":
            status_text.value = "请先选择问题"
            status_text.color = Theme.ERROR
            status_text.update()
            return

        is_running[0] = True
        status_text.value = "运行中..."
        status_text.color = Theme.ACCENT
        status_text.update()
        results_container.controls.clear()
        results_container.update()

        try:
            # Load demo output JSON
            demo_json_path = demoraw_dir / f"{problem}-demo_output.json"
            if not demo_json_path.exists():
                status_text.value = f"未找到演示输出: {demo_json_path}"
                status_text.color = Theme.ERROR
                status_text.update()
                is_running[0] = False
                return

            with open(demo_json_path, "r", encoding="utf-8") as f:
                demo_data = json.load(f)

            # Load checkdata (input file) - 支持无输入程序
            checkdata_path = checkdata_dir / f"{problem}.txt"
            inputs = []

            if checkdata_path.exists():
                # Parse input file - 支持多行输入
                with open(checkdata_path, "r", encoding="utf-8") as f:
                    raw_text = f.read()
                lines = raw_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
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
                                i -= 1  # Decrement so outer loop's increment doesn't skip the bracket
                                break
                            if next_line:
                                input_lines.append(next_line)
                            i += 1
                        inputs.append((case_id, '\n'.join(input_lines)))
                    else:
                        i += 1
            else:
                # 无checkdata时，直接使用demo_data中的测试用例
                for tc in demo_data.get("test_cases", []):
                    inputs.append((tc.get("case_id", ""), tc.get("input_text", "")))

            # Run user exe with each input
            results_data = []

            def run_one_case(case_id, input_val):
                try:
                    if not os.path.exists(exe_path[0]):
                        return {
                            "case_id": case_id,
                            "input": input_val,
                            "expected_hex": "",
                            "expected_text": "",
                            "actual_hex": "",
                            "actual_text": f"[错误: exe文件不存在 {exe_path[0]}]",
                            "status": "FAIL",
                            "hex_match": False,
                            "text_match": False,
                        }

                    proc = subprocess.run(
                        [exe_path[0]],
                        input=(input_val + "\n").encode("utf-8"),
                        capture_output=True,
                        timeout=5,
                        cwd=str(Path(exe_path[0]).parent),
                    )
                    raw_output = proc.stdout
                    stderr_output = proc.stderr
                    user_hex = raw_output.hex() if raw_output else ""
                    user_text = raw_output.decode("gbk", errors="replace").strip()
                    user_stderr = stderr_output.decode("utf-8", errors="replace").strip() if stderr_output else ""

                    # Find expected output from demo_data
                    expected_hex = ""
                    expected_text = ""
                    for tc in demo_data.get("test_cases", []):
                        if tc.get("case_id") == case_id:
                            expected_hex = tc.get("output_hex", "")
                            expected_text = tc.get("output_text", "").strip()
                            break

                    hex_match = (user_hex == expected_hex)
                    text_match = (user_text == expected_text)

                    # PASS: hex same, PARTIAL: text same but hex different, FAIL: neither same
                    if hex_match:
                        status = "PASS"
                    elif text_match:
                        status = "PARTIAL"  # encoding wrong
                    else:
                        status = "FAIL"

                    return {
                        "case_id": case_id,
                        "input": input_val,
                        "expected_hex": expected_hex,
                        "expected_text": expected_text,
                        "actual_hex": user_hex,
                        "actual_text": user_text if user_text else f"[空输出] (returncode={proc.returncode}, stderr={user_stderr[:50] if user_stderr else 'none'})",
                        "status": status,
                        "hex_match": hex_match,
                        "text_match": text_match,
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "case_id": case_id,
                        "input": input_val,
                        "expected_hex": "",
                        "expected_text": "",
                        "actual_hex": "",
                        "actual_text": "[超时]",
                        "status": "FAIL",
                        "hex_match": False,
                        "text_match": False,
                    }
                except Exception as ex:
                    return {
                        "case_id": case_id,
                        "input": input_val,
                        "expected_hex": "",
                        "expected_text": "",
                        "actual_hex": "",
                        "actual_text": f"[错误: {str(ex)}]",
                        "status": "FAIL",
                        "hex_match": False,
                        "text_match": False,
                    }

            for case_id, input_val in inputs:
                result = run_one_case(case_id, input_val)
                results_data.append(result)

                # Determine status display
                status = result["status"]
                if status == "PASS":
                    status_icon = ft.icons.Icons.CHECK_CIRCLE
                    status_color = Theme.SUCCESS
                elif status == "PARTIAL":
                    status_icon = ft.icons.Icons.WARNING
                    status_color = "#F59E0B"  # amber
                else:
                    status_icon = ft.icons.Icons.ERROR
                    status_color = Theme.ERROR

                result_card = glass_card(
                    ft.Column([
                        ft.Row([
                            ft.Container(
                                ft.Icon(status_icon, color=status_color, size=18),
                            ),
                            ft.Text(f"#{case_id}", weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY, size=14),
                            ft.Text(f"输入: {input_val}", color=Theme.TEXT_SECONDARY, size=12),
                            ft.Container(
                                ft.Text(status, size=11, color=status_color, weight=ft.FontWeight.W_600),
                                padding=Padding.only(left=8, right=8, top=2, bottom=2),
                                bgcolor="rgba(0,0,0,0.1)",
                                border_radius=8,
                            ),
                        ], spacing=8),
                        ft.Container(
                            ft.Column([
                                ft.Text("期望 (HEX):", color=Theme.TEXT_SECONDARY, size=11),
                                ft.Text(result["expected_hex"], color=Theme.TEXT_PRIMARY, size=11, selectable=True),
                                ft.Text("实际 (HEX):", color=Theme.TEXT_SECONDARY, size=11),
                                ft.Text(result["actual_hex"], color=Theme.TEXT_PRIMARY, size=11, selectable=True),
                                ft.Container(height=4),
                                ft.Text("期望:", color=Theme.TEXT_SECONDARY, size=11),
                                ft.Text(result["expected_text"], color=Theme.SUCCESS if status == "PASS" else Theme.TEXT_PRIMARY, size=12),
                                ft.Text("实际:", color=Theme.TEXT_SECONDARY, size=11),
                                ft.Text(result["actual_text"], color=Theme.ERROR if status == "FAIL" else Theme.SUCCESS if status == "PASS" else "#F59E0B", size=12),
                            ], spacing=2),
                            padding=10,
                            bgcolor="rgba(0,0,0,0.2)",
                            border_radius=8,
                        ),
                    ], spacing=8),
                    padding=12,
                )
                results_container.controls.append(result_card)
                results_container.update()

            current_results[0] = {
                "problem": problem,
                "exe": exe_path[0],
                "results": results_data,
            }

            passed = sum(1 for r in results_data if r["status"] == "PASS")
            partial = sum(1 for r in results_data if r["status"] == "PARTIAL")
            failed = sum(1 for r in results_data if r["status"] == "FAIL")
            total = len(results_data)

            if failed == 0 and partial == 0:
                status_text.value = f"完成: {passed}/{total} 通过 ✓"
                status_text.color = Theme.SUCCESS
            elif failed == 0:
                status_text.value = f"完成: {passed}/{total} 通过, {partial} 基本通过 ⚠"
                status_text.color = "#F59E0B"
            else:
                status_text.value = f"完成: {passed}/{total} 通过, {partial} 基本通过, {failed} 失败 ✗"
                status_text.color = Theme.ERROR
            status_text.update()

        except Exception as ex:
            status_text.value = f"错误: {str(ex)}"
            status_text.color = Theme.ERROR
            status_text.update()
        finally:
            is_running[0] = False

    # Main layout
    page.add(
        ft.Container(
            content=ft.Column([
                # Header / Nav bar
                glass_card(
                    ft.Row([
                        ft.Text("HyperField", size=22, weight=ft.FontWeight.W_700, color=Theme.TEXT_PRIMARY),
                        ft.Text("Lite", size=14, color=Theme.ACCENT, weight=ft.FontWeight.W_500),
                    ]),
                    padding=Padding.only(left=24, right=24, top=16, bottom=16),
                ),
                # Main content
                ft.Container(
                    content=ft.Column([
                        # Config section
                        glass_card(
                            ft.Column([
                                page_header("导入 EXE", "选择你的程序进行测试"),
                                ft.Container(height=20),
                                ft.Row([
                                    ft.Column([
                                        ft.Text("程序文件", color=Theme.TEXT_SECONDARY, size=12),
                                        ft.Row([
                                            ft.Button(
                                                "选择文件",
                                                icon=ft.icons.Icons.FOLDER_OPEN,
                                                on_click=pick_exe_click,
                                                style=ft.ButtonStyle(
                                                    bgcolor=Theme.ACCENT,
                                                    color=ft.Colors.WHITE,
                                                ),
                                            ),
                                            exe_name,
                                        ], spacing=12),
                                    ], spacing=4),
                                    ft.Column([
                                        ft.Text("问题", color=Theme.TEXT_SECONDARY, size=12),
                                        problem_dropdown,
                                    ], spacing=4),
                                    ft.Column([
                                        ft.Text("", size=12),  # spacer
                                        ft.Button(
                                            "开始测试",
                                            icon=ft.icons.Icons.PLAY_ARROW,
                                            on_click=run_comparison,
                                            style=ft.ButtonStyle(
                                                bgcolor=Theme.ACCENT,
                                                color=ft.Colors.WHITE,
                                            ),
                                        ),
                                    ], spacing=4),
                                ], spacing=32, alignment=ft.MainAxisAlignment.START),
                                ft.Container(height=16),
                                status_text,
                            ], spacing=0),
                            padding=24,
                        ),
                        # Results section
                        ft.Container(
                            content=ft.Column([
                                ft.Row([
                                    ft.Text("测试结果", size=18, weight=ft.FontWeight.W_600, color=Theme.TEXT_PRIMARY),
                                ]),
                                ft.Container(
                                    content=results_container,
                                    expand=True,
                                    height=400,
                                ),
                            ], spacing=12),
                            padding=24,
                            expand=True,
                        ),
                    ], spacing=24),
                    padding=24,
                    expand=True,
                ),
            ], spacing=0),
            expand=True,
            bgcolor=Theme.BG_LIGHT,
        ),
    )


if __name__ == "__main__":
    ft.run(main)
