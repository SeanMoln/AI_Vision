"""
載入並處理老師成績資料
"""
import pandas as pd
from pathlib import Path
import config

def load_teacher_scores(excel_path: str = None) -> pd.DataFrame:
    """
    載入老師評分的 Excel 檔案

    Args:
        excel_path: Excel 檔案路徑，預設為 DATA/input/立裁期中成績.xlsx

    Returns:
        處理後的 DataFrame
    """
    if excel_path is None:
        excel_path = config.IMAGE_ROOT / "立裁期中成績.xlsx"

    df = pd.read_excel(excel_path)

    # 清理欄位名稱
    df = df.rename(columns={
        '學號': 'student_id',
        '學生姓名': 'student_name',
        '陳老師': 'teacher_chen',
        '夏老師': 'teacher_hsia',
        '徐老師': 'teacher_hsu',
        'AI': 'ai_score',
        '三位平均': 'teacher_avg',
        '平均': 'final_avg'
    })

    # 移除空白列
    df = df.dropna(subset=['student_id'])

    return df

def save_teacher_scores_csv(df: pd.DataFrame, output_path: str = None):
    """
    儲存清理後的成績到 CSV

    Args:
        df: 成績 DataFrame
        output_path: 輸出路徑，預設為 DATA/scores_teacher/midterm_scores_clean.csv
    """
    if output_path is None:
        output_path = config.SCORES_TEACHER_DIR / "midterm_scores_clean.csv"

    df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"✓ 已儲存清理後的成績到: {output_path}")

def get_student_list(df: pd.DataFrame) -> list:
    """
    從成績 DataFrame 中取得學生 ID 列表

    Args:
        df: 成績 DataFrame

    Returns:
        學生 ID 列表
    """
    return df['student_id'].tolist()

def save_student_list(student_ids: list, output_path: str = None):
    """
    儲存學生 ID 列表到文字檔

    Args:
        student_ids: 學生 ID 列表
        output_path: 輸出路徑，預設為 DATA/students_list.txt
    """
    if output_path is None:
        output_path = config.DATA_DIR / "students_list.txt"

    with open(output_path, 'w', encoding='utf-8') as f:
        for student_id in student_ids:
            f.write(f"{student_id}\n")

    print(f"✓ 已儲存學生名單到: {output_path}")

if __name__ == "__main__":
    # 載入成績
    df = load_teacher_scores()
    print(f"載入 {len(df)} 位學生的成績")
    print(f"\n欄位: {list(df.columns)}")
    print(f"\n前3筆資料:")
    print(df.head(3))

    # 儲存清理後的 CSV
    save_teacher_scores_csv(df)

    # 取得並儲存學生名單
    student_ids = get_student_list(df)
    save_student_list(student_ids)
    print(f"\n✓ 共 {len(student_ids)} 位學生")
