"""
批次評分腳本：為所有學生進行評分
"""
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import config
from load_teacher_scores import load_teacher_scores
from grade_single_student import grade_student

def batch_grade_all_students(delay_seconds: int = 2, limit: int = None):
    """
    批次評分所有學生

    Args:
        delay_seconds: 每次 API 呼叫之間的延遲秒數（避免 rate limit）
        limit: 限制評分學生數量，None 表示評分所有學生
    """
    print("="*80)
    print("批次評分系統 - AI 視覺評分")
    print("="*80)
    print(f"開始時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. 載入學生名單
    print("步驟 1: 載入學生名單...")
    try:
        df_teachers = load_teacher_scores()
        students = df_teachers[['student_id', 'student_name']].values.tolist()

        # 如果有限制數量，只取前 N 位
        if limit is not None:
            students = students[:limit]
            print(f"✓ 載入 {len(students)} 位學生（限制評分數量）")
        else:
            print(f"✓ 載入 {len(students)} 位學生")
    except Exception as e:
        print(f"❌ 載入學生名單失敗: {e}")
        return

    # 2. 批次評分
    print(f"\n步驟 2: 開始批次評分...")
    print(f"  每次評分間隔: {delay_seconds} 秒")
    print()

    results = []
    failed_students = []
    total_tokens = 0
    total_cost = 0.0

    for idx, (student_id, student_name) in enumerate(students, 1):
        print(f"\n[{idx}/{len(students)}] 評分學生: {student_id} {student_name}")
        print("-" * 80)

        try:
            result = grade_student(student_id, student_name, save_json=True)

            if result:
                results.append(result)

                # 累計 token 使用量和費用
                if 'usage_stats' in result:
                    total_tokens += result['usage_stats']['total_tokens']
                if 'cost_usd' in result:
                    total_cost += result['cost_usd']

                print(f"✓ 完成 ({idx}/{len(students)})")
            else:
                failed_students.append({
                    'student_id': student_id,
                    'student_name': student_name,
                    'reason': '評分失敗'
                })
                print(f"❌ 失敗 ({idx}/{len(students)})")

        except Exception as e:
            print(f"❌ 發生錯誤: {e}")
            failed_students.append({
                'student_id': student_id,
                'student_name': student_name,
                'reason': str(e)
            })

        # 延遲以避免 API rate limit
        if idx < len(students):
            print(f"\n⏳ 等待 {delay_seconds} 秒...")
            time.sleep(delay_seconds)

    # 3. 彙整結果
    print("\n" + "="*80)
    print("步驟 3: 彙整評分結果...")
    print("="*80)

    if not results:
        print("❌ 沒有成功的評分結果")
        return

    # 建立 DataFrame
    rows = []
    for result in results:
        row = {
            'student_id': result['student_id'],
            'student_name': result['student_name'],
        }
        # 加入各題分數
        for q in [f'Q{i}' for i in range(1, 29)]:
            row[q] = result['scores'].get(q, None)
        row['total'] = result['total']
        rows.append(row)

    df_ai_scores = pd.DataFrame(rows)

    # 4. 儲存結果
    output_csv = config.SCORES_AI_DIR / "scores_ai_final.csv"
    df_ai_scores.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"\n✓ AI 評分結果已儲存至: {output_csv}")

    # 5. 儲存失敗名單
    if failed_students:
        failed_log = config.FAILED_STUDENTS_LOG
        with open(failed_log, 'w', encoding='utf-8') as f:
            f.write(f"失敗學生名單 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*60 + "\n\n")
            for item in failed_students:
                f.write(f"學號: {item['student_id']}\n")
                f.write(f"姓名: {item['student_name']}\n")
                f.write(f"原因: {item['reason']}\n")
                f.write("-"*60 + "\n")

        print(f"\n⚠ {len(failed_students)} 位學生評分失敗")
        print(f"  失敗名單已儲存至: {failed_log}")

    # 6. 顯示統計
    print("\n" + "="*80)
    print("批次評分完成統計")
    print("="*80)
    print(f"總學生數: {len(students)}")
    print(f"成功評分: {len(results)} 位")
    print(f"失敗評分: {len(failed_students)} 位")
    print(f"成功率: {len(results)/len(students)*100:.1f}%")

    if results:
        total_scores = [r['total'] for r in results]
        print(f"\nAI 評分統計:")
        print(f"  平均分: {sum(total_scores)/len(total_scores):.1f}")
        print(f"  最高分: {max(total_scores)}")
        print(f"  最低分: {min(total_scores)}")

    # 顯示 API 使用統計
    print(f"\n{'='*80}")
    print("API 使用統計")
    print(f"{'='*80}")
    print(f"總 Token 使用量: {total_tokens:,} tokens")
    print(f"總費用 (USD): ${total_cost:.6f}")
    print(f"總費用 (TWD): NT${total_cost * 31:.2f} (以匯率 1:31 計算)")
    if len(results) > 0:
        print(f"平均每位學生:")
        print(f"  Token: {total_tokens/len(results):,.0f} tokens")
        print(f"  費用: ${total_cost/len(results):.6f} USD (≈ NT${total_cost/len(results)*31:.4f})")

    print(f"\n結束時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

def compare_with_teacher_scores():
    """
    比較 AI 評分與老師評分
    """
    print("\n" + "="*80)
    print("比較 AI 評分與老師評分")
    print("="*80)

    # 載入 AI 評分
    ai_scores_file = config.SCORES_AI_DIR / "scores_ai_final.csv"
    if not ai_scores_file.exists():
        print("❌ 找不到 AI 評分結果檔案")
        return

    df_ai = pd.read_csv(ai_scores_file)

    # 載入老師評分
    df_teacher = load_teacher_scores()

    # 合併
    df_compare = pd.merge(
        df_teacher[['student_id', 'student_name', 'teacher_avg']],
        df_ai[['student_id', 'total']],
        on='student_id',
        how='inner'
    )

    df_compare = df_compare.rename(columns={'total': 'ai_total'})

    # 計算差異
    df_compare['difference'] = df_compare['ai_total'] - df_compare['teacher_avg']
    df_compare['abs_difference'] = df_compare['difference'].abs()

    # 儲存比較結果
    compare_file = config.SCORES_AI_DIR / "compare_ai_teacher.csv"
    df_compare.to_csv(compare_file, index=False, encoding='utf-8-sig')
    print(f"\n✓ 比較結果已儲存至: {compare_file}")

    # 顯示統計
    print(f"\n比較統計:")
    print(f"  樣本數: {len(df_compare)}")
    print(f"  平均差異: {df_compare['difference'].mean():.2f}")
    print(f"  平均絕對差異: {df_compare['abs_difference'].mean():.2f}")
    print(f"  差異標準差: {df_compare['difference'].std():.2f}")
    print(f"  最大正差異: {df_compare['difference'].max():.2f}")
    print(f"  最大負差異: {df_compare['difference'].min():.2f}")

    # 顯示差異最大的幾位學生
    print(f"\n差異最大的 5 位學生:")
    top_diff = df_compare.nlargest(5, 'abs_difference')[['student_id', 'student_name', 'teacher_avg', 'ai_total', 'difference']]
    print(top_diff.to_string(index=False))

def main():
    """主程式"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--compare':
        # 只執行比較
        compare_with_teacher_scores()
    else:
        # 執行批次評分
        delay = 2  # 預設延遲 2 秒
        limit = 10  # 預設評分所有學生

        if len(sys.argv) > 1:
            try:
                delay = int(sys.argv[1])
            except ValueError:
                print("警告: 無效的延遲時間，使用預設值 2 秒")

        if len(sys.argv) > 2:
            try:
                limit = int(sys.argv[2])
                print(f"限制評分: 前 {limit} 位學生")
            except ValueError:
                print("警告: 無效的學生數量限制")

        batch_grade_all_students(delay_seconds=delay, limit=limit)

        # 評分完成後自動執行比較
        print("\n")
        compare_with_teacher_scores()

if __name__ == "__main__":
    main()
