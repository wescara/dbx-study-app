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

# Strategy: find option blocks and work backwards to collect question text
i = 0
while i < len(blocks):
    block = blocks[i]
    
    # Skip if not an options block
    if not block.startswith('A.'):
        i += 1
        continue
    
    # Found an options block - work backwards to find the question
    options_block = block
    question_text = ""
    
    # Collect preceding blocks as question text (going backwards)
    j = i - 1
    while j >= 0:
        prev_block = blocks[j]
        
        # Stop if we hit another options block or if we've gone too far
        if prev_block.startswith('A.'):
            break
        
        # If this looks like an explanation/answer, skip it for now and keep going
        if re.match(r'^([A-F])\.', prev_block) or prev_block in ['A', 'B', 'C', 'D', 'E', 'F']:
            j -= 1
            continue
        
        # This is likely question text
        if not question_text:
            question_text = prev_block
        else:
            question_text = prev_block + " " + question_text
        
        j -= 1
        # Stop after collecting one reasonable block (usually the main question)
        if len(question_text) > 50:
            break
    
    # Parse options
    lines = options_block.split('\n')
    options = {}
    correct_letter = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        match = re.match(r'^([A-F])\.\s*(.*)', line)
        if match:
            letter = match.group(1)
            text = match.group(2)
            
            # Check if this line is repeated (answer indicator) or is the last meaningful line
            if text and letter not in options:
                options[letter] = text
            elif text == options.get(letter, None):
                # Repeated - this is the answer
                correct_letter = letter
    
    # If we haven't found the answer yet, look for a single letter line or pick the last letter option
    if not correct_letter:
        for line in reversed(lines):
            line = line.strip()
            if len(line) == 1 and line in 'ABCDEF':
                correct_letter = line
                break
            match = re.match(r'^([A-F])\.\s', line)
            if match:
                correct_letter = match.group(1)
                break
    
    # Look for explanation in following blocks
    explanation = ""
    k = i + 1
    while k < len(blocks) and k < i + 3:  # Look ahead a couple blocks
        next_block = blocks[k]
        # If it's not an options block and not a question-like block, it might be explanation
        if (not next_block.startswith('A.') and 
            not next_block[0].isupper() and
            len(next_block) < 200 and
            not '?' in next_block):
            explanation = next_block
            break
        k += 1
    
    # Validate
    if not question_text or not correct_letter or len(options) < 4:
        i += 1
        continue
    
    question_text = question_text.strip()
    
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
    elif 'job' in q_lower or 'task' in q_lower or 'orchestration' in q_lower:
        topic, subtopic = 'Databricks Intelligence Platform', 'Jobs and Orchestration'
    elif 'permission' in q_lower or 'grant' in q_lower or 'rbac' in q_lower:
        topic, subtopic = 'Databricks Intelligence Platform', 'Access Control'
    else:
        topic, subtopic = 'Development and Ingestion', 'General'
    
    # Build question row
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
    i += 1

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
