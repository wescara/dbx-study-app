import pandas as pd
import re

# Load both files
dcdea_df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
syntax_df = pd.read_csv('data/syntax_questions_for_review.csv')

# Filter DCDEA questions (QID 2045-2089)
dcdea_questions = dcdea_df[(dcdea_df['QID'] >= 2045) & (dcdea_df['QID'] <= 2089)].copy()

# Keywords that indicate syntax/code questions
syntax_keywords = [
    'SQL', 'PYTHON', 'PYSPARK', 'syntax', 'code', 'command', 'statement',
    'script', 'query', 'function', 'parameter', 'argument', 'option',
    'CREATE TABLE', 'SELECT', 'WHERE', 'JOIN', 'GROUP BY',
    'def ', '():', 'import ', 'lambda', 'transform', 'udf',
    'spark.sql', 'spark.read', '.write', '.option', '.mode'
]

syntax_questions_found = []

for idx, row in dcdea_questions.iterrows():
    question_text = str(row['Question']).upper()
    
    # Check if question contains syntax keywords
    has_syntax = any(keyword.upper() in question_text for keyword in syntax_keywords)
    
    if has_syntax:
        # Extract the correct answer text
        try:
            # Get option letter
            correct_letter = str(row['CorrectLetter']).strip()
            
            # Map letter to option column
            letter_to_col = {'A': 'A', 'B': 'B', 'C': 'C', 
                           'D': 'D', 'E': 'E', 'F': 'F'}
            
            if ',' in correct_letter:
                # Multiple answers - just take first for now
                correct_letter = correct_letter.split(',')[0]
            
            if correct_letter in letter_to_col:
                correct_answer = str(row[letter_to_col[correct_letter]])
            else:
                correct_answer = ''
            
            syntax_questions_found.append({
                'QID': int(row['QID']),
                'Topic': row['Topic'],
                'Subtopic': row['Subtopic'],
                'Question': row['Question'],
                'CorrectLetter': correct_letter,
                'CorrectAnswer': correct_answer,
                'Note': 'From DCDEA Practice Exam 2',
                'miss_count': 0
            })
        except Exception as e:
            print(f"Error processing QID {row['QID']}: {e}")

print(f"Found {len(syntax_questions_found)} syntax questions in DCDEA")
print("\nSyntax questions found:")
for q in syntax_questions_found:
    print(f"  QID {q['QID']}: {q['Question'][:80]}...")
    print(f"    Answer: {q['CorrectAnswer'][:100]}...\n")
