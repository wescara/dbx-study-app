# Exam File Processing Prompt

Use this prompt for processing additional exam question DOCX files.

## Prompt Template

```
I need to extract questions from [FILENAME].docx and create a new Excel workbook in the 
same format as DBx_Questions.xlsx. Here are the requirements:

1. Extract all questions from the DOCX file (one question per page)
2. Create new Excel file matching DBx_Questions.xlsx format
3. Set QID starting at [NEXT_AVAILABLE_QID] - sequentially numbered
4. Populate all required fields:
   - Source: [SOURCE_ABBREVIATION] (e.g., "SG" for Study Guide)
   - Exam: [EXAM_NUMBER] (e.g., 2 for "DCDEA Practice Exam 2")
   - Topic/Subtopic: Map to existing master list values (use the same topics/subtopics 
     already in the workbook)
   - VerificationStatus: "Confirmed" for all new questions
   - Difficulty: Assign as Easy/Medium/Hard based on question complexity
5. Extract and OCR any embedded graphics
6. Update syntax_questions_for_review.csv with any syntax/code-related questions

The file should be saved as [FILENAME]_Questions.xlsx in the data/ folder.
```

## Instructions Before Running

Before using this prompt with a new file, gather this information:

- **Current max QID**: Check the highest QID in `data/DCDEA_Practice_Exam_2_Questions.xlsx` (currently 2089)
- **Source abbreviation**: Identify the source code for the document (e.g., "SG", "PE3", etc.)
- **Exam number**: Determine the exam number/name (e.g., "3" for "Practice Exam 3")
- **Expected question count**: Verify the total number of questions in the DOCX

## Previous Processing Results

- **DCDEA Practice Exam 2**: 45 questions (QID 2045-2089, Source: SG, Exam: 2)
  - 35 syntax questions added to `syntax_questions_for_review.csv`
  - 7 Easy, 23 Medium, 15 Hard difficulty distribution
