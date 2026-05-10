import pandas as pd

df = pd.read_excel('Custom_Questions_All_Test_temp.xlsx')

# Check all explanations for newlines (multi-line indicators)
multiline_count = 0
multiline_qids = []

for idx, row in df.iterrows():
    exp = str(row['Explanation'])
    if '\n' in exp:
        multiline_count += 1
        multiline_qids.append(row['QID'])

print(f"Total questions with multi-line explanations: {multiline_count}/92")
print(f"\nQIDs with multi-line explanations:")
print(multiline_qids)

# Show a few examples
print(f"\n\nExamples of multi-line explanations:")
print("=" * 80)
for qid in multiline_qids[:5]:
    row = df[df['QID'] == qid]
    if len(row) > 0:
        exp = row.iloc[0]['Explanation']
        print(f"\nQID {qid}:")
        print(exp)
        print("-" * 40)
