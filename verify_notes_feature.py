#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
验证 Patient Notes 功能是否已添加到代码中
"""

import re

def verify_notes_feature():
    """检查 app.py 中是否包含 Patient Notes 功能"""

    print("=" * 60)
    print("验证 Patient Notes 功能")
    print("=" * 60)
    print()

    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')

    checks = {
        '✅ 笔记标题': False,
        '✅ 保存功能': False,
        '✅ 清除功能': False,
        '✅ 笔记管理函数': False,
        '✅ AI集成(add_patient_chat)': False,
        '✅ AI集成(generate_patient_response)': False
    }

    # 检查1: 笔记标题
    if '### 📝 Patient Notes' in content:
        checks['✅ 笔记标题'] = True
        # 找到行号
        for i, line in enumerate(lines, 1):
            if '### 📝 Patient Notes' in line:
                print(f"✅ 笔记标题找到 (行号: {i})")
                print(f"   {lines[i-1].strip()}")
                break

    # 检查2: 保存功能
    if 'Save Notes' in content and 'update_patient_notes' in content:
        checks['✅ 保存功能'] = True
        print("✅ 保存功能存在 (💾 Save Notes)")

    # 检查3: 清除功能
    if 'Clear Notes' in content:
        checks['✅ 清除功能'] = True
        print("✅ 清除功能存在 (🗑️ Clear Notes)")

    # 检查4: 笔记管理函数
    functions = ['load_patient_notes', 'save_patient_notes',
                 'get_patient_notes', 'update_patient_notes']
    all_found = all(func in content for func in functions)
    if all_found:
        checks['✅ 笔记管理函数'] = True
        print("✅ 笔记管理函数完整:")
        for func in functions:
            for i, line in enumerate(lines, 1):
                if f'def {func}' in line:
                    print(f"   - {func}() (行号: {i})")
                    break

    # 检查5: AI集成 - add_patient_chat
    if 'def add_patient_chat' in content:
        # 查找函数内是否调用了 get_patient_notes
        func_start = content.find('def add_patient_chat')
        next_func = content.find('\ndef ', func_start + 1)
        func_content = content[func_start:next_func]

        if 'get_patient_notes' in func_content and 'Additional Notes' in func_content:
            checks['✅ AI集成(add_patient_chat)'] = True
            print("✅ AI集成已添加到 add_patient_chat()")

    # 检查6: AI集成 - generate_patient_response
    if 'def generate_patient_response' in content:
        func_start = content.find('def generate_patient_response')
        next_func = content.find('\ndef ', func_start + 1)
        func_content = content[func_start:next_func]

        if 'get_patient_notes' in func_content and 'Additional Clinical Notes' in func_content:
            checks['✅ AI集成(generate_patient_response)'] = True
            print("✅ AI集成已添加到 generate_patient_response()")

    print()
    print("=" * 60)
    print("检查结果:")
    print("=" * 60)

    all_passed = all(checks.values())

    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check.replace('✅ ', '')}")

    print()
    if all_passed:
        print("🎉 所有检查通过！Patient Notes 功能已完整添加！")
    else:
        print("⚠️ 部分检查未通过，请检查代码")

    print()
    print("=" * 60)
    print("代码位置信息:")
    print("=" * 60)

    # 显示笔记部分的代码片段
    for i, line in enumerate(lines, 1):
        if '### 📝 Patient Notes' in line:
            print(f"\n从第 {i} 行开始的代码片段:\n")
            for j in range(max(0, i-2), min(len(lines), i+15)):
                print(f"{j+1:4d}: {lines[j]}")
            break

    return all_passed

if __name__ == "__main__":
    verify_notes_feature()
