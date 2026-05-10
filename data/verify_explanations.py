import pandas as pd

df = pd.read_excel('Custom_Questions_All_Test.xlsx')

# Check a few N/A QIDs that should have AI-generated explanations
na_qids_sample = [1768, 1775, 1820, 1859]
print("Sample AI-Generated Explanations (were N/A):")
print("=" * 80)
for qid in na_qids_sample:
    row = df[df['QID'] == qid]
    if len(row) > 0:
        exp = row.iloc[0]['Explanation']
        print(f"\n{qid}: {exp[:100]}...")

# Check a few original QIDs that should have original explanations
original_qids_sample = [1769, 1774, 1800, 1854]
print("\n\nSample Original Explanations (preserved from source):")
print("=" * 80)
for qid in original_qids_sample:
    row = df[df['QID'] == qid]
    if len(row) > 0:
        exp = row.iloc[0]['Explanation']
        print(f"\n{qid}: {exp[:100]}...")
