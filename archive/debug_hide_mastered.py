import pandas as pd
import sys
sys.path.insert(0, r'c:\dbx-study-app')
from app import add_performance, load_questions, load_excluded_qids

DATA_PATH = r'c:\dbx-study-app\data\DBx_Questions.xlsx'
ATTEMPTS_PATH = r'c:\dbx-study-app\data\attempts.csv'
SHEET_NAME = 'QuestionBank'

# Load data
questions = load_questions(DATA_PATH, SHEET_NAME)
attempts = pd.read_csv(ATTEMPTS_PATH, parse_dates=['timestamp'])

# Compute stats (as in app)
stats = add_performance(questions, attempts)

# Apply filters as in app
confirmed_only = True
if confirmed_only and "VerificationStatus" in stats.columns:
    stats = stats[stats["VerificationStatus"] == "Confirmed"].copy()

# Mark mastered
stats["mastered"] = (stats["accuracy"] >= 0.85) & (stats["attempts"] >= 3)

# Check before hide_mastered
attempted_before = stats[stats["attempts"] > 0].copy()
high_risk_before = attempted_before[(attempted_before["Difficulty"].isin(["Medium", "Hard"])) & (attempted_before["accuracy"] < 0.6)]

print(f'HIGH-RISK BEFORE hide_mastered: {len(high_risk_before)}')

# Apply hide_mastered
hide_mastered = True
if hide_mastered:
    hidden = stats[stats["mastered"] & (stats["FlagForReview"].fillna(0) != 1)]
    print(f'Questions being hidden: {len(hidden)}')
    
    # Check if any hidden are high-risk
    hidden_mr = hidden[(hidden["Difficulty"].isin(["Medium", "Hard"])) & (hidden["accuracy"] < 0.6)]
    print(f'Hidden questions that are Medium/Hard + <60%: {len(hidden_mr)}')
    if len(hidden_mr) > 0:
        print('Hidden high-risk:')
        print(hidden_mr[['QID', 'Topic', 'Difficulty', 'accuracy', 'attempts', 'mastered', 'FlagForReview']])
    
    stats = stats[~stats["mastered"] | (stats["FlagForReview"].fillna(0) == 1)].copy()

# Check after hide_mastered
attempted_after = stats[stats["attempts"] > 0].copy()
high_risk_after = attempted_after[(attempted_after["Difficulty"].isin(["Medium", "Hard"])) & (attempted_after["accuracy"] < 0.6)]

print(f'HIGH-RISK AFTER hide_mastered: {len(high_risk_after)}')
