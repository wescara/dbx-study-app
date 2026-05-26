import pandas as pd

# Load data
questions = pd.read_excel(r'C:\dbx-study-app\data\DBx_Questions.xlsx', sheet_name='QuestionBank')
attempts = pd.read_csv(r'C:\dbx-study-app\data\attempts.csv')

# Simulate add_performance
DIFF_WEIGHT = {"Easy": 0, "Medium": 1, "Hard": 2}

def add_performance(questions, attempts):
    q = questions.copy()
    if attempts.empty:
        q["attempts"] = 0
        q["correct_total"] = 0
        q["accuracy"] = 0.0
        return q
    
    att = attempts.copy()
    att["timestamp"] = pd.to_datetime(att["timestamp"], format="mixed", errors="coerce")
    now = pd.Timestamp.now()
    att["days_ago"] = (now - att["timestamp"]).dt.total_seconds() / 86400
    att["weight"] = 0.5 ** (att["days_ago"] / 14)
    att["weighted_correct"] = att["correct"].astype(float) * att["weight"]
    
    agg = att.groupby("QID").agg(
        attempts=("correct", "count"),
        correct_total=("correct", "sum"),
        weighted_correct=("weighted_correct", "sum"),
        weighted_total=("weight", "sum"),
    ).reset_index()
    agg["accuracy"] = agg["weighted_correct"] / agg["weighted_total"]
    
    out = q.merge(agg, on="QID", how="left")
    return out.fillna({"attempts": 0, "correct_total": 0, "accuracy": 0.0})

stats = add_performance(questions, attempts)

# Apply filters like the app does
confirmed_only = True
hide_mastered = True
if confirmed_only and "VerificationStatus" in stats.columns:
    stats = stats[stats["VerificationStatus"] == "Confirmed"].copy()

stats["mastered"] = (stats["accuracy"] >= 0.85) & (stats["attempts"] >= 3)
if hide_mastered:
    stats = stats[~stats["mastered"] | (stats["FlagForReview"].fillna(0) == 1)].copy()

# Now apply untouched filter
untouched = stats[stats["attempts"] == 0].copy()

print(f"Total stats (after confirmed/mastered filters): {len(stats)}")
print(f"Untouched (attempts == 0): {len(untouched)}")
print()

# Check new untouched questions
today = pd.Timestamp.now()
cutoff = today - pd.Timedelta(days=3)
new_untouched = untouched[untouched['DateAdded'] >= cutoff]
print(f"NEW untouched (last 3 days, 0 attempts): {len(new_untouched)}")
print()
print("Sample new untouched questions:")
print(new_untouched[['QID', 'DateAdded', 'Difficulty', 'Topic']].head(10))
