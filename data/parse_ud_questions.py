import pandas as pd
import re
from datetime import datetime

# Read the entire file
with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by double newlines
blocks = [b.strip() for b in content.split('\n\n') if b.strip()]

questions = []
qid = 1770
i = 0

while i < len(blocks):
    block = blocks[i]
    
    # Check if this block starts with "A." (options block)
    if block.startswith('A.'):
        i += 1
        continue
    
    # This should be a question block
    question_text = block
    i += 1
    
    # Next block should be options
    if i >= len(blocks) or not blocks[i].startswith('A.'):
        continue
    
    options_block = blocks[i]
    i += 1
    
    # Parse options
    lines = options_block.split('\n')
    options = {}
    correct_letter = None
    
    for line in lines:
        line = line.strip()
        match = re.match(r'^([A-F])\.\s*(.*)', line)
        if match:
            letter = match.group(1)
            text = match.group(2)
            
            # Check if this line is both option and answer (e.g., "E. Pull" appearing twice)
            if text and letter not in options:
                options[letter] = text
            elif text == options.get(letter, None):
                # This is a repeated line - likely the answer
                correct_letter = letter
            else:
                # It's just an option
                if letter not in options:
                    options[letter] = text
        elif len(line) == 1 and line in 'ABCDEF':
            # Single letter answer
            correct_letter = line
    
    # Try to find explanation in next block if it exists
    explanation = ""
    if i < len(blocks) and (not blocks[i].startswith('A.') and (not blocks[i][0].isupper() or blocks[i].startswith('When') or blocks[i].startswith('By') or blocks[i].startswith('This'))):
        # This might be explanation/clarification
        explanation = blocks[i]
        i += 1
    
    # Validate
    if not question_text or not correct_letter or len(options) < 4:
        continue
    
    # Topic/Subtopic assignment
    q_lower = question_text.lower()
    
    if 'repos' in q_lower or 'git' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Repos and Git Operations'
    elif 'delta lake' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Delta Lake'
    elif 'vacuum' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Delta Lake Operations'
    elif 'auto loader' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Auto Loader'
    elif 'dlt' in q_lower or 'delta live table' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Delta Live Tables'
    elif 'pyspark' in q_lower or 'spark.sql' in q_lower or 'spark' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Spark SQL and PySpark'
    elif 'python' in q_lower or 'if-condition' in q_lower or 'syntax' in q_lower or 'code' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Python Syntax'
    elif 'lakehouse' in q_lower or 'architecture' in q_lower:
        topic, subtopic = 'Databricks Intelligence Platform', 'Lakehouse Architecture'
    elif 'structured streaming' in q_lower or 'trigger' in q_lower or 'streaming' in q_lower:
        topic, subtopic = 'Development and Ingestion', 'Structured Streaming'
    elif 'sql warehouse' in q_lower or 'databricks sql' in q_lower:
        topic, subtopic = 'Databricks Intelligence Platform', 'SQL Warehouse'
    else:
        topic, subtopic = 'Development and Ingestion', 'General'
    
    # Build question row with all required columns
    row = {
        'Source': 'UD',
        'QID': qid,
        'Exam': 1,
        'Number': qid - 1769,
        'Topic': topic,
        'Subtopic': subtopic,
        'Difficulty': 'Medium',
        'Question': question_text,
        'A': options.get('A', ''),
        'B': options.get('B', ''),
        'C': options.get('C', ''),
        'D': options.get('D', ''),
        'E': options.get('E', ''),
        'F': options.get('F', ''),
        'CorrectLetter': correct_letter,
        'Explanation': explanation,
        'Notes': '',
        'LastReviewed': datetime.now().date(),
        'CorrectCount': 0,
        'IncorrectCount': 0,
        'FlagForReview': False,
        'Tags': '',
        'Graphic': '',
        'Deeper Dive': '',
        'VerifiedAnswer': correct_letter,
        'VerificationStatus': 'Confirmed',
        'AnswerMatchesWorkbook': '',
        'VerificationNotes': 'Custom question from user study materials',
        'VerificationSourceKeys': '',
        'VerifiedOn': '',
    }
    
    questions.append(row)
    qid += 1

# Create DataFrame and save
df = pd.DataFrame(questions)
if len(df) > 0:
    df.to_excel('Custom_Questions_All_Test.xlsx', sheet_name='Custom Questions', index=False)

    print(f"✓ Created test workbook: Custom_Questions_All_Test.xlsx")
    print(f"✓ Added {len(df)} questions")
    print(f"✓ QID range: 1770 to {1770 + len(df) - 1}")
    print(f"\nQuestions by topic:")
    for topic in sorted(df['Topic'].unique()):
        count = len(df[df['Topic'] == topic])
        print(f"  - {topic}: {count} questions")
else:
    print("ERROR: No questions parsed!")
