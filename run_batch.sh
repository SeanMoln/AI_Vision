#!/bin/bash
# 批次評分腳本

# 預設間隔 2 秒
DELAY=${1:-2}

echo "================================"
echo "批次評分系統"
echo "================================"
echo "API 呼叫間隔: $DELAY 秒"
echo ""
echo "注意: 批次評分會消耗較多 API 額度"
echo "請確認已準備好再繼續"
echo ""
read -p "按 Enter 繼續，或 Ctrl+C 取消..."

# 啟動虛擬環境並執行批次評分
cd "$(dirname "$0")"
source venv/bin/activate
cd src
python grade_batch.py "$DELAY"
