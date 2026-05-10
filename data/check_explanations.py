import re

with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

qid_pattern = r'^-(\d+)-+'
sections = re.split(qid_pattern, content, flags=re.MULTILINE)

original_explanations = {}
na_qids = []

for i in range(1, len(sections), 2):
    if i + 1 >= len(sections):
        break
    
    qid = int(sections[i].strip())
    section_content = sections[i + 1].strip()
    
    lines = section_content.split('\n')
    for line in lines:
        if 'Explanation:' in line:
            explanation = line.replace('Explanation:', '').strip()
            if explanation and explanation.lower() != 'n/a':
                original_explanations[qid] = explanation
            elif explanation.lower() == 'n/a':
                na_qids.append(qid)
            break

print(f'ORIGINAL EXPLANATIONS ({len(original_explanations)} questions):')
print('=' * 80)
for qid in sorted(original_explanations.keys()):
    exp = original_explanations[qid]
    print(f'\n{qid}:')
    print(exp[:120] + ('...' if len(exp) > 120 else ''))

print(f'\n\nN/A EXPLANATIONS THAT NEEDED GENERATION ({len(na_qids)} questions):')
print('=' * 80)
for qid in sorted(na_qids):
    print(f'{qid}', end=' ')
print()
