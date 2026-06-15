import pandas as pd
import os
import sys

# Simulate app.py setup
DATA_PATH = r'C:\dbx-study-app\data\DBx_Questions.xlsx'
SHEET_NAME = "QuestionBank"
ATTEMPTS_PATH = r'C:\dbx-study-app\data\attempts.csv'

def load_excluded_qids(path=r'C:\dbx-study-app\data\excluded_qids.txt'):
    if os.path.exists(path):
        with open(path) as f:
            return {int(line.strip()) for line in f if line.strip().isdigit()}
    return set()

def load_questions(xlsx_path, sheet_name):
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    excluded = load_excluded_qids()
    if excluded:
        df = df[~df["QID"].isin(excluded)]
    return df

def get_exam_weight(topic: str, subtopic: str = None) -> float:
    """Get exam weight for a topic/subtopic."""
    EXAM_WEIGHTS = {
        "Data Processing & Transformations": 0.31,
    }
    if subtopic and subtopic in EXAM_WEIGHTS:
        return EXAM_WEIGHTS[subtopic]
    if topic in EXAM_WEIGHTS:
        return EXAM_WEIGHTS[topic]
    return 0.15

# Load data
questions = load_questions(DATA_PATH, SHEET_NAME)

# Check if ExamWeight is in questions before adding it
print(f"ExamWeight in questions before add: {'ExamWeight' in questions.columns}")

# Add exam weights
questions = pd.DataFrame.apply(questions, lambda df: df, axis=1)
questions["ExamWeight"] = questions.apply(
    lambda row: get_exam_weight(row.get("Topic", ""), row.get("Subtopic", "")),
    axis=1
)

print(f"ExamWeight in questions after add: {'ExamWeight' in questions.columns}")
q1532_before = questions[questions['QID'] == 1532][['QID', 'Topic', 'ExamWeight']]
print(f"\nQID 1532 ExamWeight before merge: {q1532_before['ExamWeight'].values}")

attempts = pd.read_csv(ATTEMPTS_PATH)
attempts['timestamp'] = pd.to_datetime(attempts['timestamp'], format='mixed')

# Do the add_performance manually to see where it's lost
att = attempts.copy()
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

# This is the merge
out = questions.merge(agg, on="QID", how="left")

print(f"\nExamWeight in merged output: {'ExamWeight' in out.columns}")
q1532_after = out[out['QID'] == 1532][['QID', 'Topic', 'ExamWeight']]
print(f"QID 1532 ExamWeight after merge: {q1532_after['ExamWeight'].values if len(q1532_after) > 0 else 'NOT FOUND'}")
