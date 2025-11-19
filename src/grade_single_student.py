"""
單一學生評分腳本
"""
import json
import sys
from pathlib import Path
from typing import List, Optional
import config
from call_vision_api import (
    build_vision_messages,
    call_vision_model,
    parse_scores_from_response,
    parse_defect_descriptions_from_response,
    validate_scores,
    calculate_cost
)
from deduction_scoring import (
    calculate_all_scores,
    format_scoring_report
)

def find_student_images(student_id: str, student_name: str = None) -> Optional[List[str]]:
    """
    尋找學生的照片檔案

    Args:
        student_id: 學生ID（如 B11276001）
        student_name: 學生姓名（可選）

    Returns:
        照片路徑列表，如果找不到則返回 None
    """
    # 在 DATA/input 目錄中尋找該學生的資料夾
    input_dir = config.IMAGE_ROOT

    # 可能的資料夾名稱模式
    possible_folder_patterns = [
        f"{student_id}{student_name}",  # B11276001林芷綺
        f"{student_id} {student_name}",  # B11276001 林芷綺
        f"{student_id}",  # B11276001
    ]

    student_folder = None

    # 嘗試找到學生資料夾
    for folder in input_dir.iterdir():
        if folder.is_dir():
            folder_name = folder.name
            # 檢查資料夾名稱是否包含學生ID
            if student_id in folder_name:
                if student_name is None or student_name in folder_name:
                    student_folder = folder
                    break

    if not student_folder:
        print(f"❌ 找不到學生 {student_id} 的資料夾")
        return None

    # 尋找照片檔案（第一張到第五張）
    image_files = []
    image_patterns = ['第一張', '第二張', '第三張', '第四張', '第五張']

    for pattern in image_patterns:
        # 尋找包含該模式的檔案
        matching_files = list(student_folder.glob(f"*{pattern}*.jpg")) + \
                        list(student_folder.glob(f"*{pattern}*.jpeg")) + \
                        list(student_folder.glob(f"*{pattern}*.png"))

        if matching_files:
            image_files.append(str(matching_files[0]))
        else:
            print(f"⚠ 警告: 找不到 {pattern} 的照片")

    if len(image_files) < 3:
        print(f"❌ 學生 {student_id} 的照片不足（至少需要3張：正面、後面、側面）")
        return None

    print(f"✓ 找到 {len(image_files)} 張照片")
    return image_files

