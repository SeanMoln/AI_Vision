"""
扣分制評分邏輯
根據 AI 偵測到的瑕疵描述，計算扣分後的分數
"""

# 每題的滿分
MAX_SCORES = {
    'Q1': 3, 'Q2': 4, 'Q3': 5, 'Q4': 5, 'Q5': 3,
    'Q6': 3, 'Q7': 3, 'Q8': 3, 'Q9': 3, 'Q10': 3,
    'Q11': 6, 'Q12': 6,
    'Q13': 3, 'Q14': 4, 'Q15': 5, 'Q16': 5, 'Q17': 3,
    'Q18': 3, 'Q19': 3, 'Q20': 3, 'Q21': 3,
    'Q22': 6, 'Q23': 6, 'Q24': 3, 'Q25': 3,
    'Q26': 2, 'Q27': 2, 'Q28': 2
}

# 每題允許的分數選項（用於對齊）
ALLOWED_SCORES = {
    'Q1': [3, 2.5, 1.5, 1, 0],
    'Q2': [4, 3, 2, 1, 0],
    'Q3': [5, 4, 3, 2, 0],
    'Q4': [5, 4, 3, 2, 0],
    'Q5': [3, 2.5, 1.5, 1, 0],
    'Q6': [3, 0],
    'Q7': [3, 1.5, 0],
    'Q8': [3, 1.5, 0],
    'Q9': [3, 1.5, 0],
    'Q10': [3, 1.5, 0],
    'Q11': [6, 5, 3, 1, 0],
    'Q12': [6, 5, 3, 1, 0],
    'Q13': [3, 2.5, 2, 1, 0],
    'Q14': [4, 2, 0],
    'Q15': [5, 4, 3, 2, 0],
    'Q16': [5, 4, 3, 2, 0],
    'Q17': [3, 2.5, 1.5, 1, 0],
    'Q18': [3, 0],
    'Q19': [3, 1.5, 0],
    'Q20': [3, 1.5, 0],
    'Q21': [3, 1.5, 0],
    'Q22': [6, 5, 3, 1, 0],
    'Q23': [6, 5, 3, 1, 0],
    'Q24': [3, 2, 0],
    'Q25': [3, 2, 0],
    'Q26': [2, 1.5, 1, 0.5, 0],
    'Q27': [2, 1.5, 1, 0.5, 0],
    'Q28': [2, 1, 0],
}

# 瑕疵關鍵字與扣分對應
# 格式: (關鍵字列表, 扣分等級)
# 扣分等級: 0=滿分, 1=輕微扣分, 2=中度扣分, 3=重度扣分, 4=極差(0分)
DEFECT_KEYWORDS = {
    # === 優良品質 (不扣分) ===
    '完美': ('優良', 0),
    '非常平整': ('優良', 0),
    '完全對齊': ('優良', 0),
    '精準轉移': ('優良', 0),
    '完全無皺紋': ('優良', 0),
    '非常整齊': ('優良', 0),
    '完全服貼': ('優良', 0),
    '非常平衡': ('優良', 0),
    '優秀設計': ('優良', 0),
    '精緻複雜': ('優良', 0),
    '複雜設計': ('優良', 0),
    '位置正確': ('優良', 0),
    '適當鬆份': ('優良', 0),

    # === 良好品質 (輕微扣分) ===
    # 移除了「稍微」、「少許」、「些微」等詞
    '不錯': ('輕微', 1),
    '中等複雜': ('輕微', 1),
    '中等': ('輕微', 1),
    '可以': ('輕微', 1),
    '下降不足': ('輕微', 1),

    # === 明顯瑕疵 (中度扣分) ===
    '明顯': ('中度', 2),
    '多處': ('中度', 2),
    '偏離': ('中度', 2),
    '歪斜': ('中度', 2),
    '凌亂': ('中度', 2),
    '不平衡': ('中度', 2),
    '空隙': ('中度', 2),
    '偏移': ('中度', 2),
    '基本設計': ('中度', 2),
    '基本款': ('中度', 2),
    '基本': ('中度', 2),
    '簡單設計': ('中度', 2),
    '簡單': ('中度', 2),
    '普通設計': ('中度', 2),
    '普通': ('中度', 2),
    '有偏差': ('中度', 2),
    '有皺摺': ('中度', 2),
    '有皺紋': ('中度', 2),
    '不平整': ('中度', 2),
    '不精準': ('中度', 2),
    '不整齊': ('中度', 2),
    '不對齊': ('中度', 2),
    '不服貼': ('中度', 2),
    '不平滑': ('中度', 2),
    '壓到': ('中度', 2),
    '過緊': ('中度', 2),
    '過鬆': ('中度', 2),

    # === 嚴重問題 (重度扣分) ===
    '嚴重': ('重度', 3),
    '很': ('重度', 3),  # "很凌亂"、"很簡單"
    '太': ('重度', 3),  # "太緊"、"太鬆"
    '失衡': ('重度', 3),
    '拉扯': ('重度', 3),
    '錯誤': ('重度', 3),
    '極簡單': ('重度', 3),

    # === 完全不合格 (0分) ===
    '沒有': ('極差', 4),
    '沒': ('極差', 4),
    '無法': ('極差', 4),
    '看不': ('極差', 4),
    '缺少': ('極差', 4),
    '缺失': ('極差', 4),
}

