import pandas as pd

dcdea_df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
dcdea_questions = dcdea_df[(dcdea_df['QID'] >= 2045) & (dcdea_df['QID'] <= 2089)].copy()

syntax_keywords = [
    'SQL', 'PYTHON', 'PYSPARK', 'syntax', 'code', 'command', 'statement',
    'script', 'query', 'function', 'parameter', 'argument', 'option',
    'CREATE TABLE', 'SELECT', 'WHERE', 'JOIN', 'GROUP BY',
    'def ', '():', 'import ', 'lambda', 'transform', 'udf',
    'spark.sql', 'spark.read', '.write', '.option', '.mode'
]

non_syntax = []

for idx, row in dcdea_questions.iterrows():
    question_text = str(row['Question']).upper()
    has_syntax = any(keyword.upper() in question_text for keyword in syntax_keywords)
    
    if not has_syntax:
        non_syntax.append({
            'QID': int(row['QID']),
            'Number': int(row['Number']),
            'Topic': row['Topic'],
            'Subtopic': row['Subtopic'],
            'Question': row['Question'][:100]
        })

print(f"Non-syntax questions: {len(non_syntax)}\n")
for q in non_syntax:
    print(f"Q{q['Number']} (QID {q['QID']}): {q['Subtopic']}")
    print(f"  {q['Question']}...\n")
