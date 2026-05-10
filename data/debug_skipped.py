import re

with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

blocks = [b.strip() for b in content.split('\n\n') if b.strip()]

print(f"Total blocks: {len(blocks)}")
print(f"Looking for option blocks...\n")

option_count = 0
question_count = 0
skipped = 0

for i in range(len(blocks)):
    block = blocks[i]
    
    if not block.startswith('A.'):
        continue
    
    option_count += 1
    
    # Found an options block - work backwards to find question
    question_text = ""
    j = i - 1
    while j >= 0:
        prev_block = blocks[j]
        if prev_block.startswith('A.'):
            break
        if re.match(r'^([A-F])\.', prev_block) or prev_block in ['A', 'B', 'C', 'D', 'E', 'F']:
            j -= 1
            continue
        if not question_text:
            question_text = prev_block
        else:
            question_text = prev_block + " " + question_text
        j -= 1
        if len(question_text) > 50:
            break
    
    # Parse options
    lines = block.split('\n')
    options = {}
    correct_letter = None
    
    for line in lines:
        line = line.strip()
        match = re.match(r'^([A-F])\.\s*(.*)', line)
        if match:
            letter = match.group(1)
            text = match.group(2)
            if text and letter not in options:
                options[letter] = text
            elif text == options.get(letter, None):
                correct_letter = letter
            else:
                if letter not in options:
                    options[letter] = text
        elif len(line) == 1 and line in 'ABCDEF':
            correct_letter = line
    
    # Check if valid
    if not question_text or not correct_letter or len(options) < 4:
        print(f"\nOption block {option_count} at index {i} SKIPPED:")
        print(f"  Question text: {repr(question_text[:60] if question_text else 'NONE')}")
        print(f"  Correct letter: {correct_letter}")
        print(f"  Options count: {len(options)}")
        print(f"  Available options: {list(options.keys())}")
        skipped += 1
    else:
        question_count += 1

print(f"\n\nSummary:")
print(f"Option blocks found: {option_count}")
print(f"Questions extracted: {question_count}")
print(f"Skipped: {skipped}")
