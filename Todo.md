0. 專案與資料結構先定好

建一個專案資料夾（範例）

ai_grading_midterm/

data/

rubric/（評量尺規相關）

scores_teacher/（老師原始分數）

images/（學生照片）

B11076032_front.jpg

B11076032_back.jpg

B11076032_side.jpg

…

scores_ai/（AI 評分輸出檔）

prompts/

rubric_ai_friendly.md

vision_system_prompt.txt

src/

config.py

load_teacher_scores.py

build_prompt.py

call_vision_api.py

grade_single_student.py

grade_batch.py

notebooks/（可選，用來試驗）

在 .env 或 config.py 中預留：

OPENAI_API_KEY

影像檔根目錄 IMAGE_ROOT

模型名稱 VISION_MODEL_NAME（例如 gpt-4o-mini 或未來的 vision 模型名）

1. 評分尺規（Rubric）整理成「AI 可讀格式」
1.1 從 docx 萃取所有題目與描述

把 期中考--教師版上衣折子變化評量尺規(修正後).docx 的內容整理成表格形式（可以用 Word、Excel 或手動整理）：

欄位包含：

題號（Q1, Q2, …）

題目名稱（例：準備材料：胚布整燙平整）

滿分（例：+3、+5、+6）

各等級敘述（極優 / 優 / 尚可 / 差 / 極差）

對應分數（3 / 2.5 / 1.5 / 0…）

確認每題的實際可能分數集合：

例如：

Q1 只會出現：3, 2.5, 1.5, 1, 0

Q4 只會出現：5, 4, 3, 2, 0

整理成一份 JSON 或表格，後面 prompt 會用到。

1.2 把 rubric 重寫成「規則化、短句、視覺可判斷」

為每題建立一個結構（存在 prompts/rubric_ai_friendly.md 或 JSON）：

例如 Q1：

id: Q1

name: 準備材料：胚布整燙平整

max_score: 3

rules:

3 分：布料整片平整，看不到明顯折痕或壓痕。

2.5 分：有一條輕微折痕，退一步看幾乎看不見。

1.5 分：有兩條以上不明顯折痕，退一步看略可見。

1 分：有一條明顯折痕，退一步看仍清楚可見。

0 分：多條明顯折痕，整體看起來皺或沒整燙。

對所有題（正面、後片、側面）逐一完成同樣格式：

明確描述「照片中該看什麼」：

布面是否平整、是否有斜紋、折子是否完整轉移、人台中心線是否對齊、鬆份是否足夠、有無拉扯皺紋、折子設計複雜度等。

確認每個敘述都：

避免模糊用語（例如「尚可」要改成具體狀況）

全部是「可以在照片中觀察到的東西」

2. 老師成績資料整理（為了後面對照）
2.1 把 PDF / Excel 成績轉成機器可用格式

若手上已有原始 Excel（從 PDF 轉出）：

存成 data/scores_teacher/midterm_scores.xlsx

決定欄位命名規則：

student_id（學號）

student_name（姓名）

Q1～Q28（對應每題分數）

total（總分，如果有）

撰寫 src/load_teacher_scores.py：

讀取 Excel → DataFrame

檢查欄位是否與 rubric 題目數量一致（28 題）

存成 data/scores_teacher/midterm_scores_clean.csv

2.2 簡單統計（支援後面校正）

在 notebooks/ 建一個 Notebook：

載入 midterm_scores_clean.csv

對每題計算：

平均值

標準差

最常見分數（mode）

將結果輸出為 data/scores_teacher/teacher_stats_per_question.csv：

欄位：

question_id（Q1…Q28）

mean

std

mode

min

max

3. 定義最終輸出格式與檔案規格
3.1 單一學生評分結果格式

設計一份 JSON 結構（單一學生）：

{
  "student_id": "B11076032",
  "scores": {
    "Q1": 2.5,
    "Q2": 3,
    "Q3": 5,
    "...": 0
  },
  "total": 64.0
}


定義儲存位置：

每位學生一個 JSON：
data/scores_ai/json/B11076032.json

或之後聚合成一個 CSV（全部學生）。

3.2 批次輸出格式（最終評分檔）

設計一個 scores_ai_final.csv 或 xlsx：

欄位：

