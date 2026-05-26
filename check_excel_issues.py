import pandas as pd
import openpyxl
from openpyxl.utils import get_column_letter

# First check for data issues
df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

print("Checking for potential issues...\n")

# Check Exam column values
print(f"Unique Exam values: {df['Exam'].unique()}")
print(f"Exam data types: {df['Exam'].dtype}")

# Check for problematic data types
print("\nData type summary:")
for col in df.columns:
    print(f"  {col}: {df[col].dtype}")

# Check for NaN or unusual values
print("\nColumns with NaN:")
for col in df.columns:
    nan_count = df[col].isna().sum()
    if nan_count > 0:
        print(f"  {col}: {nan_count} NaN values")

# Check for very long strings or special characters
print("\nChecking for problematic content...")
for col in ['Question', 'Explanation']:
    max_len = df[col].str.len().max()
    print(f"  {col} max length: {max_len}")

# Show DCDEA questions
dcdea = df[df['Exam'] == 'DCDEA Practice Exam 2']
print(f"\nDCDEA questions: {len(dcdea)}")
