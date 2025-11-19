# AI 視覺評分系統

使用 OpenAI Vision API 自動評分服裝設計期中考作品。

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

確認 `.env` 檔案中有設定 OpenAI API Key：
```
OPENAI_API_KEY=your_api_key_here
VISION_MODEL_NAME=gpt-4o-mini
```

### 3. 使用方式

#### 單一學生評分
```bash
cd src
source ../venv/bin/activate
python grade_single_student.py B11276001 林芷綺
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
│   ├── rubric_ai_friendly.md           # AI 友善評分尺規
│   └── vision_system_prompt.txt        # Vision API system prompt
├── logs/                               # 錯誤記錄
└── requirements.txt                    # Python 套件需求
```

## 評分標準

本系統評估 28 個項目（Q1-Q28），總分 100 分：

- **正面照** (Q1-Q12): 47 分
  - 布料整燙、對齊、折子轉移、平整度、縫份、尺寸、設計等

- **後片照** (Q13-Q25): 47 分
  - 布料整燙、對齊、折子轉移、平整度、縫份、尺寸、設計等

- **側面照** (Q26-Q28): 6 分
  - 前後片別法、袖籠處理

詳細評分標準請參考 `prompts/rubric_ai_friendly.md`

## 輸出檔案

### 個別學生 JSON (`DATA/scores_ai/json/B11276XXX.json`)
```json
{
  "student_id": "B11276001",
  "student_name": "林芷綺",
  "scores": {
    "Q1": 2.5,
    "Q2": 3,
    ...
    "Q28": 1
  },
  "total": 75.5
}
```

### 批次評分 CSV (`DATA/scores_ai/scores_ai_final.csv`)
包含所有學生的 student_id, Q1~Q28, total

### 比較結果 CSV (`DATA/scores_ai/compare_ai_teacher.csv`)
包含 student_id, teacher_avg, ai_total, difference

## 注意事項

1. 確保每位學生至少有 3 張照片（第一張、第二張、第三張）
2. API 呼叫需要時間，建議設定適當的間隔避免 rate limit
3. 評分結果會自動驗證分數是否在允許範圍內
4. 失敗的評分會記錄在 `logs/failed_students.txt`
5. API 錯誤會儲存在 `logs/api_error_*.txt` 和 `logs/raw_response_*.txt`
