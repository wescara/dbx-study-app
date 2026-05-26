import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
print(f'Total rows: {len(df)}')
print()

# Check Q1
q1 = df[df['QID'] == 2045].iloc[0]
print(f'QID 2045 (Q1):')
print(f'  Source: {q1["Source"]}')
print(f'  Question: {str(q1["Question"])[:70]}...')
print(f'  Options: A, B, C, D, E')
print(f'  Correct Answer: {q1["CorrectLetter"]}')
print()

# Check a few more
for qid in [2046, 2047, 2089]:
    row = df[df['QID'] == qid].iloc[0]
    print(f'QID {qid}: Correct={row["CorrectLetter"]}, Source={row["Source"]}')
