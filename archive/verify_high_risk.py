import pandas as pd
import os

# Load the actual questions file the app uses
DATA_PATH = r"C:\dbx-study-app\data\DBx_Questions.xlsx"
SHEET_NAME = "QuestionBank"

questions = pd.read_excel(DATA_PATH, sheet_name=SHEET_NAME)
print(f"Questions loaded: {len(questions)} rows, {questions['QID'].nunique()} unique QIDs")

# Load attempts
attempts = pd.read_csv('data/attempts.csv')
attempts['timestamp'] = pd.to_datetime(attempts['timestamp'], format='mixed')

# Calculate performance stats (matching app's add_performance function)
now = pd.Timestamp.now()
att = attempts.copy()
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

# Merge questions with performance stats
stats = questions.merge(agg, on="QID", how="left")
stats = stats.fillna({"attempts": 0, "correct_total": 0, "accuracy": 0.0, "ExamWeight": 0.15})

# Apply filters (matching app defaults)
confirmed_only = True
hide_mastered = False

# Confirmed-only filter
if confirmed_only and "VerificationStatus" in stats.columns:
    stats = stats[stats["VerificationStatus"] == "Confirmed"].copy()
    print(f"After confirmed filter: {len(stats)} rows")

# Mastery filter
stats["mastered"] = (stats["accuracy"] >= 0.85) & (stats["attempts"] >= 3)
if hide_mastered:
    stats = stats[~stats["mastered"] | (stats["FlagForReview"].fillna(0) == 1)].copy()

# Get attempted questions
attempted = stats[stats["attempts"] > 0].copy()
print(f"Questions Attempted: {len(attempted)} rows, {attempted['QID'].nunique()} unique QIDs")
print(f"Overall Accuracy: {attempted['accuracy'].mean():.1%}")
print()

# Filter for high-risk: Medium/Hard + <60% accuracy
high_risk = attempted[(attempted["Difficulty"].isin(["Medium", "Hard"])) & (attempted["accuracy"] < 0.6)]

print(f"High-Risk (M/H & <60%): {len(high_risk)} rows")
print(f"\nTop topics in high-risk:")
print(high_risk['Topic'].value_counts())
