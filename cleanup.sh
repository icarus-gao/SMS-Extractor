#!/bin/bash

# SMS Extractor 项目清理脚本
# 用于清理临时文件、缓存等

echo "🧹 开始清理 SMS Extractor 项目..."
echo ""

# 进入项目根目录
cd "$(dirname "$0")"

# 1. 清理 Python 缓存
echo "📦 清理 Python 缓存文件..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo "✓ Python 缓存已清理"

# 2. 清理 macOS 系统文件
echo ""
echo "🍎 清理 macOS 系统文件..."
find . -name ".DS_Store" -delete 2>/dev/null
echo "✓ .DS_Store 文件已清理"

# 3. 清理临时文件
echo ""
echo "🗑️  清理临时文件..."
find . -type f -name "*.tmp" -delete 2>/dev/null
find . -type f -name "*.temp" -delete 2>/dev/null
find . -type f -name "*.bak" -delete 2>/dev/null
find . -type f -name "*~" -delete 2>/dev/null
echo "✓ 临时文件已清理"

# 4. 清理 Django 迁移文件的缓存（可选）
echo ""
echo "🔧 清理 Django 缓存..."
cd sms_backend 2>/dev/null
if [ -f "manage.py" ]; then
    # 清理过期的 session
    python manage.py clearsessions 2>/dev/null && echo "✓ Django sessions 已清理"
fi
cd ..

# 5. 显示清理统计
echo ""
echo "📊 清理完成！"
echo ""
echo "项目大小："
du -sh . 2>/dev/null
echo ""
echo "sms_backend 大小："
du -sh sms_backend 2>/dev/null
echo ""

# 6. 可选：清理测试数据（谨慎使用！）
read -p "❓ 是否清理测试项目数据？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "⚠️  清理测试数据..."
    # 只清理明显的测试项目
    rm -rf sms_backend/data/projects/test* 2>/dev/null
    rm -rf sms_backend/data/projects/1/ 2>/dev/null
    echo "✓ 测试数据已清理"
else
    echo "⏭️  跳过测试数据清理"
fi

echo ""
echo "✅ 清理完成！"
echo ""
echo "💡 提示："
echo "   - 已清理的文件不会影响项目运行"
echo "   - Python 缓存会在下次运行时自动重建"
echo "   - 可以安全地提交清理后的代码到 Git"
echo ""