def grade_student(student_id: str, student_name: str = None, save_json: bool = True,
                 use_deduction_mode: bool = True) -> Optional[dict]:
    """
    為單一學生評分（分三次API呼叫：前片、後片、側面）

    Args:
        student_id: 學生ID
        student_name: 學生姓名（可選）
        save_json: 是否儲存 JSON 結果
        use_deduction_mode: 是否使用扣分制模式（True=瑕疵偵測+扣分, False=直接評分）

    Returns:
        評分結果字典，包含 student_id, scores, total
    """
    mode_text = "扣分制模式（瑕疵偵測）" if use_deduction_mode else "直接評分模式"
    print(f"\n{'='*60}")
    print(f"開始評分: {student_id} {student_name or ''}")
    print(f"評分模式: {mode_text}")
    print(f"{'='*60}\n")

    # 1. 尋找學生照片
    print("步驟 1/6: 尋找學生照片...")
    image_paths = find_student_images(student_id, student_name)

    if not image_paths:
        return None

    # 確保至少有3張照片
    if len(image_paths) < 3:
        print(f"❌ 照片不足（需要至少3張）")
        return None

    # 將照片分組：前片、後片、側面
    front_images = [image_paths[0]]  # 第一張 = 前片
    back_images = [image_paths[1]]   # 第二張 = 後片
    side_images = [image_paths[2]]   # 第三張 = 側面

    # 如果有第四、五張，也加入相應組別
    if len(image_paths) >= 4:
        front_images.append(image_paths[3])  # 第四張也是前片
    if len(image_paths) >= 5:
        back_images.append(image_paths[4])   # 第五張也是後片

    all_scores = {}
    all_defect_descriptions = {}  # 儲存瑕疵描述
    total_usage_stats = {
        'prompt_tokens': 0,
        'completion_tokens': 0,
        'total_tokens': 0,
        'model': config.VISION_MODEL_NAME
    }

    # 2. 評分前片 (Q1-Q12)
    print("\n步驟 2/6: 評分前片 (Q1-Q12)...")
    try:
        from call_vision_api import build_vision_messages_for_section
        messages = build_vision_messages_for_section(
            student_id, front_images, "front", range(1, 13),
            use_defect_detection=use_deduction_mode
        )
        response_text, usage_stats = call_vision_model(messages)

        print("✓ 前片評分完成")
        print(f"  Token: {usage_stats['total_tokens']:,}")

        # 累計統計
        for key in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
            total_usage_stats[key] += usage_stats[key]

        # 解析結果
        required_qs = [f"Q{i}" for i in range(1, 13)]

        if use_deduction_mode:
            # 解析瑕疵描述
            descriptions = parse_defect_descriptions_from_response(response_text, required_questions=required_qs)
            all_defect_descriptions.update(descriptions)
        else:
            # 直接解析分數
            result = parse_scores_from_response(response_text, required_questions=required_qs)
            all_scores.update(result['scores'])

    except Exception as e:
        print(f"❌ 前片評分失敗: {e}")
        return None

    # 3. 評分後片 (Q13-Q25)
    print("\n步驟 3/6: 評分後片 (Q13-Q25)...")
    try:
        messages = build_vision_messages_for_section(
            student_id, back_images, "back", range(13, 26),
            use_defect_detection=use_deduction_mode
        )
        response_text, usage_stats = call_vision_model(messages)

        print("✓ 後片評分完成")
        print(f"  Token: {usage_stats['total_tokens']:,}")

        # 累計統計
        for key in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
            total_usage_stats[key] += usage_stats[key]

        # 解析結果
        required_qs = [f"Q{i}" for i in range(13, 26)]

        if use_deduction_mode:
            descriptions = parse_defect_descriptions_from_response(response_text, required_questions=required_qs)
            all_defect_descriptions.update(descriptions)
        else:
            result = parse_scores_from_response(response_text, required_questions=required_qs)
            all_scores.update(result['scores'])

    except Exception as e:
        print(f"❌ 後片評分失敗: {e}")
        return None

    # 4. 評分側面 (Q26-Q28)
    print("\n步驟 4/6: 評分側面 (Q26-Q28)...")
    try:
        messages = build_vision_messages_for_section(
            student_id, side_images, "side", range(26, 29),
            use_defect_detection=use_deduction_mode
        )
        response_text, usage_stats = call_vision_model(messages)

        print("✓ 側面評分完成")
        print(f"  Token: {usage_stats['total_tokens']:,}")

        # 累計統計
        for key in ['prompt_tokens', 'completion_tokens', 'total_tokens']:
            total_usage_stats[key] += usage_stats[key]

        # 解析結果
        required_qs = [f"Q{i}" for i in range(26, 29)]

        if use_deduction_mode:
            descriptions = parse_defect_descriptions_from_response(response_text, required_questions=required_qs)
            all_defect_descriptions.update(descriptions)
        else:
            result = parse_scores_from_response(response_text, required_questions=required_qs)
            all_scores.update(result['scores'])

    except Exception as e:
        print(f"❌ 側面評分失敗: {e}")
        return None

    # 如果使用扣分模式，現在根據瑕疵描述計算分數
    if use_deduction_mode:
        print("\n步驟 4.5/6: 根據瑕疵描述計算扣分...")
        all_scores = calculate_all_scores(all_defect_descriptions)

        # 顯示扣分報告
        report = format_scoring_report(all_defect_descriptions, all_scores)
        print("\n" + report)

    # 5. 驗證與顯示結果
    print("\n步驟 5/6: 驗證評分結果...")

    # 確保所有28題都有分數
    if len(all_scores) != 28:
        print(f"❌ 評分不完整：只有 {len(all_scores)}/28 題")
        return None

    # 計算總分
    total = sum(all_scores.values())

    # 驗證分數
    warnings = validate_scores(all_scores)
    if warnings:
        print("\n⚠ 分數驗證警告:")
        for warning in warnings:
            print(f"  {warning}")

    # 顯示統計
    print(f"\n總 Token 使用: {total_usage_stats['total_tokens']:,} tokens")
    cost_info = calculate_cost(total_usage_stats)
    print(f"總費用: ${cost_info['total_cost']:.6f} USD (≈ NT${cost_info['total_cost'] * 31:.4f})")

    # 顯示結果
    print(f"\n{'='*60}")
    print(f"評分完成: {student_id}")
    print(f"{'='*60}")
    print(f"總分: {total} / 100")
    print(f"\n各題分數:")

    # 分組顯示
    print("\n正面照 (Q1-Q12):")
    for i in range(1, 13):
        q = f"Q{i}"
        print(f"  {q}: {all_scores[q]}")

    print("\n後片照 (Q13-Q25):")
    for i in range(13, 26):
        q = f"Q{i}"
        print(f"  {q}: {all_scores[q]}")

    print("\n側面照 (Q26-Q28):")
    for i in range(26, 29):
        q = f"Q{i}"
        print(f"  {q}: {all_scores[q]}")

    # 6. 儲存結果
    print("\n步驟 6/6: 儲存結果...")

    output_data = {
        "student_id": student_id,
        "student_name": student_name,
        "scores": all_scores,
        "total": total,
        "usage_stats": total_usage_stats,
        "cost_usd": cost_info['total_cost']
    }

    # 如果使用扣分模式，也儲存瑕疵描述
    if use_deduction_mode and all_defect_descriptions:
        output_data["defect_descriptions"] = all_defect_descriptions
        output_data["scoring_mode"] = "deduction"
    else:
        output_data["scoring_mode"] = "direct"

    if save_json:
        output_file = config.SCORES_AI_JSON_DIR / f"{student_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"✓ 結果已儲存至: {output_file}")

    return output_data

def main():
    """主程式"""
    if len(sys.argv) < 2:
        print("使用方式: python grade_single_student.py <student_id> [student_name]")
        print("範例: python grade_single_student.py B11276001 林芷綺")
        sys.exit(1)

    student_id = sys.argv[1]
    student_name = sys.argv[2] if len(sys.argv) > 2 else None

    result = grade_student(student_id, student_name)

    if result:
        print(f"\n✓ 評分成功完成")
        sys.exit(0)
    else:
        print(f"\n❌ 評分失敗")
        sys.exit(1)

if __name__ == "__main__":
    main()
