# AI 視覺評分系統

使用 OpenAI Vision API (GPT-4 Vision) 自動評分服裝設計立體剪裁期中考作品。

## 系統特色

- **扣分制評分邏輯**: AI 先偵測瑕疵描述,再由程式根據關鍵字計算扣分
- **三階段評估**: 分別評估正面照、後片照、側面照,降低 token 使用量
- **智慧全局調整**: 自動偵測 AI 過於樂觀的評分並進行修正
- **嚴格評審標準**: 禁用「稍微」、「少許」等輕描淡寫的詞彙
- **完整評分報告**: 同時輸出瑕疵描述與最終分數

## 快速開始

### 1. 安裝環境

```bash
# 建立虛擬環境
python3 -m venv venv

# 啟動虛擬環境
source venv/bin/activate

# 安裝套件
pip install -r requirements.txt
```

### 2. 設定 API Key

在專案根目錄建立 `.env` 檔案,設定 OpenAI API Key：
```bash
OPENAI_API_KEY=your_api_key_here
VISION_MODEL_NAME=gpt-4o
```

**注意**: 建議使用 `gpt-4o` 以獲得更準確的瑕疵偵測結果。

### 3. 使用方式

#### 單一學生評分(建議使用)
```bash
# 使用 shell script
./run_single_student.sh B11276024 王淯靚

# 或直接執行 Python
cd src
source ../venv/bin/activate
python grade_single_student.py B11276024 王淯靚
```

#### 批次評分所有學生
```bash
cd src
source ../venv/bin/activate
python grade_batch.py
```

設定 API 呼叫間隔（秒）：
```bash
python grade_batch.py 3  # 每次間隔 3 秒
```

#### 只比較 AI 與老師評分
```bash
python grade_batch.py --compare
```

## 專案結構

```
AI_vision/
├── DATA/
│   ├── input/                          # 學生照片與成績
│   │   ├── B11276XXX姓名/              # 學生資料夾
│   │   │   ├── ...第一張.jpg           # 正面照
│   │   │   ├── ...第二張.jpg           # 後面照
│   │   │   ├── ...第三張.jpg           # 側面照
│   │   │   └── ...                     # 其他照片
│   │   └── 立裁期中成績.xlsx           # 老師成績
│   ├── scores_ai/                      # AI 評分輸出
│   │   ├── json/                       # 個別學生 JSON
│   │   ├── scores_ai_final.csv         # 批次評分結果
│   │   └── compare_ai_teacher.csv      # 比較結果
│   └── scores_teacher/                 # 老師成績處理
├── src/
│   ├── config.py                       # 配置檔
│   ├── load_teacher_scores.py          # 載入老師成績
│   ├── call_vision_api.py              # Vision API 呼叫
│   ├── grade_single_student.py         # 單一學生評分
│   └── grade_batch.py                  # 批次評分
├── prompts/
│   ├── rubric_ai_friendly.md            # AI 友善評分尺規
│   ├── vision_system_prompt.txt         # 舊版直接評分 prompt
│   └── vision_defect_detection_prompt.txt # 新版瑕疵偵測 prompt
├── logs/                                # 錯誤記錄
└── requirements.txt                     # Python 套件需求
```

## 評分系統架構

### 扣分制評分流程

```
1. AI 瑕疵偵測
   ↓
   使用 vision_defect_detection_prompt.txt
   AI 回傳瑕疵描述 (不給分數)
   例如: "有明顯皺摺"、"完全對齊"、"簡單設計"

2. 關鍵字分析
   ↓
   deduction_scoring.py 分析瑕疵描述
   根據關鍵字判斷嚴重程度:
   - 優良 (level 0): "完全對齊"、"精準轉移"
   - 輕微 (level 1): "不錯"、"中等複雜"
   - 中度 (level 2): "明顯"、"不平整"、"簡單"
   - 重度 (level 3): "嚴重"、"很"
   - 極差 (level 4): "沒有"、"看不"

3. 計算扣分
   ↓
   根據瑕疵等級選擇對應分數
   例如 Q1 (滿分3): 優良→3, 輕微→2.5, 中度→1.5, 重度→1, 極差→0

4. 全局調整
   ↓
   如果 AI 評價過於樂觀:
   - 中度以上瑕疵 > 40%
   - 優良評價 > 30%
   → 所有「優良」項目降一級
```

### 評分標準

本系統評估 28 個項目（Q1-Q28），總分 100 分：

- **正面照** (Q1-Q12): 47 分
  - Q1: 整燙品質 (3分)
  - Q2: 前中心對齊 (4分)
  - Q3: 折子轉移 (5分)
  - Q4: 無皺紋 (5分)
  - Q5: 芽口整齊 (3分)
  - Q6-Q10: 領口下降、避開乳尖、袖籠下降、鬆份等 (各3分)
  - Q11-Q12: 折子複雜度、領口設計 (各6分)

- **後片照** (Q13-Q25): 47 分
  - 與正面照類似項目

- **側面照** (Q26-Q28): 6 分
  - Q26-Q27: 肩線/斜邊平衡 (各2分)
  - Q28: 袖籠貼合 (2分)

詳細評分標準請參考 [prompts/rubric_ai_friendly.md](prompts/rubric_ai_friendly.md)

## 輸出檔案

### 個別學生 JSON (`DATA/scores_ai/json/B11276XXX.json`)
```json
{
  "student_id": "B11276024",
  "student_name": "王淯靚",
  "scores": {
    "Q1": 1.5,
    "Q2": 3,
    ...
    "Q28": 1
  },
  "total": 55.0,
  "defect_descriptions": {
    "Q1": "有明顯皺摺",
    "Q2": "完全對齊",
    "Q3": "精準轉移",
    "Q4": "有皺紋",
    ...
  },
  "scoring_mode": "deduction",
  "usage_stats": {
    "total_tokens": 15942,
    "model": "gpt-4o"
  },
  "cost_usd": 0.0422
}
```

### 批次評分 CSV (`DATA/scores_ai/scores_ai_final.csv`)
包含所有學生的 student_id, Q1~Q28, total

### 比較結果 CSV (`DATA/scores_ai/compare_ai_teacher.csv`)
包含 student_id, teacher_avg, ai_total, difference

## 測試結果

使用扣分制評分系統後,AI 評分與老師評分的差距大幅縮小:


### Token 使用量 (gpt-4o)
- 單一學生完整評分: ~16,000 tokens
- 費用: 約 $0.04 USD / 學生 (≈ NT$1.3)

## 注意事項

1. 確保每位學生至少有 3 張照片（第一張、第二張、第三張）
2. API 呼叫需要時間，建議設定適當的間隔避免 rate limit
3. 評分結果會自動驗證分數是否在允許範圍內
4. 失敗的評分會記錄在 `logs/failed_students.txt`
5. API 錯誤會儲存在 `logs/api_error_*.txt` 和 `logs/raw_response_*.txt`
6. `.env` 檔案包含 API 金鑰,已加入 `.gitignore`,不會上傳到 GitHub
7. 學生資料與照片受隱私保護,不會上傳到公開 repository

## 技術限制

- AI 視覺模型仍有傾向給予「善意理解」的特性
- 對於極低分作品 (< 30 分),AI 評分可能仍會高估 20-30 分
- 建議將 AI 評分作為輔助參考,而非完全取代人工評分
