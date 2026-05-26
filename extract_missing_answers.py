from docx import Document
import re

docx_path = 'data/DCDEA Practice Exam 2.docx'
doc = Document(docx_path)

# Parse questions
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
        if re.match(r'^Correct', text):
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

# Find the specific questions with issues
problem_q_nums = [2, 6, 10, 20, 22, 35]

print("Missing data from DOCX:\n")
for q_num in problem_q_nums:
    q = next((q for q in questions if q['num'] == q_num), None)
    if q:
        print(f"Question {q_num}:")
        
        # Extract options and correct answer
        separator_idx = -1
        for i, line in enumerate(q['lines']):
            if line.startswith('-'):
                separator_idx = i
                break
        
        if separator_idx > 0:
            option_lines = q['lines'][2:separator_idx]
            explanation_lines = q['lines'][separator_idx+1:]
            
            print("  Options:")
            for i, line in enumerate(option_lines[:6]):
                letter = chr(65 + i)
                print(f"    {letter}: {line[:70]}...")
            
            # Find correct answer
            for line in explanation_lines:
                if 'Correct' in line:
                    match = re.search(r'\(([^)]+)\)', line)
                    if match:
                        answer = match.group(1)
                        # Convert to letters
                        try:
                            nums = [int(n.strip()) for n in answer.split(',')]
                            letters = ','.join([chr(64 + n) for n in nums])
                            print(f"  Correct: {letters} (from: {line[:60]}...)")
                        except:
                            print(f"  Correct: {answer}")
                    break
        print()