student_id

Q1～Q28

total

位置：data/scores_ai/scores_ai_final.csv

4. Prompt 設計與檔案化
4.1 System Prompt（評分角色 + 原則）

在 prompts/vision_system_prompt.txt 中撰寫內容：

指定角色：服裝設計教師，熟悉立體剪裁與評分標準。

任務：

讀 rubric 摘要

檢視多張照片（front/back/side）

依每題的規則給出分數

不要超過規則中列出的分數集合。

要求：

分數只能是 rubric 中定義的值（例如：3 / 2.5 / 1.5 / 1 / 0）

嚴格依規則，不要自由發揮

最終只輸出 JSON 格式，不能加文字解釋。

4.2 Prompt 中 embed Rubric

將 rubric_ai_friendly.md 的內容摘要嵌入 system prompt：

每題：題號 + 簡短規則 + 分數選項列表

注意控制長度，避免 prompt 超長：

只保留需要視覺判斷的關鍵詞（平整、折痕、斜紋、拉扯、對齊線等）。

4.3 輸出格式約束

在 system prompt 明確定義輸出格式範例：

{
  "Q1": 2.5,
  "Q2": 3,
  "Q3": 5,
  "...": 0,
  "Q28": 1.5
}


指定：

若無法判斷某題，仍須給出最接近的分數（不能留空）。

5. 單一學生評分流程實作
5.1 寫一個函式：組裝 Vision API 請求

在 src/call_vision_api.py 中：

建立函式 build_vision_messages(student_id, image_paths)：

image_paths：包含 front/back/side 三張路徑。

messages：

system: 讀取 vision_system_prompt.txt 內容

user:

一段簡短說明：這是某位學生的正面 / 背面 / 側面照

三個 image_url（或本地檔經過 base64/上傳後的 URL）

建立函式 call_vision_model(messages)：

呼叫 OpenAI 的 chat/vision 端點

拿到 model 回傳的文字（JSON 字串）

建立函式 parse_scores_from_response(text)：

將文字 parse 成 Python dict

檢查：

是否含 Q1～Q28

是否都是數字且在允許的分數集合中

計算 total 分數。

5.2 寫單一學生評分腳本

在 src/grade_single_student.py：

接受輸入：student_id

根據命名規則組合照片路徑：

images/{student_id}_front.jpg

images/{student_id}_back.jpg

images/{student_id}_side.jpg

呼叫：

build_vision_messages

call_vision_model

parse_scores_from_response

輸出結果：

在終端顯示每題分數與總分

存一份 JSON 到 data/scores_ai/json/{student_id}.json

增加基本錯誤處理：

如果某張照片缺失 → 印出警告，暫停不評分。

如果 API 回傳格式錯誤 → 儲存 raw 回應到 logs/ 做 debug。

6. 批次評分（所有學生）
6.1 建立學生名單

從老師成績檔 midterm_scores_clean.csv 抓取全部 student_id 列表。

寫到 data/students_list.txt（一行一個學號），之後批次用。

6.2 寫批次評分腳本 src/grade_batch.py

步驟：

讀取 students_list.txt

對每個 student_id：

檢查三張照片是否都存在

呼叫 grade_single_student 對應的核心函式（不要重寫邏輯）

把每位學生的結果暫存到 list

評分過程中：

印出進度（第幾個 / 總數）

若某學生錯誤（照片少或 API error），記錄到 logs/failed_students.txt

批次完成後：

將所有學生的結果合併成一個 DataFrame：

student_id

Q1～Q28

total

存到 data/scores_ai/scores_ai_final.csv

7. 基本檢查與對照

（仍然「不部署」，只是檢查 AI 評分品質）

7.1 結果基本 sanity check

開啟 scores_ai_final.csv：

確認每題分數都在預期集合中（無奇怪小數）

無缺欄位（所有學生都有 Q1～Q28）

7.2 與老師分數簡單比較（可選，但很有用）

合併：

scores_teacher/midterm_scores_clean.csv

scores_ai/scores_ai_final.csv

依 student_id join

計算：

每題（Q1～Q28）AI vs 老師的差值分佈

總分差距（AI_total - teacher_total）

輸出一個比較檔：

data/scores_ai/compare_ai_teacher.csv