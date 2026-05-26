import pandas as pd
import numpy as np

df = pd.read_excel('c:\\dbx-study-app\\data\\DCDEA_Practice_Exam_2_NEW_QUESTIONS.xlsx')
print('Total rows:', len(df))
print('\nFirst question details:')
row = df.iloc[0]
print('Number:', row['Number'])
print('Question:', str(row['Question'])[:100])
print('A:', str(row['A'])[:80] if pd.notna(row['A']) else '(empty)')
print('B:', str(row['B'])[:80] if pd.notna(row['B']) else '(empty)')
print('C:', str(row['C'])[:80] if pd.notna(row['C']) else '(empty)')
print('D:', str(row['D'])[:80] if pd.notna(row['D']) else '(empty)')
print('CorrectLetter:', row['CorrectLetter'])
print('Explanation:', str(row['Explanation'])[:100] if pd.notna(row['Explanation']) else '(empty)')

# Check for empty options
print('\n\nSummary of data quality:')
print('Rows with empty A:', len(df[df['A'] == '']))
print('Rows with empty B:', len(df[df['B'] == '']))
print('Rows with empty C:', len(df[df['C'] == '']))
print('Rows with empty D:', len(df[df['D'] == '']))
print('Rows with empty Explanation:', len(df[df['Explanation'] == '']))