def detect_defect_level(description: str) -> tuple:
    """
    根據瑕疵描述判斷嚴重程度

    Args:
        description: AI 回傳的瑕疵描述

    Returns:
        (瑕疵等級名稱, 扣分等級 0-4)
    """
    description = description.lower().strip()

    # 檢查關鍵字
    max_level = 0
    matched_category = '優良'

    for keyword, (category, level) in DEFECT_KEYWORDS.items():
        if keyword in description:
            if level > max_level:
                max_level = level
                matched_category = category

    return matched_category, max_level

def calculate_deduction_score(question: str, description: str) -> float:
    """
    根據瑕疵描述計算扣分後的分數

    Args:
        question: 題號 (如 'Q1')
        description: AI 回傳的瑕疵描述

    Returns:
        扣分後的分數
    """
    max_score = MAX_SCORES.get(question, 0)
    allowed = ALLOWED_SCORES.get(question, [0])

    # 偵測瑕疵等級
    category, level = detect_defect_level(description)

    # 根據扣分等級選擇對應的分數
    # level 0: 滿分或次高分
    # level 1: 次高分或中等分
    # level 2: 中等分或低分
    # level 3: 低分
    # level 4: 0分

    if level == 0:  # 優良
        # 給滿分
        score = allowed[0]
    elif level == 1:  # 輕微瑕疵
        # 給次高分
        if len(allowed) >= 2:
            score = allowed[1]
        else:
            score = allowed[0]
    elif level == 2:  # 中度瑕疵
        # 給中等分數
        mid_index = len(allowed) // 2
        score = allowed[mid_index]
    elif level == 3:  # 重度瑕疵
        # 給倒數第二低的分數
        if len(allowed) >= 2:
            score = allowed[-2]
        else:
            score = allowed[-1]
    else:  # level == 4, 極差
        # 給0分
        score = 0

    return score

def calculate_all_scores(defect_descriptions: dict, apply_global_adjustment: bool = True) -> dict:
    """
    根據所有題目的瑕疵描述計算分數

    Args:
        defect_descriptions: AI 回傳的瑕疵描述字典 {Q1: "...", Q2: "...", ...}
        apply_global_adjustment: 是否套用全局調整（預設開啟）

    Returns:
        分數字典 {Q1: 2.5, Q2: 3, ...}
    """
    scores = {}

    for question in [f'Q{i}' for i in range(1, 29)]:
        description = defect_descriptions.get(question, '看不清楚')
        score = calculate_deduction_score(question, description)
        scores[question] = score

    # 全局調整：如果 AI 給分過於樂觀，往下調整
    if apply_global_adjustment:
        scores = apply_global_score_adjustment(scores, defect_descriptions)

    return scores

