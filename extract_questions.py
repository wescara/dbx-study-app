from docx import Document
import pandas as pd
import re
from datetime import datetime

doc_path = 'c:\\dbx-study-app\\data\\DCDEA Practice Exam 2.docx'
doc = Document(doc_path)

questions_data = []
current_question = None
current_section = None

for para in doc.paragraphs:
    text = para.text.strip()
    
    if not text:
        continue
    
    # Check if this is a question start
    if text.startswith('Question '):
        if current_question:
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
                'CorrectLetter': '',
                'Explanation': '',
                'Documentation': '',
                'CorrectAnswer': ''
            }
            current_section = 'question'
        continue
    
    if current_question is None:
        continue
    
    # Line separator indicates end of options
    if '---' in text:
        current_section = 'separator'
        continue
    
    # Overall explanation section
    if text.lower().startswith('overall explanation'):
        current_section = 'explanation'
        continue
    
    # Documentation section
    if text.lower().startswith('documentation'):
        current_section = 'documentation'
        continue
    
    # Correct Answer section
    if text.lower().startswith('correct answer'):
        match = re.search(r'Correct Answer[:\s]*(.+)', text, re.IGNORECASE)
        if match:
            current_question['CorrectAnswer'] = match.group(1).strip()
        current_section = None
        continue
    
    # Parse answer options
    if current_section == 'question' and len(text) > 2 and text[0] in 'ABCDEF' and text[1] == ':':
        letter = text[0]
        answer_text = text[2:].strip()
        current_question[letter] = answer_text
    elif current_section == 'question':
        if current_question['Question']:
            current_question['Question'] += ' ' + text
        else:
            current_question['Question'] += text
    elif current_section == 'explanation':
        current_question['Explanation'] += text + '\n'
    elif current_section == 'documentation':
        current_question['Documentation'] += text + '\n'

# Add the last question
if current_question:
    questions_data.append(current_question)

print(f"Extracted {len(questions_data)} questions")
print(f"\nFirst question example:")
q1 = questions_data[0]
print(f"  Number: {q1['Number']}")
print(f"  Question: {q1['Question'][:100]}...")
print(f"  Correct Answer: {q1['CorrectAnswer']}")

# Create DataFrame
df = pd.DataFrame(questions_data)

# Now add the other columns from master deck template
master_columns = [
    'Source', 'QID', 'Exam', 'Number', 'Topic', 'Subtopic', 'Difficulty', 
    'Question', 'A', 'B', 'C', 'D', 'E', 'F', 'CorrectLetter', 'Explanation', 
    'Notes', 'LastReviewed', 'CorrectCount', 'IncorrectCount', 'FlagForReview', 
    'Tags', 'Graphic', 'Deeper Dive', 'VerifiedAnswer', 'VerificationStatus', 
    'AnswerMatchesWorkbook', 'VerificationNotes', 'VerificationSourceKeys', 
    'VerifiedOn', 'ToDelete', 'DateAdded'
]

# Reorder and add missing columns
df_new = pd.DataFrame()
df_new['Source'] = 'DCDEA Practice Exam 2'
df_new['QID'] = df['Number'].astype(str).str.zfill(4)  # Will be filled in properly
df_new['Exam'] = 2
df_new['Number'] = df['Number']
df_new['Topic'] = ''
df_new['Subtopic'] = ''
df_new['Difficulty'] = ''
df_new['Question'] = df['Question']
df_new['A'] = df['A']
df_new['B'] = df['B']
df_new['C'] = df['C']
df_new['D'] = df['D']
df_new['E'] = df['E']
df_new['F'] = df['F']

# Extract correct letters from CorrectAnswer
df_new['CorrectLetter'] = df['CorrectAnswer'].str.extract(r'(\d+)')  # Will need manual review
df_new['Explanation'] = df['Explanation'].str.strip()
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

print(f"\n✓ Created Excel file: {output_file}")
print(f"  Total questions: {len(df_new)}")
