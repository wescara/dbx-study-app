from docx import Document
import re
import pandas as pd

docx_path = 'data/DCDEA Practice Exam 2.docx'
doc = Document(docx_path)

# Parse questions from paragraphs
questions = []
current_question = None
current_lines = []

for para in doc.paragraphs:
    text = para.text.strip()
    if not text:
        continue
    
    question_match = re.match(r'^Question\s+(\d+):', text)
    if question_match:
        if current_question is not None:
            current_question['lines'] = current_lines
            questions.append(current_question)
        
        current_question = {'num': int(question_match.group(1))}
        current_lines = [text]
        continue
    
    if current_question is not None:
        if text.startswith('Correct Anwser:') or text.startswith('Correct Answer:'):
            current_lines.append(text)
            current_question['lines'] = current_lines
            questions.append(current_question)
            current_question = None
            current_lines = []
            continue
        
        current_lines.append(text)

if current_question is not None:
    current_question['lines'] = current_lines
    questions.append(current_question)

print(f"Total questions: {len(questions)}\n")

# Better parser that identifies answer options by looking for single letter + colon pattern
def parse_question_better(q):
    lines = q['lines']
    
    # The question text usually starts at line 1 or 2
    # Options are identified as single lines with content
    # Explanation starts after a separator line
    
    question_text_lines = []
    options = {}
    explanation_lines = []
    correct_answer = ""
    in_explanation = False
    
    i = 1  # Skip "Question N:" line
    
    # Collect question text until we hit options or separator
    while i < len(lines):
        line = lines[i]
        
        if line.startswith('-'):  # separator line
            in_explanation = True
            i += 1
            break
        
        # Check if this looks like an option (short, concise line that starts a new thought)
        # Real options tend to be relatively short or start with specific keywords
        is_option_line = False
        
        # Option candidates: 
        # 1. Lines matching expected answer option patterns
        # 2. Very short lines (< 150 chars typically)
        # 3. Lines that look like complete thoughts
        
        if len(line) < 150 and not line.startswith('The ') and not line.startswith('A ') and not line.startswith('Bronze') and not line.startswith('Silver'):
            # Check if it's not part of a longer question description
            if re.match(r'^[A-Za-z]', line) and (line.isupper() or (len(line) > 3 and len(line) < 100)):
                is_option_line = True
        
        if is_option_line and len(options) < 6:
            # This is likely an option
            option_letter = chr(65 + len(options))  # A, B, C, D, E, F
            options[option_letter] = line
        else:
            question_text_lines.append(line)
        
        i += 1
    
    # Collect explanation
    if in_explanation:
        for line in lines[i:]:
            if 'Correct Anwser:' in line or 'Correct Answer:' in line:
                # Extract correct answer
                match = re.search(r'\(([^)]+)\)', line)
                if match:
                    correct_answer = match.group(1)
                break
            if not line.startswith('-'):
                explanation_lines.append(line)
    
    question_text = ' '.join(question_text_lines).strip()
    explanation = ' '.join(explanation_lines).strip()
    
    return {
        'num': q['num'],
        'question': question_text,
        'options': options,
        'explanation': explanation,
        'correct_answer': correct_answer
    }

# Try better parsing on first few questions
print("Testing better parser on first 5 questions:\n")
for i in range(min(5, len(questions))):
    q = questions[i]
    parsed = parse_question_better(q)
    
    print(f"Q{parsed['num']}:")
    print(f"  Question: {parsed['question'][:90]}...")
    print(f"  Options ({len(parsed['options'])}):")
    for letter, text in sorted(parsed['options'].items()):
        print(f"    {letter}: {text[:60]}...")
    print(f"  Correct: {parsed['correct_answer']}")
    print()
