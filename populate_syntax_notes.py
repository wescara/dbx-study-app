import pandas as pd
import re

# Load the CSV
csv_path = r"C:\dbx-study-app\data\syntax_questions_for_review.csv"
df = pd.read_csv(csv_path)

# Populate Note column with the CorrectAnswer if Note is empty
def extract_syntax(answer):
    """Extract key syntax from the answer"""
    if pd.isna(answer) or answer == "" or answer == "nan":
        return ""
    
    answer = str(answer).strip()
    
    # For multi-line answers, take just the first line or key syntax
    if "\n" in answer:
        lines = answer.split("\n")
        # If it's a code block, take the first meaningful line
        syntax = lines[0].strip()
    else:
        syntax = answer
    
    # Clean up formatting
    syntax = syntax.strip()
    
    return syntax

# Fill in Note column where it's empty
print(f"Total rows: {len(df)}")
print(f"Rows with empty Note: {df['Note'].isna().sum() + (df['Note'] == '').sum()}")

# Populate empty Note fields with first line of CorrectAnswer
for idx, row in df.iterrows():
    if pd.isna(df.loc[idx, 'Note']) or df.loc[idx, 'Note'] == '':
        syntax = extract_syntax(df.loc[idx, 'CorrectAnswer'])
        df.loc[idx, 'Note'] = syntax
        if idx < 10:  # Show first 10
            print(f"QID {int(df.loc[idx, 'QID'])}: {syntax[:80]}")

# Save back
df.to_csv(csv_path, index=False)
print(f"\n✅ Updated {csv_path}")
print(f"Rows with Note now: {(df['Note'] != '').sum()}")
