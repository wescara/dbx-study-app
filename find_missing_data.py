import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
dcdea = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)]

# Find questions with missing data
print("Questions with missing data:\n")

for idx, row in dcdea.iterrows():
    missing = []
    if pd.isna(row['CorrectLetter']):
        missing.append('CorrectLetter')
    for col in ['A', 'B', 'C', 'D']:
        if pd.isna(row[col]):
            missing.append(col)
    
    if missing:
        qid = int(row['QID'])
        q_num = int(row['Number'])
        print(f"QID {qid} (Q{q_num}): Missing {', '.join(missing)}")
        print(f"  Question: {row['Question'][:70]}...")
        print()
