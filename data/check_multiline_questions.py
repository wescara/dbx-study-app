import pandas as pd

df = pd.read_excel('Custom_Questions_All_Test_temp.xlsx')

# Check all questions for newlines (multi-line questions)
multiline_count = 0
multiline_qids = []

for idx, row in df.iterrows():
    q = str(row['Question'])
    if '\n' in q:
        multiline_count += 1
        multiline_qids.append(row['QID'])

print(f"Total questions with multi-line questions: {multiline_count}/92")
print(f"\nQIDs with multi-line questions:")
print(multiline_qids)

# Show a few examples
print(f"\n\nExamples of multi-line questions:")
print("=" * 80)
for qid in multiline_qids[:3]:
    row = df[df['QID'] == qid]
    if len(row) > 0:
        q = row.iloc[0]['Question']
        print(f"\nQID {qid}:")
        print(q)
        print("-" * 40)
