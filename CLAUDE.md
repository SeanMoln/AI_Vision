# CLAUDE.md
## 使用繁體中文
## 更動或更新無需要撰寫使用手冊或修改紀錄
## 如有更動，回饋訊息只發送修改前後的差異，不是整個文件
## 簡單任務用 Haiku，複雜任務再用 Sonnet
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered vision-based grading system for fashion design midterm exams. The system uses OpenAI's Vision API (GPT-4 Vision) to automatically evaluate student work by analyzing multiple photographs of their garment construction projects against a detailed rubric.

The grading focuses on立體剪裁 (draping/3D pattern making) techniques, evaluating 28 different criteria across fabric preparation, pleats execution, alignment, and design complexity based on front, back, and side view photographs.

### Key Innovation: Deduction-Based Scoring System

Unlike traditional direct scoring approaches where AI assigns scores directly, this system implements a two-stage approach:

1. **Defect Detection Stage**: AI analyzes images and outputs defect descriptions only (e.g., "有明顯皺摺", "完全對齊", "簡單設計")
2. **Program-Level Deduction**: Python logic analyzes keywords in descriptions and calculates scores based on severity levels

This approach significantly reduces AI's tendency to be overly optimistic (the "善意理解" problem) and provides more consistent scoring aligned with strict academic standards.

## Project Structure

```
AI_vision/
├── DATA/
│   ├── input/                          # Student submission images
│   │   ├── B11276XXX[Name]/           # Each student folder with 5 photos
│   │   └── 立裁期中成績.xlsx           # Teacher's grading spreadsheet
│   ├── scores_ai/                      # AI grading output
│   │   ├── json/                       # Per-student detailed JSON files
│   │   ├── scores_ai_final.csv         # Batch grading results
│   │   └── compare_ai_teacher.csv      # Comparison with teacher scores
│   └── scores_teacher/                 # Cleaned teacher scores (CSV)
├── src/
│   ├── config.py                       # Configuration and paths
│   ├── load_teacher_scores.py          # Excel → CSV conversion
│   ├── call_vision_api.py              # OpenAI Vision API wrapper
│   ├── deduction_scoring.py            # ⭐ Keyword-based deduction logic
│   ├── grade_single_student.py         # Single student evaluation
│   └── grade_batch.py                  # Batch processing for all students
├── prompts/
│   ├── rubric_ai_friendly.md           # Rubric in AI-readable format
│   ├── vision_system_prompt.txt        # Old direct scoring prompt (deprecated)
│   └── vision_defect_detection_prompt.txt  # ⭐ New defect detection prompt
├── logs/                               # Error logs and failed API responses
├── .env                                # OpenAI API key (NOT in git)
├── .gitignore                          # Excludes .env and student data
├── run_single_student.sh               # Shell script for easy testing
└── requirements.txt                    # Python dependencies
```

## Data Organization

### Student Image Naming Convention
Each student folder contains exactly 5 images named:
- `{StudentID}{StudentName}第一張.jpg` (Image 1 - typically front view)
- `{StudentID}{StudentName}第二張.jpg` (Image 2 - typically back view)
- `{StudentID}{StudentName}第三張.jpg` (Image 3 - typically side view)
- `{StudentID}{StudentName}第四張.jpg` (Image 4 - additional angle)
- `{StudentID}{StudentName}第五張.jpg` (Image 5 - additional angle)

Note: Some variations exist with spaces (e.g., "B11276028 呂沛橙") or extra punctuation (e.g., "第一張..jpg").

### Student ID Format
Student IDs follow the pattern: `B11276XXX` where XXX is a unique identifier.

## Implementation Roadmap

The [Todo.md](Todo.md) file contains a comprehensive 7-phase implementation plan:

1. **Phase 0**: Project structure setup
2. **Phase 1**: Convert the rubric from DOCX to AI-readable format (JSON/Markdown) with 28 questions (Q1-Q28)
3. **Phase 2**: Extract and clean teacher scores from Excel into CSV format
4. **Phase 3**: Define output formats (per-student JSON and batch CSV)
5. **Phase 4**: Design Vision API prompts with embedded rubric rules
6. **Phase 5**: Implement single-student grading pipeline
7. **Phase 6**: Implement batch grading for all students
8. **Phase 7**: Compare AI scores with teacher scores for validation

## Key Technical Requirements

### Rubric Structure
The grading rubric evaluates 28 criteria (Q1-Q28) with specific score thresholds:
- Each question has a maximum score (e.g., +3, +5, +6)
- Scores are discretized to specific values (e.g., Q1: 3, 2.5, 1.5, 1, 0)
- Evaluation criteria are based on visual features observable in photographs:
  - Fabric smoothness and ironing quality
  - Pleat execution and transfer accuracy
  - Center line alignment
  - Appropriate ease/allowance
  - Absence of pulling or wrinkling
  - Design complexity

### API Configuration
The system uses OpenAI's Vision API:
- API key stored in `.env` as `OPENAI_API_KEY`
- **Recommended model**: `gpt-4o` (NOT gpt-4o-mini) for better defect detection accuracy
- Each grading request includes multiple images (front/back/side views)
- Three separate API calls per student to reduce token usage (front/back/side)

### Deduction Scoring Logic

