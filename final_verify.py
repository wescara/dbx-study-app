import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
new_qs = df[df['Source'] == 'SG']

print(f'✓ New DCDEA questions added: {len(new_qs)}')
print(f'✓ QID range: {int(new_qs["QID"].min())}-{int(new_qs["QID"].max())}')
print(f'✓ Total questions in file: {len(df)}')

missing = len(new_qs[new_qs['CorrectLetter'].isna()])
has_answer = len(new_qs) - missing
print(f'✓ Questions with correct answers: {has_answer}/{len(new_qs)}')

print(f'\n15 graphics extracted to: data/extracted_images_exam2/')

# Show a few sample questions
print(f'\nSample questions:')
for idx in [0, 1, 44]:
    q = new_qs.iloc[idx]
    print(f"  QID {int(q['QID'])}: Q{int(q['Number'])} - Correct: {q['CorrectLetter']}")
