# CLAUDE.md
## 使用繁體中文
## 更動或更新無需要撰寫使用手冊或修改紀錄
## 如有更動，回饋訊息只發送修改前後的差異，不是整個文件
## 簡單任務用 Haiku，複雜任務再用 Sonnet
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an AI-powered vision-based grading system for fashion design midterm exams. The system uses OpenAI's Vision API (GPT-4 Vision) to automatically evaluate student work by analyzing multiple photographs of their garment construction projects against a detailed rubric.

The grading focuses on立體剪裁 (draping/3D pattern making) techniques, evaluating 28 different criteria across fabric preparation, pleats execution, alignment, and design complexity based on front, back, and side view photographs.

## Project Structure

```
AI_vision/
├── DATA/
│   ├── input/              # Student submission images organized by student ID and name
│   │   ├── B11276XXX[Name]/ # Each student has a folder with 5 photos (第一張 to 第五張)
│   │   └── 立裁期中成績.xlsx  # Teacher's original grading spreadsheet
│   └── ouput/              # AI-generated grading results (currently empty)
├── DEMO/
│   ├── HIGH/               # High-scoring examples (for reference/testing)
│   ├── Medium/             # Medium-scoring examples
│   └── LOW/                # Low-scoring examples
├── .env                    # OpenAI API key configuration
└── Todo.md                 # Detailed implementation plan in Chinese
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
- Recommended model: `gpt-4o-mini` or equivalent vision-capable model
- Each grading request includes multiple images (front/back/side views)

### Output Format
Per-student results should be structured as:
```json
{
  "student_id": "B11276XXX",
  "scores": {
    "Q1": 2.5,
    "Q2": 3,
    ...
    "Q28": 1.5
  },
  "total": 64.0
}
```

Batch results should be saved as CSV with columns: `student_id, Q1, Q2, ..., Q28, total`

## Development Guidelines

### When Implementing Code
- Create modules in a `src/` directory following the structure outlined in Todo.md:
  - `config.py` - Configuration and environment variables
  - `load_teacher_scores.py` - Excel/CSV processing for teacher scores
  - `build_prompt.py` - Prompt construction with embedded rubric
  - `call_vision_api.py` - OpenAI Vision API integration
  - `grade_single_student.py` - Single student grading logic
  - `grade_batch.py` - Batch processing for all students

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

## Language Note
The project documentation and data are primarily in Traditional Chinese (繁體中文). Student names, file names, and the rubric content use Chinese text. Ensure proper UTF-8 encoding when processing files and strings.
