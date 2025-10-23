#!/bin/bash
# 脚本用于更新本地代码并验证改动

echo "========================================"
echo "更新代码并验证改动"
echo "========================================"
echo ""

# 1. 检查当前分支
echo "1. 检查当前分支..."
current_branch=$(git branch --show-current)
echo "   当前分支: $current_branch"

if [ "$current_branch" != "claude/add-patient-notes-011CUQf8Z1WAMEatkrhSZgqq" ]; then
    echo "   ⚠️  警告: 当前不在正确的分支上"
    echo "   正在切换到正确的分支..."
    git checkout claude/add-patient-notes-011CUQf8Z1WAMEatkrhSZgqq
fi
echo ""

# 2. 拉取最新代码
echo "2. 拉取最新代码..."
git pull origin claude/add-patient-notes-011CUQf8Z1WAMEatkrhSZgqq
echo ""

# 3. 检查最新commit
echo "3. 最近的提交记录:"
git log --oneline -5
echo ""

# 4. 验证Patient Notes功能
echo "4. 验证Patient Notes功能..."
if grep -q "### 📝 Patient Notes" app.py; then
    echo "   ✅ Patient Notes 功能存在 (行号 $(grep -n "### 📝 Patient Notes" app.py | cut -d: -f1))"
else
    echo "   ❌ Patient Notes 功能不存在"
fi
echo ""

# 5. 验证文件上传功能
echo "5. 验证文件上传功能..."
if grep -q "### 📎 Attach Files to Chat" app.py; then
    echo "   ✅ 文件上传功能存在 (行号 $(grep -n "### 📎 Attach Files to Chat" app.py | cut -d: -f1))"
else
    echo "   ❌ 文件上传功能不存在"
fi
echo ""

# 6. 检查app.py修改时间
echo "6. app.py 文件信息:"
ls -lh app.py | awk '{print "   修改时间:", $6, $7, $8}'
echo "   文件大小: $(ls -lh app.py | awk '{print $5}')"
echo ""

echo "========================================"
echo "验证完成！"
echo "========================================"
echo ""
echo "如果所有检查都通过，请："
echo "1. 停止当前运行的 streamlit (Ctrl+C)"
echo "2. 重新启动: streamlit run app.py"
echo "3. 在浏览器中硬刷新: Ctrl+Shift+R (Windows) 或 Cmd+Shift+R (Mac)"
echo ""
