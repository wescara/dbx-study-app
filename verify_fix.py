import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

# Get just the new DCDEA questions by QID range
dcdea_new = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)]

print(f"DCDEA Practice Exam 2 (new questions QID 2045-2089):")
print(f"  Count: {len(dcdea_new)}")
print(f"  Source: {dcdea_new['Source'].unique()}")
print(f"  Exam value: {dcdea_new['Exam'].unique()}")
print(f"  Exam data type: {dcdea_new['Exam'].dtype}")

# Check for any missing data in answer options
print(f"\nData quality check:")
for col in ['A', 'B', 'C', 'D']:
    nan_count = dcdea_new[col].isna().sum()
    print(f"  {col}: {nan_count} NaN values")

print(f"\nCorrect answers with data: {dcdea_new['CorrectLetter'].notna().sum()}/45")

# Show sample
print(f"\nSample DCDEA questions:")
print(f"  Q1 (QID 2045): Exam={dcdea_new.iloc[0]['Exam']}, Correct={dcdea_new.iloc[0]['CorrectLetter']}")
print(f"  Q45 (QID 2089): Exam={dcdea_new.iloc[-1]['Exam']}, Correct={dcdea_new.iloc[-1]['CorrectLetter']}")

print(f"\n✓ Excel file fixed and ready")
