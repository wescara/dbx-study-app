import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

print(f"Total rows: {len(df)}")
print(f"Total QIDs: {len(df['QID'].unique())}")

# Check for SG source
sg = df[df['Source'] == 'SG']
print(f"\nRows with Source='SG': {len(sg)}")
print(f"Unique QIDs with SG: {len(sg['QID'].unique())}")
print(f"QID range for SG: {int(sg['QID'].min())} to {int(sg['QID'].max())}")

# Check for duplicates
dup_qids = df[df.duplicated(subset=['QID'], keep=False)]
print(f"\nDuplicate QIDs: {len(dup_qids)}")

# Show first SG entries
print(f"\nFirst 3 SG entries:")
for idx, row in sg.head(3).iterrows():
    print(f"  QID {int(row['QID'])}: Q{int(row['Number'])} - {row['Question'][:50]}...")

# Show last SG entries  
print(f"\nLast 3 SG entries:")
for idx, row in sg.tail(3).iterrows():
    print(f"  QID {int(row['QID'])}: Q{int(row['Number'])} - {row['Question'][:50]}...")
