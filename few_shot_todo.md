1. 選定三位學生（最關鍵）

挑三位「具明顯差異」的學生：

差（Low-quality）：老師分數最低 or 有明顯瑕疵

中（Medium-quality）：老師分數中間（55–65）

優（High-quality）：老師分數較高（70–80）

TODO：

 從 PDF / CSV 中選三位

 記錄：student_id、老師總分、AI 目前對他們的行為

 群組成：

low_student_id = ???  
mid_student_id = ???  
high_student_id = ???  

🟧 2. 擷取三位學生各自的「影像特徵描述」

這一步 不需要真照片。
你只要用文字描述即可，依你老師的標準。

每位學生至少描述 3 個特徵：

1 個「前片」瑕疵 / 優點

1 個「後片」瑕疵 / 優點

1 個「側面」的合格或不合格點

例如（模板）：

Low-quality example:
- Front: center line clearly off; multiple wrinkles
- Back: pleat not fully transferred
- Side: sleeve armhole not fitted, extra tension

Medium example:
- Front: slight wrinkles; pleats mostly correct
- Back: mild tension but acceptable
- Side: armhole acceptable but not perfect

High-quality example:
- Front: perfectly aligned center line, no wrinkles
- Back: pleats crisp and fully transferred
- Side: sleeve armhole smooth and well-fitted

TODO：

 為 low_student 建 3–4 行「描述」

 為 mid_student 建 3–4 行「描述」

 為 high_student 建 3–4 行「描述」

🟨 3. 擷取老師為那三位學生的部分分數（3～5 題即可）

你不需要 28 題，只挑選最明顯的幾題：

例子：

Low-quality:
Q2 = 1
Q3 = 2
Q4 = 2

Medium:
Q2 = 3
Q3 = 3
Q8 = 1.5

High-quality:
Q2 = 4
Q4 = 5
Q3 = 5


挑選原則：

要能代表品質差異

要包含：中心線、皺紋、折子、貼合等指標

3～5 題就足夠（token 最低）

TODO：

 為 low 學生挑 3～4 題

 為 mid 學生挑 3～4 題

 為 high 學生挑 3～4 題

 保存為簡易 JSON 或你自己抄寫

🟦 4. 整合成少量 few-shot（控制在 150～250 tokens）

最終 few-shot 建議格式如下（這是 AI 最容易學習的格式）：

### Example: Low-quality work
Image characteristics:
- Front: center line clearly off; multiple visible wrinkles
- Back: pleat not fully transferred
- Side: sleeve armhole has tension
Reference scoring:
{"Q2":1, "Q3":2, "Q4":2}

### Example: Medium-quality work
Image characteristics:
- Front: mild wrinkles; pleats mostly correct
- Back: mild tension but acceptable
- Side: armhole acceptable
Reference scoring:
{"Q2":3, "Q3":3, "Q8":1.5}

### Example: High-quality work
Image characteristics:
- Front: perfectly aligned center line; no wrinkles
- Back: pleats crisp and fully transferred
- Side: armhole smooth and well-fitted
Reference scoring:
{"Q2":4, "Q3":5, "Q4":5}

TODO：

 按照上面格式，把三位學生的特徵＋分數寫入

 控制每個 example ≤ 70 tokens

 三個 example 合計 150–220 tokens（超低 token）

🟫 5. 把 few-shot 放到 System Prompt「最上方」

在 vision_system_prompt.txt 頭部放：

Below are three reference grading examples.  
Use these to understand the teacher's scoring style:

### Example: Low-quality work
...

### Example: Medium-quality work
...

### Example: High-quality work
...


放在 任務描述前面，模型會優先吸收這些示例。

TODO：

 在 system prompt 頭部插入 few-shot（不要放 user message）

 確定少於 300 tokens

 確保後面不再有「總分規範」這種累贅語句

🟥 6. 移除（或弱化）所有「總分」相關語句

非常重要
你不能在 Prompt 裡告訴模型：

“分數要落在 55–75”

“不可太高、不可太低”

“避免 collapse”

“避免全部 2–3 分”

…

這些句子會導致模型自動「找一個固定模板」輸出
→ 讓你出現：

75.5

75.5

75.5

75.5

使用 few-shot 後，這些語句需要 全部刪除 或 弱化。

TODO：

 刪除總分約束語句

 刪除 collapse 語句