#!/bin/bash
# 單一學生評分腳本

if [ $# -lt 1 ]; then
    echo "使用方式: ./run_single_student.sh <學號> [姓名]"
    echo "範例: ./run_single_student.sh B11276001 林芷綺"
    exit 1
fi

# 啟動虛擬環境並執行評分
cd "$(dirname "$0")"
source venv/bin/activate
cd src
python grade_single_student.py "$@"
