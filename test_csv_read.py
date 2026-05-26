import pandas as pd

# Read with proper parsing
df = pd.read_csv('data/syntax_questions_for_review.csv')

print(f"Loaded {len(df)} questions successfully")
print(f"Columns: {list(df.columns)}")

# Check for problematic rows
for idx, row in df.iterrows():
    if idx > 10 and idx < 15:
        print(f"\nRow {idx}:")
        print(f"  QID: {row['QID']}")
        print(f"  Question length: {len(str(row['Question']))}")
        print(f"  Question: {str(row['Question'])[:100]}...")