The core innovation is in `src/deduction_scoring.py`:

1. **Defect Keywords Dictionary**: Maps Chinese defect descriptions to severity levels (0-4)
   - Level 0 (優良): "完全對齊", "精準轉移", "適當鬆份" → Full marks
   - Level 1 (輕微): "不錯", "中等複雜" → Minor deduction
   - Level 2 (中度): "明顯", "不平整", "簡單" → Medium deduction
   - Level 3 (重度): "嚴重", "很" → Heavy deduction
   - Level 4 (極差): "沒有", "看不" → Zero marks

2. **Euphemistic Words Banned**: The prompt explicitly prohibits words like "稍微", "少許", "些微" to force AI to give direct assessments

3. **Global Adjustment Mechanism**: If AI shows optimism bias (>40% medium+ defects but >30% excellent ratings), all "excellent" ratings are downgraded by one level

### Output Format
Per-student results now include both scores and defect descriptions:
```json
{
  "student_id": "B11276XXX",
  "student_name": "姓名",
  "scores": {
    "Q1": 1.5,
    "Q2": 3,
    ...
    "Q28": 1
  },
  "total": 55.0,
  "defect_descriptions": {
    "Q1": "有明顯皺摺",
    "Q2": "完全對齊",
    ...
  },
  "scoring_mode": "deduction",
  "usage_stats": {
    "total_tokens": 15942,
    "model": "gpt-4o"
  },
  "cost_usd": 0.0422
}
```

Batch results should be saved as CSV with columns: `student_id, Q1, Q2, ..., Q28, total`

## Development Guidelines

### When Implementing Code
- All core modules are in `src/` directory:
  - `config.py` - Configuration and environment variables
  - `load_teacher_scores.py` - Excel/CSV processing for teacher scores
  - `call_vision_api.py` - OpenAI Vision API integration with base64 image encoding
  - **`deduction_scoring.py`** - Core deduction logic (keyword → score mapping)
  - `grade_single_student.py` - Single student evaluation pipeline
  - `grade_batch.py` - Batch processing for all students

### Important Implementation Notes

1. **Two-Stage Evaluation**:
   - AI should ONLY output defect descriptions, NOT scores
   - Use `prompts/vision_defect_detection_prompt.txt` as the system prompt
   - Python code in `deduction_scoring.py` handles all score calculation

2. **Keyword Matching Strategy**:
   - Keywords are checked in the order they appear in DEFECT_KEYWORDS
   - The highest severity level found wins
   - Example: "很不平整" matches both "很" (level 3) and "不平整" (level 2) → level 3 wins

3. **Global Adjustment Trigger**:
   - Only triggers when BOTH conditions are met:
     - (中度 + 重度 + 極差) / total > 40%
     - 優良 / total > 30%
   - This prevents over-correction when AI is appropriately harsh

### Error Handling
- Handle missing images gracefully (some students may have incomplete submissions)
- Log failed evaluations to `logs/failed_students.txt`
- Store unparseable API responses to `logs/` for debugging
- Validate that all scores fall within the allowed discrete values for each question

### Data Processing
- The Excel file `立裁期中成績.xlsx` contains teacher's original scores for validation
- Student names include Chinese characters - ensure UTF-8 encoding throughout
- Image file paths may have inconsistent naming (spaces, punctuation) - implement robust path resolution

### Score Validation
- AI-generated scores must match the discrete values defined in the rubric
- No free-form decimals allowed (e.g., Q1 cannot be 2.3, only 3, 2.5, 1.5, 1, or 0)
- Implement sanity checks comparing AI scores against teacher score distributions

## Performance Metrics

### Test Results (Student B11276024)
- Teacher score: **29.5 / 100**
- AI scoring progression:
  - Old direct scoring: 81.5 → 85.5 (over-optimistic)
  - Deduction with lenient words: 70.0 → 75.5 (still high)
  - **Deduction + banned euphemisms: 55.0** ✓
- **Improvement**: 34-point reduction from peak (38% decrease)
- **Gap with teacher**: Reduced from 59.5 to 25.5 points

### Cost Analysis (gpt-4o)
- Tokens per student: ~16,000 tokens (split across 3 API calls)
- Cost per student: ~$0.04 USD (≈ NT$1.3)
- For 30 students: ~$1.2 USD (≈ NT$40)

### Known Limitations
- AI vision models inherently tend toward "善意理解" (generous interpretation)
- For very low-scoring work (<30 points), AI may still overestimate by 20-30 points
- Recommend using AI scores as reference, not replacement for human grading
- Works best for medium-range scores (40-80 points)

## Language Note
The project documentation and data are primarily in Traditional Chinese (繁體中文). Student names, file names, and the rubric content use Chinese text. Ensure proper UTF-8 encoding when processing files and strings.

## Version History

### v2.0 - Deduction-Based Scoring (Current)
- Implemented two-stage evaluation (defect detection → score calculation)
- Banned euphemistic language in prompts
- Added global optimism adjustment mechanism
- Achieved 38% improvement in score accuracy for low-scoring work

### v1.0 - Direct Scoring (Deprecated)
- AI directly assigned scores to each question
- Suffered from severe optimism bias
- Archived in `prompts/vision_system_prompt.txt`
