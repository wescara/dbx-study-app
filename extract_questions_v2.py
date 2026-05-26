from docx import Document
import pandas as pd
import re
from datetime import datetime

doc_path = 'c:\\dbx-study-app\\data\\DCDEA Practice Exam 2.docx'
doc = Document(doc_path)

questions_data = []
current_question = None
option_lines = []
in_explanation = False
in_documentation = False
explanation_text = ''
documentation_text = ''
correct_answer = ''

for para in doc.paragraphs:
    text = para.text.strip()
    
    if not text:
        continue
    
    # Question start
    if text.startswith('Question '):
        if current_question:
            # Save previous question
            if len(option_lines) >= 2:  # At least question and one option
                current_question['Question'] = option_lines[0] if option_lines else ''
                # Remaining lines are answer options
                for i, opt in enumerate(option_lines[1:]):
                    if i < 6:  # Max 6 options
                        current_question[chr(65 + i)] = opt  # A, B, C, D, E, F
            current_question['Explanation'] = explanation_text.strip()
            current_question['Documentation'] = documentation_text.strip()
            current_question['CorrectAnswer'] = correct_answer
            questions_data.append(current_question)
        
        match = re.match(r'Question (\d+):', text)
        if match:
            current_question = {
                'Number': int(match.group(1)),
                'Question': '',
                'A': '',
                'B': '',
                'C': '',
                'D': '',
                'E': '',
                'F': '',
                'Explanation': '',
                'Documentation': '',
                'CorrectAnswer': ''
            }
            option_lines = []
            in_explanation = False
            in_documentation = False
            explanation_text = ''
            documentation_text = ''
            correct_answer = ''
        continue
    
    if current_question is None:
        continue
    
    # Separator line
    if '---' in text:
        # After separator, next section is explanation
        if not in_explanation and not in_documentation:
            in_explanation = True
        elif in_explanation and not in_documentation:
            in_explanation = False
        continue
    
    # Documentation section
    if text.lower().startswith('documentation'):
        in_explanation = False
        in_documentation = True
        continue
    
    # Correct Answer
    if text.lower().startswith('correct answer'):
        match = re.search(r'Correct Answer[:\s]*(.+)', text, re.IGNORECASE)
        if match:
            correct_answer = match.group(1).strip()
        in_documentation = False
        continue
    
    # Collect text into appropriate section
    if in_explanation:
        explanation_text += text + ' '
    elif in_documentation:
        documentation_text += text + ' '
    else:
        # This is part of question/options section
        option_lines.append(text)

# Add the last question
if current_question and len(option_lines) >= 1:
    current_question['Question'] = option_lines[0] if option_lines else ''
    for i, opt in enumerate(option_lines[1:]):
        if i < 6:
            current_question[chr(65 + i)] = opt
    current_question['Explanation'] = explanation_text.strip()
    current_question['Documentation'] = documentation_text.strip()
    current_question['CorrectAnswer'] = correct_answer
    questions_data.append(current_question)

print(f"Extracted {len(questions_data)} questions")
print(f"\nFirst question example:")
q1 = questions_data[0]
print(f"  Number: {q1['Number']}")
print(f"  Question: {q1['Question'][:80]}")
print(f"  Option A: {q1['A'][:80]}")
print(f"  Option B: {q1['B'][:80]}")
print(f"  Correct Answer: {q1['CorrectAnswer']}")

# Create DataFrame with proper column mapping
df_new = pd.DataFrame()
df_new['Source'] = 'DCDEA Practice Exam 2'
df_new['QID'] = [f"DCDEA2_{i:03d}" for i in range(1, len(questions_data) + 1)]
df_new['Exam'] = 2
df_new['Number'] = [q['Number'] for q in questions_data]
df_new['Topic'] = ''
df_new['Subtopic'] = ''
df_new['Difficulty'] = ''
df_new['Question'] = [q['Question'] for q in questions_data]
df_new['A'] = [q['A'] for q in questions_data]
df_new['B'] = [q['B'] for q in questions_data]
df_new['C'] = [q['C'] for q in questions_data]
df_new['D'] = [q['D'] for q in questions_data]
df_new['E'] = [q['E'] for q in questions_data]
df_new['F'] = [q['F'] for q in questions_data]
df_new['CorrectLetter'] = [q['CorrectAnswer'] for q in questions_data]
df_new['Explanation'] = [q['Explanation'] for q in questions_data]
df_new['Notes'] = ''
df_new['LastReviewed'] = ''
df_new['CorrectCount'] = ''
df_new['IncorrectCount'] = ''
df_new['FlagForReview'] = ''
df_new['Tags'] = ''
df_new['Graphic'] = ''
df_new['Deeper Dive'] = ''
df_new['VerifiedAnswer'] = ''
df_new['VerificationStatus'] = ''
df_new['AnswerMatchesWorkbook'] = ''
df_new['VerificationNotes'] = ''
df_new['VerificationSourceKeys'] = ''
df_new['VerifiedOn'] = ''
df_new['ToDelete'] = ''
df_new['DateAdded'] = datetime.now()

# Save to Excel
output_file = 'c:\\dbx-study-app\\data\\DCDEA_Practice_Exam_2_NEW_QUESTIONS.xlsx'
df_new.to_excel(output_file, index=False, sheet_name='Questions')

print(f"\nCreated Excel file: {output_file}")
print(f"Total questions: {len(df_new)}")
print(f"\nColumn summary:")
print(f"  - All questions have text: {df_new['Question'].str.len().min()} chars min")
print(f"  - All options have text: A={df_new['A'].str.len().min()}, B={df_new['B'].str.len().min()}, C={df_new['C'].str.len().min()}, D={df_new['D'].str.len().min()}")
