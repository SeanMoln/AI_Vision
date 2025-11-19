"""
分析評分差異的工具
"""
import pandas as pd
import numpy as np
import config

def analyze_teacher_consistency():
    """分析老師評分的一致性"""
    df = pd.read_csv(config.SCORES_TEACHER_DIR / "midterm_scores_clean.csv")

    print("="*80)
    print("老師評分一致性分析")
    print("="*80)

    # 計算三位老師之間的差異
    df['teacher_std'] = df[['teacher_chen', 'teacher_hsia', 'teacher_hsu']].std(axis=1)
    df['teacher_range'] = df[['teacher_chen', 'teacher_hsia', 'teacher_hsu']].max(axis=1) - \
                          df[['teacher_chen', 'teacher_hsia', 'teacher_hsu']].min(axis=1)

    print(f"\n老師評分統計:")
    print(f"  平均標準差: {df['teacher_std'].mean():.2f}")
    print(f"  平均分數範圍: {df['teacher_range'].mean():.2f}")
    print(f"  最大分數範圍: {df['teacher_range'].max():.2f}")

    print(f"\n評分差異最大的 10 位學生:")
    top_diff = df.nlargest(10, 'teacher_range')[
        ['student_id', 'student_name', 'teacher_chen', 'teacher_hsia',
         'teacher_hsu', 'teacher_avg', 'teacher_range']
    ]
    print(top_diff.to_string(index=False))

    # 分析每位老師的評分分布
    print(f"\n\n各老師評分分布:")
    for teacher in ['teacher_chen', 'teacher_hsia', 'teacher_hsu']:
        scores = df[teacher].dropna()
        print(f"\n{teacher}:")
        print(f"  平均: {scores.mean():.2f}")
        print(f"  標準差: {scores.std():.2f}")
        print(f"  最高: {scores.max():.2f}")
        print(f"  最低: {scores.min():.2f}")

def analyze_ai_vs_teachers():
    """分析 AI 評分與老師評分的差異"""
    df_compare = pd.read_csv(config.SCORES_AI_DIR / "compare_ai_teacher.csv")
    df_teacher = pd.read_csv(config.SCORES_TEACHER_DIR / "midterm_scores_clean.csv")

    # 合併資料
    df_merged = df_compare.merge(
        df_teacher[['student_id', 'teacher_chen', 'teacher_hsia', 'teacher_hsu']],
        on='student_id'
    )

    print("\n" + "="*80)
    print("AI 與各老師評分差異比較")
    print("="*80)

    # 計算 AI 與每位老師的差異
    df_merged['diff_chen'] = df_merged['ai_total'] - df_merged['teacher_chen']
    df_merged['diff_hsia'] = df_merged['ai_total'] - df_merged['teacher_hsia']
    df_merged['diff_hsu'] = df_merged['ai_total'] - df_merged['teacher_hsu']

    print(f"\nAI 與各老師的平均差異:")
    print(f"  AI vs 陳老師: {df_merged['diff_chen'].mean():.2f} (±{df_merged['diff_chen'].std():.2f})")
    print(f"  AI vs 夏老師: {df_merged['diff_hsia'].mean():.2f} (±{df_merged['diff_hsia'].std():.2f})")
    print(f"  AI vs 徐老師: {df_merged['diff_hsu'].mean():.2f} (±{df_merged['diff_hsu'].std():.2f})")
    print(f"  AI vs 平均: {df_merged['difference'].mean():.2f} (±{df_merged['difference'].std():.2f})")

    # 詳細比較
    print(f"\n詳細比較:")
    detail = df_merged[[
        'student_id', 'student_name',
        'teacher_chen', 'teacher_hsia', 'teacher_hsu',
        'teacher_avg', 'ai_total',
        'diff_chen', 'diff_hsia', 'diff_hsu', 'difference'
    ]]
    print(detail.to_string(index=False))

    # 分析 AI 更接近哪位老師
    print(f"\n\nAI 評分接近度分析:")
    abs_diffs = pd.DataFrame({
        '陳老師': df_merged['diff_chen'].abs(),
        '夏老師': df_merged['diff_hsia'].abs(),
        '徐老師': df_merged['diff_hsu'].abs()
    })
    print(f"平均絕對差異:")
    print(abs_diffs.mean().to_string())

    closest_teacher = abs_diffs.idxmin(axis=1)
    print(f"\n各學生 AI 評分最接近的老師:")
    for idx, row in df_merged.iterrows():
        print(f"  {row['student_name']}: {closest_teacher.iloc[idx]}")

def suggest_improvements():
    """建議如何改善評分"""
    df_compare = pd.read_csv(config.SCORES_AI_DIR / "compare_ai_teacher.csv")

    print("\n" + "="*80)
    print("評分差異改善建議")
    print("="*80)

    avg_diff = df_compare['difference'].mean()
    avg_abs_diff = df_compare['abs_difference'].mean()

    print(f"\n當前狀況:")
    print(f"  平均差異: {avg_diff:.2f} 分")
    print(f"  平均絕對差異: {avg_abs_diff:.2f} 分")

    if avg_diff > 15:
        print(f"\n建議:")
        print(f"  1. AI 評分明顯偏高，建議:")
        print(f"     - 在 system prompt 中加入更嚴格的扣分標準")
        print(f"     - 降低設計複雜度項目（Q11, Q12, Q22, Q23）的分數")
        print(f"     - 對瑕疵要更敏感，發現問題立即扣分")
    elif avg_diff > 10:
        print(f"\n建議:")
        print(f"  1. AI 評分略偏高，可以:")
        print(f"     - 強調「完美才給滿分」的原則")
        print(f"     - 對平整度、對齊等項目更嚴格")
    elif avg_diff < -10:
        print(f"\n建議:")
        print(f"  1. AI 評分偏低，可以:")
        print(f"     - 適度放寬評分標準")
        print(f"     - 給予學生更多肯定")
    else:
        print(f"\n建議:")
        print(f"  1. AI 評分接近老師平均，差異合理")
        print(f"  2. 可以繼續優化細節項目的評分標準")

    print(f"\n  3. 考慮調整的項目:")
    # 讀取一個 JSON 檔案分析哪些項目可能需要調整
    import json
    json_files = list(config.SCORES_AI_JSON_DIR.glob("*.json"))
    if json_files:
        with open(json_files[0], 'r', encoding='utf-8') as f:
            sample = json.load(f)
            scores = sample['scores']

            high_scores = [(q, s) for q, s in scores.items() if s >= 5]
            if high_scores:
                print(f"     高分項目（可能需要更嚴格）:")
                for q, s in high_scores[:5]:
                    print(f"       {q}: {s}")

def main():
    """主程式"""
    analyze_teacher_consistency()
    print("\n\n")
    analyze_ai_vs_teachers()
    print("\n\n")
    suggest_improvements()

if __name__ == "__main__":
    main()
