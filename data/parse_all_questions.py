import pandas as pd
import re
from datetime import datetime

# Read the entire file
with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by double newlines to separate questions
question_blocks = [b.strip() for b in content.split('\n\n') if b.strip()]

questions_data = []
qid_counter = 1770

for block in question_blocks:
    lines = block.split('\n')
    
    if len(lines) < 7:  # Minimum: question + 5 options + answer
        continue
    
    # Find where options start (line that starts with "A.")
    question_lines = []
    option_start_idx = -1
    
    for i, line in enumerate(lines):
        if line.strip().startswith('A.'):
            option_start_idx = i
            break
        question_lines.append(line.strip())
    
    if option_start_idx == -1:
        continue
    
    question_text = ' '.join(question_lines).strip()
    
    if not question_text:
        continue
    
    # Extract options (A-E)
    options = {'A': '', 'B': '', 'C': '', 'D': '', 'E': '', 'F': ''}
    correct_answer = None
    explanation = ""
    
    # Parse options from the block
    for i in range(option_start_idx, len(lines)):
        line = lines[i].strip()
        
        # Check for option pattern "X. text"
        for letter in ['A', 'B', 'C', 'D', 'E', 'F']:
            if line.startswith(letter + '.'):
                options[letter] = line[2:].strip()
                break
    
    # Find the correct answer (last occurrence or repeated single letter)
    for line in reversed(lines[option_start_idx:]):
        line = line.strip()
        
        # Check for pattern "X. text" or just "X" or "X." at end
        if re.match(r'^([A-F])(?:\.|$|\s)', line):
            potential_answer = line[0]
            if potential_answer in options:
                correct_answer = potential_answer
                # Extract explanation if it exists after the answer
                if ': ' in line:
                    explanation = line.split(': ', 1)[1]
                break
    
    # Skip if we don't have the required fields
    if not question_text or not correct_answer:
        continue
    
    if not any(options.values()):  # At least one option should be filled
        continue
    
    # Derive topic/subtopic based on question content
    q_lower = question_text.lower()
    
    if 'repos' in q_lower or 'git' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Repos and Git Operations'
    elif 'delta lake' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Delta Lake'
    elif 'vacuum' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Delta Lake Operations'
    elif 'auto loader' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Auto Loader'
    elif 'dlt' in q_lower or 'delta live table' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Delta Live Tables'
    elif 'pyspark' in q_lower or 'spark.sql' in q_lower or 'spark.table' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Spark SQL and PySpark'
    elif 'python' in q_lower or 'if-condition' in q_lower or 'syntax' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Python Syntax'
    elif 'udf' in q_lower or 'user defined function' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'User Defined Functions'
    elif 'union' in q_lower or 'join' in q_lower or 'intersect' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'SQL Set Operations'
    elif 'lakehouse' in q_lower or 'architecture' in q_lower:
        topic = 'Databricks Intelligence Platform'
        subtopic = 'Lakehouse Architecture'
    elif 'bronze' in q_lower or 'silver' in q_lower or 'gold' in q_lower:
        topic = 'Data Architecture'
        subtopic = 'Multi-Hop Architecture'
    elif 'structured streaming' in q_lower or 'trigger' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Spark Structured Streaming'
    elif 'sql warehouse' in q_lower or 'databricks sql' in q_lower:
        topic = 'Databricks Intelligence Platform'
        subtopic = 'Databricks SQL'
    elif 'constraint' in q_lower or 'expect' in q_lower:
        topic = 'Development and Ingestion'
        subtopic = 'Delta Live Tables - Constraints'
    elif 'job' in q_lower or 'task' in q_lower or 'orchestration' in q_lower:
        topic = 'Databricks Intelligence Platform'
        subtopic = 'Jobs and Orchestration'
    elif 'permission' in q_lower or 'grant' in q_lower or 'rbac' in q_lower:
        topic = 'Databricks Intelligence Platform'
        subtopic = 'Access Control and Permissions'
    else:
        topic = 'Development and Ingestion'
        subtopic = 'General'
    
    # Derive difficulty
    if 'simple' in q_lower or 'basic' in q_lower or 'easy' in q_lower or 'default' in q_lower:
        difficulty = 'Easy'
    elif 'hard' in q_lower or 'complex' in q_lower or 'advanced' in q_lower:
        difficulty = 'Hard'
    else:
        difficulty = 'Medium'
    
    question_data = {
        'Source': 'UD',
        'QID': qid_counter,
        'Exam': 1,
        'Number': qid_counter - 1769,
        'Topic': topic,
        'Subtopic': subtopic,
        'Difficulty': difficulty,
        'Question': question_text,
        'A': options.get('A', ''),
        'B': options.get('B', ''),
        'C': options.get('C', ''),
        'D': options.get('D', ''),
        'E': options.get('E', ''),
        'F': options.get('F', ''),
        'CorrectLetter': correct_answer,
        'Explanation': explanation,
        'Notes': None,
        'LastReviewed': datetime.now().date(),
        'CorrectCount': 0,
        'IncorrectCount': 0,
        'FlagForReview': False,
        'Tags': '',
        'Graphic': None,
        'Deeper Dive': None,
        'VerifiedAnswer': correct_answer,
        'VerificationStatus': 'Confirmed',
        'AnswerMatchesWorkbook': None,
        'VerificationNotes': 'Custom question from user study materials',
        'VerificationSourceKeys': None,
        'VerifiedOn': None,
    }
    
    questions_data.append(question_data)
    qid_counter += 1

# Create DataFrame
df_questions = pd.DataFrame(questions_data)

# Save to Excel
output_file = 'Custom_Questions_All_Test.xlsx'
df_questions.to_excel(output_file, sheet_name='Custom Questions', index=False)

print(f"✓ Created test workbook: {output_file}")
print(f"✓ Added {len(df_questions)} questions")
print(f"✓ QID range: 1770 to {1770 + len(df_questions) - 1}")
print(f"\nQuestions by topic:")
for topic in sorted(df_questions['Topic'].unique()):
    count = len(df_questions[df_questions['Topic'] == topic])
    print(f"  - {topic}: {count} questions")
print(f"\nDifficulty breakdown:")
for diff in ['Easy', 'Medium', 'Hard']:
    count = len(df_questions[df_questions['Difficulty'] == diff])
    if count > 0:
        print(f"  - {diff}: {count} questions")
