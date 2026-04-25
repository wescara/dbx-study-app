import pandas as pd
from datetime import datetime

ATTEMPTS_PATH = r"C:\dbx-study-app\data\attempts.csv"

def load_questions(path):
    return pd.read_excel(path, sheet_name="QuestionBank")

def load_attempts(path=ATTEMPTS_PATH):
    try:
        return pd.read_csv(path, parse_dates=["timestamp"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["QID", "timestamp", "selected", "correct"])

def record_attempt(qid, selected, correct, path=ATTEMPTS_PATH):
    attempt = pd.DataFrame([{
        "QID": int(qid),
        "timestamp": datetime.now(),
        "selected": selected,
        "correct": bool(correct),
    }])
    attempts = load_attempts(path)
    attempts = pd.concat([attempts, attempt], ignore_index=True)
    attempts.to_csv(path, index=False)

def compute_stats(questions, attempts):
    if len(attempts) == 0:
        questions = questions.copy()
        questions["attempts"] = 0
        questions["correct"] = 0
        questions["accuracy"] = 0.0
        return questions

    stats = attempts.groupby("QID").agg(
        attempts=("correct", "count"),
        correct=("correct", "sum")
    ).reset_index()
    stats["accuracy"] = stats["correct"] / stats["attempts"]

    out = questions.merge(stats, on="QID", how="left")
    return out.fillna({"attempts": 0, "correct": 0, "accuracy": 0.0})

def select_daily_questions(df, n=10, confirmed_only=True):
    work = df.copy()

    if confirmed_only and "VerificationStatus" in work.columns:
        work = work[work["VerificationStatus"] == "Confirmed"]

    diff_weight = {"Easy": 0, "Medium": 1, "Hard": 2}
    work["diff_w"] = work["Difficulty"].map(diff_weight).fillna(0)
    work["flag_w"] = work["FlagForReview"].fillna(0).clip(upper=1) * 2
    # LastReviewed staleness: more days since last review → higher boost (cap at 1.5)
    if "LastReviewed" in work.columns:
        now = pd.Timestamp.now()
        work["last_rev"] = pd.to_datetime(work["LastReviewed"], errors="coerce")
        days_since = (now - work["last_rev"]).dt.total_seconds() / 86400
        work["stale_w"] = (days_since.fillna(180) / 90).clip(upper=1.5)
    else:
        work["stale_w"] = 0

    # "ROI-ish" priority: low accuracy + harder + flagged-for-review + staleness boost
    work["priority"] = (1 - work["accuracy"]) * 2 + work["diff_w"] + work["flag_w"] + work["stale_w"]

    return work.sort_values("priority", ascending=False).head(n)