def apply_global_score_adjustment(scores: dict, defect_descriptions: dict) -> dict:
    """
    全局分數調整：根據瑕疵嚴重度分布，調整過於樂觀的評分

    策略：
    - 統計「優良」評價的比例
    - 如果「優良」評價過多（>50%），代表 AI 過於樂觀
    - 對「優良」項目進行保守扣分

    Args:
        scores: 原始分數字典
        defect_descriptions: 瑕疵描述字典

    Returns:
        調整後的分數字典
    """
    # 統計各級別數量
    level_counts = {'優良': 0, '輕微': 0, '中度': 0, '重度': 0, '極差': 0}

    for q, desc in defect_descriptions.items():
        category, level = detect_defect_level(desc)
        level_counts[category] += 1

    total = sum(level_counts.values())
    excellent_ratio = level_counts['優良'] / total if total > 0 else 0
    medium_or_worse_ratio = (level_counts['中度'] + level_counts['重度'] + level_counts['極差']) / total if total > 0 else 0

    # 評分邏輯：
    # - 如果中度以上瑕疵 > 40%，但優良評價 > 30%，代表 AI 過於樂觀
    # - 對所有「優良」項目進行保守扣分
    if medium_or_worse_ratio > 0.4 and excellent_ratio > 0.3:
        print(f"  ⚠ 偵測到 AI 評價過於樂觀")
        print(f"    中度以上瑕疵: {medium_or_worse_ratio:.1%}, 優良評價: {excellent_ratio:.1%}")
        print(f"  → 套用保守調整（所有優良項目降級）...")

        adjusted_scores = {}
        for question, score in scores.items():
            desc = defect_descriptions.get(question, '')
            category, level = detect_defect_level(desc)

            # 對「優良」項目進行保守扣分
            if category == '優良':
                allowed = ALLOWED_SCORES.get(question, [0])
                # 從滿分降到次高分
                if len(allowed) >= 2 and score == allowed[0]:
                    adjusted_scores[question] = allowed[1]
                else:
                    adjusted_scores[question] = score
            else:
                adjusted_scores[question] = score

        return adjusted_scores
    else:
        return scores

def format_scoring_report(defect_descriptions: dict, scores: dict) -> str:
    """
    生成評分報告（顯示瑕疵描述和對應的扣分）

    Args:
        defect_descriptions: 瑕疵描述字典
        scores: 分數字典

    Returns:
        格式化的報告字串
    """
    report_lines = []
    report_lines.append("="*60)
    report_lines.append("扣分制評分報告")
    report_lines.append("="*60)

    sections = [
        ("正面照 (Q1-Q12)", range(1, 13)),
        ("後片照 (Q13-Q25)", range(13, 26)),
        ("側面照 (Q26-Q28)", range(26, 29))
    ]

    for section_name, q_range in sections:
        report_lines.append(f"\n{section_name}:")
        for i in q_range:
            q = f"Q{i}"
            desc = defect_descriptions.get(q, "無描述")
            score = scores.get(q, 0)
            max_score = MAX_SCORES.get(q, 0)
            category, level = detect_defect_level(desc)

            report_lines.append(f"  {q}: {score}/{max_score} - [{category}] {desc}")

    total = sum(scores.values())
    report_lines.append(f"\n總分: {total} / 100")
    report_lines.append("="*60)

    return "\n".join(report_lines)

# 測試函數
if __name__ == "__main__":
    # 測試範例
    test_descriptions = {
        "Q1": "有明顯皺摺",
        "Q2": "完全對齊",
        "Q3": "精準轉移",
        "Q4": "少許皺紋",
        "Q5": "非常整齊",
        "Q11": "簡單設計",
        "Q26": "嚴重不平衡"
    }

    print("測試扣分邏輯:\n")
    for q, desc in test_descriptions.items():
        category, level = detect_defect_level(desc)
        score = calculate_deduction_score(q, desc)
        max_score = MAX_SCORES[q]
        print(f"{q}: '{desc}' → [{category}, level={level}] → {score}/{max_score}")
