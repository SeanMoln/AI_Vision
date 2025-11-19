"""
呼叫 OpenAI Vision API 進行評分
"""
import base64
import json
from pathlib import Path
from typing import List, Dict
import openai
import config

# 設定 OpenAI API key
openai.api_key = config.OPENAI_API_KEY

def encode_image_to_base64(image_path: str) -> str:
    """
    將圖片編碼為 base64 字串

    Args:
        image_path: 圖片檔案路徑

    Returns:
        base64 編碼的圖片字串
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def build_vision_messages(student_id: str, image_paths: List[str]) -> List[Dict]:
    """
    組裝 Vision API 請求的 messages（一次評所有題目）

    Args:
        student_id: 學生ID
        image_paths: 圖片路徑列表 [正面, 背面, 側面]

    Returns:
        API messages 格式
    """
    # 讀取 system prompt
    with open(config.SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    # 準備圖片內容
    image_contents = []
    image_labels = ['正面照', '後片照', '側面照', '第四張照片', '第五張照片']

    for i, img_path in enumerate(image_paths):
        if Path(img_path).exists():
            base64_image = encode_image_to_base64(img_path)
            label = image_labels[i] if i < len(image_labels) else f'第{i+1}張照片'

            image_contents.append({
                "type": "text",
                "text": f"\n## {label}"
            })
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
            })

    # 組裝 messages
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"請評分學生 {student_id} 的作品。以下是該學生的照片："
                }
            ] + image_contents + [
                {
                    "type": "text",
                    "text": "\n\n請依據評分尺規，為所有28個項目(Q1-Q28)評分，並以 JSON 格式輸出結果。"
                }
            ]
        }
    ]

    return messages

def build_vision_messages_for_section(student_id: str, image_paths: List[str],
                                     section: str, question_range: range,
                                     use_defect_detection: bool = True) -> List[Dict]:
    """
    組裝特定部位（前/後/側）的 Vision API 請求

    Args:
        student_id: 學生ID
        image_paths: 該部位的圖片路徑列表
        section: 部位名稱 ("front", "back", "side")
        question_range: 要評分的題號範圍 (如 range(1, 13) 代表 Q1-Q12)
        use_defect_detection: 是否使用瑕疵偵測模式（True=偵測瑕疵, False=直接給分）

    Returns:
        API messages 格式
    """
    # 選擇 prompt 檔案
    if use_defect_detection:
        prompt_file = config.PROJECT_ROOT / "prompts" / "vision_defect_detection_prompt.txt"
    else:
        prompt_file = config.SYSTEM_PROMPT_FILE

    # 讀取 system prompt
    with open(prompt_file, 'r', encoding='utf-8') as f:
        system_prompt = f.read()

    # 部位描述
    section_names = {
        "front": "前片",
        "back": "後片",
        "side": "側面"
    }
    section_name = section_names.get(section, section)

    # 準備圖片內容
    image_contents = []
    for i, img_path in enumerate(image_paths):
        if Path(img_path).exists():
            base64_image = encode_image_to_base64(img_path)

            image_contents.append({
                "type": "text",
                "text": f"\n## {section_name}照片 {i+1}"
            })
            image_contents.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}",
                    "detail": "high"
                }
            })

    # 生成要評分的題號列表
    questions_to_grade = [f"Q{i}" for i in question_range]
    questions_str = ", ".join(questions_to_grade)

    # 根據模式調整提示語
    if use_defect_detection:
        task_instruction = f"\n\n請檢查學生作品的{section_name}，針對這些題目描述你觀察到的瑕疵：{questions_str}\n\n只需要描述這些題目對應的項目，以 JSON 格式輸出瑕疵描述。"
    else:
        task_instruction = f"\n\n請專注評分{section_name}相關的題目：{questions_str}\n\n只需要評分這些題目，以 JSON 格式輸出結果。"

    # 組裝 messages
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": f"請檢查學生 {student_id} 的【{section_name}】。以下是該學生的{section_name}照片："
                }
            ] + image_contents + [
                {
                    "type": "text",
                    "text": task_instruction
                }
            ]
        }
    ]

    return messages

def call_vision_model(messages: List[Dict]) -> tuple[str, dict]:
    """
    呼叫 OpenAI Vision API

    Args:
        messages: API messages

    Returns:
        (模型回傳的文字, 使用統計資訊)
    """
    try:
        client = openai.OpenAI(api_key=config.OPENAI_API_KEY)

        response = client.chat.completions.create(
            model=config.VISION_MODEL_NAME,
            messages=messages,
            max_tokens=2000,
            temperature=0.3  # 稍微提高以允許更細緻的判斷
        )

        # 收集使用統計
        usage_stats = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
            'model': config.VISION_MODEL_NAME
        }

        return response.choices[0].message.content, usage_stats

    except Exception as e:
        raise Exception(f"呼叫 Vision API 失敗: {str(e)}")

def parse_defect_descriptions_from_response(response_text: str, required_questions: List[str] = None) -> Dict:
    """
    從 API 回應中解析瑕疵描述

    Args:
        response_text: API 回傳的文字
        required_questions: 必須包含的題目列表（如 ['Q1', 'Q2', ...]）

    Returns:
        瑕疵描述字典 {'Q1': '描述', 'Q2': '描述', ...}
    """
    try:
        # 嘗試提取 JSON
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
            else:
                json_str = response_text

        descriptions = json.loads(json_str)

        # 驗證所有要求的題目都有描述
        if required_questions:
            expected_questions = required_questions
        else:
            expected_questions = [f"Q{i}" for i in range(1, 29)]

        missing_questions = [q for q in expected_questions if q not in descriptions]

        if missing_questions:
            raise ValueError(f"缺少以下題目的描述: {missing_questions}")

        # 驗證描述格式（應該是字串）
        for q, desc in descriptions.items():
            if not isinstance(desc, str):
                raise ValueError(f"{q} 的描述格式錯誤: {desc}")

        return descriptions

    except json.JSONDecodeError as e:
        raise ValueError(f"無法解析 JSON 回應: {str(e)}\n原始回應: {response_text}")
    except Exception as e:
        raise ValueError(f"解析瑕疵描述失敗: {str(e)}\n原始回應: {response_text}")

def parse_scores_from_response(response_text: str, required_questions: List[str] = None) -> Dict:
    """
    從 API 回應中解析評分結果

    Args:
        response_text: API 回傳的文字
        required_questions: 必須包含的題目列表（如 ['Q1', 'Q2', ...]）
                          如果為 None，則預期所有 28 題

    Returns:
        包含 scores 和 total 的字典
    """
    try:
        # 嘗試提取 JSON（可能包含在 ```json ... ``` 中）
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            json_str = response_text[json_start:json_end].strip()
        else:
            # 嘗試找到第一個 { 和最後一個 }
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end != 0:
                json_str = response_text[json_start:json_end]
            else:
                json_str = response_text

        scores = json.loads(json_str)

        # 驗證所有要求的題目都有分數
        if required_questions is None:
            expected_questions = [f"Q{i}" for i in range(1, 29)]
        else:
            expected_questions = required_questions

        missing_questions = [q for q in expected_questions if q not in scores]

        if missing_questions:
            raise ValueError(f"缺少以下題目的分數: {missing_questions}")

        # 驗證分數格式
        for q, score in scores.items():
            if not isinstance(score, (int, float)):
                raise ValueError(f"{q} 的分數格式錯誤: {score}")

        # 計算總分（只計算要求的題目）
        if required_questions:
            total = sum(scores[q] for q in required_questions if q in scores)
        else:
            total = sum(scores.values())

        return {
            "scores": scores,
            "total": round(total, 1)
        }

    except json.JSONDecodeError as e:
        raise ValueError(f"無法解析 JSON 回應: {str(e)}\n原始回應: {response_text}")
    except Exception as e:
        raise ValueError(f"解析評分失敗: {str(e)}\n原始回應: {response_text}")

def calculate_cost(usage_stats: dict) -> dict:
    """
    計算 API 使用費用（美金）

    Args:
        usage_stats: 使用統計資訊

    Returns:
        費用資訊字典
    """
    # OpenAI GPT-4o-mini 價格（2024年價格，實際價格請參考官網）
    # Input: $0.15 / 1M tokens
    # Output: $0.60 / 1M tokens

    PRICING = {
        'gpt-4o-mini': {
            'input': 0.15 / 1_000_000,   # 每 token 價格
            'output': 0.60 / 1_000_000
        },
        'gpt-4o': {
            'input': 2.5 / 1_000_000,
            'output': 10.0 / 1_000_000
        },
        'gpt-4-vision-preview': {
            'input': 0.01 / 1000,
            'output': 0.03 / 1000
        }
    }

    model = usage_stats.get('model', 'gpt-4o-mini')

    # 如果模型不在列表中，使用 gpt-4o-mini 的價格
    if model not in PRICING:
        model = 'gpt-4o-mini'

    pricing = PRICING[model]

    input_cost = usage_stats['prompt_tokens'] * pricing['input']
    output_cost = usage_stats['completion_tokens'] * pricing['output']
    total_cost = input_cost + output_cost

    return {
        'input_cost': input_cost,
        'output_cost': output_cost,
        'total_cost': total_cost,
        'currency': 'USD'
    }

def validate_scores(scores: Dict) -> List[str]:
    """
    驗證分數是否在允許的範圍內

    Args:
        scores: 分數字典

    Returns:
        警告訊息列表（如果有的話）
    """
    # 定義每題允許的分數
    allowed_scores = {
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

    warnings = []

    for q, score in scores.items():
        if q in allowed_scores:
            if score not in allowed_scores[q]:
                warnings.append(f"⚠ {q} 的分數 {score} 不在允許範圍內: {allowed_scores[q]}")

    return warnings
