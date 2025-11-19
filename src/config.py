"""
配置文件：專案設定與環境變數
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 載入 .env 檔案
load_dotenv()

# 專案根目錄
PROJECT_ROOT = Path(__file__).parent.parent

# OpenAI API 設定
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gpt-4o-mini")

# 資料路徑
DATA_DIR = PROJECT_ROOT / "DATA"
IMAGE_ROOT = DATA_DIR / "input"
OUTPUT_DIR = DATA_DIR / "ouput"  # 保持原始拼寫
SCORES_TEACHER_DIR = DATA_DIR / "scores_teacher"
SCORES_AI_DIR = DATA_DIR / "scores_ai"
SCORES_AI_JSON_DIR = SCORES_AI_DIR / "json"

# Prompts 路徑
PROMPTS_DIR = PROJECT_ROOT / "prompts"
RUBRIC_FILE = PROMPTS_DIR / "rubric_ai_friendly.md"
SYSTEM_PROMPT_FILE = PROMPTS_DIR / "vision_system_prompt.txt"

# Logs 路徑
LOGS_DIR = PROJECT_ROOT / "logs"
FAILED_STUDENTS_LOG = LOGS_DIR / "failed_students.txt"

# 評分設定
TOTAL_QUESTIONS = 28  # Q1 ~ Q28

# 確保目錄存在
for directory in [SCORES_TEACHER_DIR, SCORES_AI_DIR, SCORES_AI_JSON_DIR,
                  PROMPTS_DIR, LOGS_DIR, OUTPUT_DIR]:
    directory.mkdir(parents=True, exist_ok=True)
