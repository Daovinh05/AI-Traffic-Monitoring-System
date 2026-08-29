#!/bin/bash

# Script khởi chạy AI Traffic Monitoring Authentication System

echo "🚀 Khởi động AI Traffic Monitoring System..."
echo ""

# Kiểm tra virtual environment
if [ ! -d ".venv" ]; then
    echo "❌ Không tìm thấy virtual environment!"
    echo "Vui lòng chạy: python3 -m venv .venv"
    exit 1
fi

# Kích hoạt virtual environment
echo "✓ Kích hoạt virtual environment..."
source .venv/bin/activate

# Kiểm tra XAMPP MySQL
echo "✓ Kiểm tra MySQL..."
/Applications/XAMPP/xamppfiles/bin/mysql -u root -e "SELECT 1" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "⚠️  XAMPP MySQL chưa chạy!"
    echo "Vui lòng mở XAMPP Control và start MySQL trước."
    echo ""
    echo "Nhấn Enter để tiếp tục hoặc Ctrl+C để hủy..."
    read
fi

# Chạy ứng dụng
echo "🚀 Khởi động ứng dụng..."
echo ""
cd py/Web
python auth_app.py
