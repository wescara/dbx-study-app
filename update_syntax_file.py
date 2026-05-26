import pandas as pd
import os

# Load both files
dcdea_df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
syntax_df = pd.read_csv('data/syntax_questions_for_review.csv')

# Filter DCDEA questions
dcdea_questions = dcdea_df[(dcdea_df['QID'] >= 2045) & (dcdea_df['QID'] <= 2089)].copy()

# Keywords that indicate syntax/code questions
syntax_keywords = [
    'SQL', 'PYTHON', 'PYSPARK', 'syntax', 'code', 'command', 'statement',
    'script', 'query', 'function', 'parameter', 'argument', 'option',
    'CREATE TABLE', 'SELECT', 'WHERE', 'JOIN', 'GROUP BY',
    'def ', '():', 'import ', 'lambda', 'transform', 'udf',
    'spark.sql', 'spark.read', '.write', '.option', '.mode'
]

new_syntax_rows = []

for idx, row in dcdea_questions.iterrows():
    question_text = str(row['Question']).upper()
    
    # Check if question contains syntax keywords
    has_syntax = any(keyword.upper() in question_text for keyword in syntax_keywords)
    
    if has_syntax:
        try:
            # Get option letter
            correct_letter = str(row['CorrectLetter']).strip()
            
            # Map letter to option column
            if ',' in correct_letter:
                # Multiple answers - just take first
                correct_letter = correct_letter.split(',')[0]
            
            if correct_letter in ['A', 'B', 'C', 'D', 'E', 'F']:
                correct_answer = str(row[correct_letter])
            else:
                correct_answer = ''
            
            new_row = {
                'QID': int(row['QID']),
                'Topic': row['Topic'],
                'Subtopic': row['Subtopic'],
                'Question': row['Question'],
                'CorrectLetter': correct_letter,
                'CorrectAnswer': correct_answer,
                'Note': 'From DCDEA Practice Exam 2',
                'miss_count': 0
            }
            new_syntax_rows.append(new_row)
        except Exception as e:
            print(f"Error processing QID {row['QID']}: {e}")

# Create DataFrame from new rows
new_syntax_df = pd.DataFrame(new_syntax_rows)

# Append to existing syntax file
updated_syntax_df = pd.concat([syntax_df, new_syntax_df], ignore_index=True)

# Remove duplicates by QID (in case any existed)
updated_syntax_df = updated_syntax_df.drop_duplicates(subset=['QID'], keep='first')

# Save to temp file first
temp_file = 'data/syntax_questions_for_review_TEMP.csv'
updated_syntax_df.to_csv(temp_file, index=False, quotechar='"', quoting=1)

# Replace original file
import shutil
final_file = 'data/syntax_questions_for_review.csv'
if os.path.exists(final_file):
    os.remove(final_file)
shutil.move(temp_file, final_file)

print(f"✓ Updated syntax file successfully")
print(f"\nOriginal count: {len(syntax_df)}")
print(f"New syntax questions added: {len(new_syntax_df)}")
print(f"Total count: {len(updated_syntax_df)}")
print(f"\nSample new entries:")
for idx in range(min(3, len(new_syntax_df))):
    row = new_syntax_df.iloc[idx]
    print(f"  QID {row['QID']}: {row['Question'][:70]}...")
    print(f"    Answer: {row['CorrectAnswer'][:70]}...\n")
