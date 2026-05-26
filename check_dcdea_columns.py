import pandas as pd

dcdea_df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

print("Columns in DCDEA file:")
print(list(dcdea_df.columns))

# Show a sample row
print("\nSample question (QID 2045):")
q = dcdea_df[dcdea_df['QID'] == 2045].iloc[0]
print(f"Question: {q['Question'][:150]}...")
print(f"CorrectLetter: {q['CorrectLetter']}")

# Check what option columns exist
option_cols = [col for col in dcdea_df.columns if 'Option' in col]
print(f"\nOption columns: {option_cols}")

for col in option_cols:
    print(f"{col}: {q[col][:100] if pd.notna(q[col]) else 'NaN'}...")
