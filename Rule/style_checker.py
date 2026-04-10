"""
C++ 代码格式检查器
检查规则基于 rules.md
"""

import re
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class StyleError:
    """格式错误"""
    line: int          # 行号（从1开始）
    column: int        # 列号（从0开始）
    severity: str      # "error" | "warning" | "critical"
    code: str          # 错误代码
    message: str       # 人类可读描述


def check_style(code: str) -> List[StyleError]:
    """
    检查C++代码格式

    Args:
        code: C++源代码字符串

    Returns:
        StyleError列表
    """
    lines = code.splitlines()
    errors: List[StyleError] = []

    # 状态跟踪
    in_block_comment = False
    in_string = False  # 简单跟踪：只考虑单行内的字符串
    brace_stack: List[Tuple[str, int]] = []  # 栈追踪大括号层级 (brace_type, expected_indent)

    # 新增状态变量
    switch_base_indent = None  # switch的基础缩进
    case_base_indent = None  # case的基础缩进
    in_do_block = False  # 是否在do-while块中
    prev_line_had_open_brace = False  # 上一行是否有 {
    prev_line_had_close_brace = False  # 上一行是否有 }
    prev_line_was_control_no_brace = False  # 上一行是否是无大括号的控制语句
    in_multi_line_condition = False  # 当前是否在多行条件语句的延续行中
    skip_next_line = False  # 下一行是否需要跳过NESTED_INDENT检查

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.lstrip()
        # tab按4空格处理
        leading_spaces = line[:len(line) - len(stripped)]
        indent = leading_spaces.expandtabs(4).__len__()

        # 简单字符串检测（不考虑转义，只用于本行）
        in_string_this_line = False
        for j, c in enumerate(stripped):
            if c == '"':
                in_string_this_line = not in_string_this_line

        # 检测行内注释开始
        comment_start = stripped.find('//')
        content_before_comment = stripped
        if comment_start != -1 and not in_string_this_line:
            content_before_comment = stripped[:comment_start]

        # ========== 逐项检查 ==========

        # 0. 检测是否在多行条件延续行中（用于跳过NESTED_INDENT检查）
        skip_nested_for_multi_line = in_multi_line_condition or skip_next_line

        # 1. 检测本行是否是多行条件的开始
        line_starts_multi_line = False
        if re.match(r'(if|while|for|switch)\s*\(', stripped):
            # 检查条件是否在同一行结束
            if not stripped.rstrip().endswith(')'):
                in_multi_line_condition = True
                line_starts_multi_line = True

        # 2. 多行条件结束时：行尾有 ) 且下一行不是条件延续
        condition_ended_this_line = False
        if in_multi_line_condition and stripped.rstrip().endswith(')'):
            # 检查下一行是否是条件延续（以 || 或 && 开头）
            if i + 1 < len(lines):
                next_stripped = lines[i + 1].strip()
                if not (next_stripped.startswith('||') or next_stripped.startswith('&&')):
                    condition_ended_this_line = True
            else:
                condition_ended_this_line = True

        # 条件结束后，重置 in_ml 状态，并标记下一行需要跳过
        if condition_ended_this_line:
            in_multi_line_condition = False
            skip_next_line = True
        else:
            skip_next_line = False

        # 1. 检查缩进（如果是非空行）
        if stripped and not stripped.startswith('//'):
            # 缩进必须是4的倍数
            if indent % 4 != 0:
                errors.append(StyleError(
                    line=i + 1,
                    column=0,
                    severity="warning",
                    code="INDENT_4SPACE",
                    message=f"缩进必须是4的倍数，当前缩进{indent}格"
                ))

        # 1b. 检查嵌套缩进层级（Rules 5, 9, 10, 12）
        # 只在brace_stack深度>=2时检查（顶层代码块如main内部）
        # 跳过无大括号控制语句后的下一行（单语句格式）
        # 跳过case块内的语句（由CASE_STMT_INDENT检查）
        # 跳过 if/while/for/switch/do 右括号开始的行（下一行才是内容缩进）
        # 跳过多行条件延续行
        if stripped and not stripped.startswith('//') and brace_stack and len(brace_stack) >= 2 and not prev_line_was_control_no_brace and not skip_nested_for_multi_line and not line_starts_multi_line:
            # 跳过case块内的语句
            if case_base_indent is not None and indent > case_base_indent:
                pass  # 由CASE_STMT_INDENT检查
            else:
                _, expected_indent = brace_stack[-1]
                # 排除case、default、空行、纯括号行
                if not stripped.startswith('case ') and not stripped.startswith('default'):
                    if not stripped.startswith('{') and not stripped.startswith('}'):
                        # 跳过 if/while/for/switch 条件换行后的内容行
                        # 这些行的缩进由后续的 { 缩进规则检查
                        if re.match(r'(if|while|for|switch)\s*\(', stripped):
                            pass
                        elif indent != expected_indent:
                            errors.append(StyleError(
                                line=i + 1,
                                column=0,
                                severity="warning",
                                code="NESTED_INDENT",
                                message=f"嵌套块缩进应为{expected_indent}格，当前{indent}格"
                            ))

        # 2. 检查一行多条语句
        if content_before_comment.strip() and ';' in content_before_comment:
            # 统计分号数量（排除字符串内的，处理转义引号）
            in_str_check = False
            j = 0
            while j < len(content_before_comment):
                c = content_before_comment[j]
                if c == '"' and not in_str_check:
                    in_str_check = True
                elif c == '"' and in_str_check:
                    # 检查是否是转义引号
                    if j > 0 and content_before_comment[j-1] == '\\':
                        # 转义引号，不切换状态
                        pass
                    else:
                        in_str_check = False
                j += 1

            if ';' in content_before_comment and not in_str_check:
                # 检查是否有 } { 这种配对符号干扰
                # 特殊情况：for循环括号内的分号不算语句分隔符
                content = content_before_comment.strip()
                is_for_loop = content.startswith('for')

                # 找出for循环的括号范围
                for_paren_end = -1
                if is_for_loop:
                    paren_match = re.search(r'for\s*\([^)]*\)', content)
                    if paren_match:
                        for_paren_end = paren_match.end()

                # 按分号分割，但排除for循环括号内的分号
                parts = []
                current_part = ''
                for j, c in enumerate(content):
                    if c == ';':
                        if is_for_loop and j < for_paren_end:
                            current_part += c
                        else:
                            parts.append(current_part)
                            current_part = ''
                    else:
                        current_part += c
                if current_part:
                    parts.append(current_part)

                meaningful_parts = [p.strip() for p in parts if p.strip()
                                   and not p.strip().startswith('//')
                                   and not p.strip().startswith('{')
                                   and not p.strip().startswith('}')]

                if len(meaningful_parts) > 1:
                    # 允许多重for循环的初始化部分
                    is_multi_for = is_for_loop and ';' in content[for_paren_end:]
                    if not is_multi_for:
                        errors.append(StyleError(
                            line=i + 1,
                            column=0,
                            severity="warning",
                            code="MULTIPLE_STMTS",
                            message=f"一行不应有多条语句"
                        ))

        # 3. 检查左大括号位置
        lbrace_match = re.search(r'\{', content_before_comment)
        if lbrace_match:
            brace_pos = lbrace_match.start()
            # 左大括号可以紧跟关键字或单独一行
            # 检查是否在关键字后直接跟{，还是{单独一行
            before_brace = content_before_comment[:brace_pos].rstrip()
            if before_brace:
                # 检查是否是 if (xxx) { 这种格式
                if not re.match(r'(if|while|for|switch|do)\s*$', before_brace) and \
                   not re.match(r'(if|while|for|switch|do)\s*\([^)]*\)$', before_brace):
                    # 不是紧跟关键字的情况，检查是否单独一行
                    pass

            # 3b. 检查左大括号后是否有语句（Rules 1-5）
            after_brace = content_before_comment[brace_pos+1:].strip()
            keyword_match = re.match(r'(if|while|for|switch|do)\s*\([^)]*\)\s*$', before_brace)
            if after_brace and not after_brace.startswith('//'):
                # { 后有内容，检查是否是正确的 { 紧跟关键字格式
                if not keyword_match:
                    # 不是紧跟关键字的情况，违规
                    errors.append(StyleError(
                        line=i + 1,
                        column=brace_pos,
                        severity="warning",
                        code="LBRACE_SAME_LINE_STATEMENT",
                        message=f"左大括号后不应有其他语句"
                    ))

        # 4. 检查右大括号单独一行
        rbrace_match = re.search(r'\}', content_before_comment)
        if rbrace_match:
            brace_content = content_before_comment.strip()
            # 右大括号应该单独一行，或者只跟分号/注释
            # 但 } while(...); 是do-while的正确格式
            after_brace = brace_content[brace_content.find('}')+1:].strip()
            if after_brace and not after_brace.startswith('//'):
                # } while(...); 是do-while，正确
                if re.match(r'while\s*\(', after_brace):
                    pass  # do-while格式，正确
                elif after_brace.startswith(';'):
                    pass  # } ; 正确
                else:
                    errors.append(StyleError(
                        line=i + 1,
                        column=0,
                        severity="warning",
                        code="RBRACE_LINE",
                        message=f"右大括号后不应有其他语句"
                    ))

        # 5. 检查 if/while/for/switch 后直接跟语句不换行
        control_pattern = re.match(r'(if|while|for|switch)\s*\([^)]*\)\s*(.*)', content_before_comment)
        if control_pattern:
            after_condition = control_pattern.group(2).strip()
            if after_condition and after_condition != '{':
                # if (...) 语句; 的格式是错误的
                if not after_condition.startswith('//'):
                    errors.append(StyleError(
                        line=i + 1,
                        column=0,
                        severity="warning",
                        code="CONTROL_STMT_SAME_LINE",
                        message=f"控制语句后的语句必须换行"
                    ))
            elif not after_condition:
                # if (...) 后面没有内容（换行单语句），标记状态
                prev_line_was_control_no_brace = True
        # 检测多行条件：if/while/for/switch ( 后面没有 ) 在同一行
        elif re.match(r'(if|while|for|switch)\s*\(', stripped) and '(' in stripped:
            # 检查条件是否在同一行结束
            # 简单检测：如果行中有 ( 但没有 ) 结尾，则为多行条件
            open_count = stripped.count('(') - stripped.count(')')
            if open_count > 0 or (not stripped.rstrip().endswith(')')):
                in_multi_line_condition = True

        # 如果在多行条件中，检查是否结束
        if in_multi_line_condition:
            # 多行条件结束时（行尾有 ）），重置状态
            if stripped.rstrip().endswith(')'):
                in_multi_line_condition = False
            # 跳过缩进检查（continuation lines 和下一行语句应该与条件起始行同缩进）
            if not stripped.startswith('//'):
                prev_line_was_control_no_brace = True

        # 6. 检查 switch/case 格式（增强版）
        switch_match = re.match(r'switch\s*\(', content_before_comment)
        if switch_match:
            switch_base_indent = indent
            case_base_indent = indent + 4  # case应该比switch多4格

        case_match = re.search(r'case\s+', content_before_comment)
        if case_match:
            # case 必须缩进4格（相对于switch）
            if switch_base_indent is not None:
                expected_case_indent = switch_base_indent + 4
                if indent != expected_case_indent:
                    errors.append(StyleError(
                        line=i + 1,
                        column=0,
                        severity="error",
                        code="CASE_INDENT",
                        message=f"case必须缩进4格（相对于switch）"
                    ))
            case_base_indent = indent
            # case 后只应该有冒号，不应跟任何语句
            after_case = content_before_comment[case_match.end():].strip()
            # case 1: 后面只能是冒号，可能有空格和注释
            if after_case and not re.match(r'\d+\s*:(\s*$|//)', after_case) and \
               not re.match(r'\d+\s*:$', after_case):
                errors.append(StyleError(
                    line=i + 1,
                    column=0,
                    severity="error",
                    code="CASE_STMT_SAME_LINE",
                    message=f"case后必须换行再写语句"
                ))

        # 6b. 检查case下的语句缩进（Rule 6）
        # 语句必须在case基础上再缩进4格，允许更深嵌套
        if case_base_indent is not None and indent > case_base_indent:
            if stripped and not stripped.startswith('case ') and \
               not stripped.startswith('default:') and \
               not stripped.startswith('break') and \
               not stripped.startswith('}'):
                expected_stmt_indent = case_base_indent + 4
                if indent < expected_stmt_indent:
                    errors.append(StyleError(
                        line=i + 1,
                        column=0,
                        severity="warning",
                        code="CASE_STMT_INDENT",
                        message=f"case下的语句必须缩进4格（相对于case）"
                    ))

        # 7. 检查 do-while 格式（增强版）
        # 匹配 do { ... } while(...); 正确格式
        do_block_match = re.match(r'do\s*\{', content_before_comment)
        # 匹配 do statement; while(...); 错误格式
        do_single_match = re.match(r'do\s+[^;]+;\s*while\s*\(', content_before_comment)
        if do_single_match:
            # do 单语句没有大括号，是错误的
            errors.append(StyleError(
                line=i + 1,
                column=0,
                severity="warning",
                code="DO_WHILE_SINGLE_NO_BRACE",
                message=f"do-while循环即使单语句也必须使用大括号"
            ))
            in_do_block = True
        elif do_block_match:
            in_do_block = True

        # 检查 } while(...); 格式
        dowhile_match = re.match(r'\}\s*while\s*\([^)]*\)\s*;?\s*$', content_before_comment)
        if dowhile_match:
            # 右大括号后直接跟 while，不应有其他内容
            before_while = content_before_comment[:content_before_comment.find('}')].strip()
            if before_while and not before_while.endswith('{'):
                in_do_block = False  # 正常格式，do-while结束

        # 8. 检查空语句（循环后的单独分号）（增强版）
        empty_stmt_patterns = [
            (r'while\s*\([^)]*\)\s*;\s*$', 'while'),
            (r'for\s*\([^)]*\)\s*;\s*$', 'for'),
        ]
        for pattern, keyword in empty_stmt_patterns:
            if re.match(pattern, content_before_comment):
                errors.append(StyleError(
                    line=i + 1,
                    column=0,
                    severity="warning",
                    code="EMPTY_STMT_SAME_LINE",
                    message=f"空语句的分号必须单独一行"
                ))

        # 9. 打表输出检测（严重违规）
        # 检测 cout << 数字常量 或 printf("数字")
        table_output_patterns = [
            r'cout\s*<<\s*[-+]?\d+\.?\d*',  # cout << 123
            r'cout\s*<<\s*"[^"]*[-+]?\d+\.?\d*"',  # cout << "123"
            r'printf\s*\(\s*"[^"]*[-+]?\d+\.?\d*"',  # printf("123"
        ]
        for pattern in table_output_patterns:
            if re.search(pattern, content_before_comment):
                # 排除明显的变量输出
                if not re.search(r'cout\s*<<\s*(a|b|c|x|y|i|j|k|n|m|result|sum|avg|count)\b', content_before_comment, re.IGNORECASE):
                    errors.append(StyleError(
                        line=i + 1,
                        column=0,
                        severity="critical",
                        code="TABLE_OUTPUT",
                        message=f"禁止打表输出（直接输出计算结果）"
                    ))

        # 10. 大括号配对追踪（增强版）
        open_braces = content_before_comment.count('{')
        close_braces = content_before_comment.count('}')
        if not in_string and not in_block_comment:
            # 处理左大括号
            for match in re.finditer(r'\{', content_before_comment):
                brace_pos = match.start()
                before_brace = content_before_comment[:brace_pos].strip()

                # 确定大括号类型
                brace_type = 'block'
                if re.match(r'(if|while|for|switch)\s*\([^)]*\)\s*$', before_brace):
                    brace_type = before_brace.split()[0]
                elif re.match(r'(else|do)\s*$', before_brace):
                    brace_type = before_brace.split()[0]

                # 计算期望缩进
                # 控制语句的 { 在同一行，如 for (...) { ，内容缩进 = 当前行缩进 + 4
                # 普通块的 { 也在同一行，如 class Foo { ，内容缩进 = 当前行缩进 + 4
                # 两者都是内容缩进 = indent + 4
                expected_indent = indent + 4

                brace_stack.append((brace_type, expected_indent))
                prev_line_had_open_brace = True

            # 处理右大括号 - pop栈
            for _ in range(close_braces):
                if brace_stack:
                    brace_stack.pop()
                    prev_line_had_close_brace = True

        # 重置无大括号控制语句标记（只在有空行或后续行时保持状态）
        # 该标记在遇到正确缩进的下一行时会被重置
        if stripped:  # 如果当前行不是空行
            prev_line_was_control_no_brace = False

        i += 1

    return errors


if __name__ == "__main__":
    # 测试代码
    test_code = '''
#include <iostream>
using namespace std;

int main()
{
    int a;
    a=10;
    cout << 3.14 << endl;

    return 0;
}
'''

    errors = check_style(test_code)
    for e in errors:
        print(f"Line {e.line}: [{e.severity}] {e.message} ({e.code})")
