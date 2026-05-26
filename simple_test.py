import pandas as pd

# Simple test without importing streamlit-heavy app.py
attempts = pd.read_csv(r'c:\dbx-study-app\data\attempts.csv')

# Count incorrect attempts per QID
incorrect_counts = attempts[attempts['correct'] == 0].groupby('QID').size().reset_index(name='incorrect_count')

# Filter for exactly 1 incorrect
one_incorrect = incorrect_counts[incorrect_counts['incorrect_count'] == 1]

print(f'✓ Previously missed (exactly 1 incorrect): {len(one_incorrect)}')
print(f'✓ Sample questions with 1 incorrect:')
print(one_incorrect.head(10))
