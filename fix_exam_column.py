import pandas as pd

# Load the file
df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

print("Before fix:")
print(f"  Exam unique values: {df['Exam'].unique()}")
print(f"  Exam data types: {df['Exam'].dtype}")

# Convert all DCDEA Practice Exam 2 to integer 2
df.loc[df['Exam'] == 'DCDEA Practice Exam 2', 'Exam'] = 2

# Convert Exam column to integer
df['Exam'] = pd.to_numeric(df['Exam'], errors='coerce').fillna(0).astype(int)

print("\nAfter fix:")
print(f"  Exam values: {sorted(df['Exam'].unique())}")
print(f"  Exam data types: {df['Exam'].dtype}")

# Check DCDEA questions now
dcdea = df[df['Exam'] == 2]
print(f"\nDCDEA questions with Exam=2: {len(dcdea)}")
print(f"QID range: {int(dcdea['QID'].min())} to {int(dcdea['QID'].max())}")

# Save cleaned file
output_path = 'data/DCDEA_Practice_Exam_2_Questions.xlsx'
df.to_excel(output_path, index=False)
print(f"\n✓ Fixed file saved to {output_path}")
