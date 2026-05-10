import re

# Read the entire file
with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

# Split by the QID pattern (lines starting with -)
qid_pattern = r'^-(\d+)-+\s*$'
sections = re.split(qid_pattern, content, flags=re.MULTILINE)

# Process first question
if len(sections) >= 3:
    qid = int(sections[1])
    section_content = sections[2].strip()
    
    print(f"=== PROCESSING QID {qid} ===")
    
    lines = section_content.split('\n')
    
    line_idx = 0
    question_text = ""
    options = {}
    
    # Get the question (first non-empty line)
    while line_idx < len(lines) and not lines[line_idx].strip():
        line_idx += 1
    
    if line_idx < len(lines):
        question_text = lines[line_idx].strip()
        line_idx += 1
    
    # Skip empty lines
    while line_idx < len(lines) and not lines[line_idx].strip():
        line_idx += 1
    
    # Parse options (A-E lines)
    option_count = 0
    while line_idx < len(lines) and option_count < 6:
        line = lines[line_idx].strip()
        
        if not line:
            line_idx += 1
            continue
        
        # Check if line starts with option letter
        match = re.match(r'^([A-F])\.\s+(.*)', line)
        if match:
            letter = match.group(1)
            text = match.group(2).strip()
            options[letter] = text
            option_count += 1
            line_idx += 1
        else:
            # No more options
            break
    
    print(f"Parsed options: {options}")
    print(f"Line index after options: {line_idx}")
    print(f"Remaining lines:")
    for i in range(line_idx, len(lines)):
        print(f"  Line {i}: {repr(lines[i])}")
    
    # Skip empty lines
    while line_idx < len(lines) and not lines[line_idx].strip():
        line_idx += 1
        print(f"Skipped empty line, now at {line_idx}")
    
    # The next line(s) should be the correct answer (or repetition of an option)
    correct_answer = None
    while line_idx < len(lines):
        line = lines[line_idx].strip()
        print(f"Checking for answer at line {line_idx}: {repr(line)}")
        
        if not line:
            line_idx += 1
            continue
        
        # Check if this line is the answer (starts with letter and has option text)
        match = re.match(r'^([A-F])\.\s+(.*)', line)
        if match:
            letter = match.group(1)
            text = match.group(2).strip()
            print(f"  -> Matched as answer: {letter}")
            if correct_answer is None:
                correct_answer = letter
            line_idx += 1
            # Could be a duplicate, check if next line is explanation
            if line_idx < len(lines) and lines[line_idx].strip().startswith('Explanation:'):
                print(f"  -> Next line is explanation, breaking")
                break
        elif line.startswith('Explanation:'):
            print(f"  -> Found explanation, breaking")
            break
        else:
            print(f"  -> Line doesn't match pattern, moving on")
            line_idx += 1
    
    print(f"\nCorrect answer found: {correct_answer}")
    print(f"Options count: {len(options)}")
    print(f"Question length: {len(question_text)}")
    print(f"Validation: Has question? {bool(question_text)}, Has options? {len(options) >= 4}, Has answer? {bool(correct_answer)}")
