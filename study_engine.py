import pandas as pd
from datetime import datetime
import uuid

ATTEMPTS_PATH = r"C:\dbx-study-app\data\attempts.csv"
TIMED_SESSIONS_PATH = r"C:\dbx-study-app\data\timed_sessions.csv"

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

def select_daily_questions(df, n=10, confirmed_only=True, previously_missed_ratio=0.7):
    """
    Select daily questions with prioritization for previously-missed questions.
    
    Args:
        df: Questions dataframe with stats (from compute_stats)
        n: Number of questions to select
        confirmed_only: If True, only select from Confirmed questions
        previously_missed_ratio: Target ratio of previously-missed (1 incorrect) to total
                                  e.g., 0.7 = 70% previously-missed, 30% other
    """
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

    # Boost for previously-missed (exactly 1 incorrect from master table)
    work["previously_missed"] = work.get("IncorrectCount", 0).fillna(0) == 1
    work["previously_missed_boost"] = work["previously_missed"].astype(float) * 3.0
    
    # "ROI-ish" priority: low accuracy + harder + flagged-for-review + staleness boost + missed boost
    work["priority"] = (1 - work["accuracy"]) * 2 + work["diff_w"] + work["flag_w"] + work["stale_w"] + work["previously_missed_boost"]

    # Sort by priority
    work_sorted = work.sort_values("priority", ascending=False)
    
    # Try to maintain previously_missed_ratio
    previously_missed = work_sorted[work_sorted["previously_missed"]]
    others = work_sorted[~work_sorted["previously_missed"]]
    
    target_missed = max(1, int(n * previously_missed_ratio))
    num_missed = min(target_missed, len(previously_missed))
    num_others = n - num_missed
    
    selected_missed = previously_missed.head(num_missed)
    selected_others = others.head(num_others)
    
    result = pd.concat([selected_missed, selected_others]).sort_values("priority", ascending=False).head(n)
    
    return result


# =============================
# Timed Session Helpers
# =============================
def format_time_remaining(seconds: int) -> str:
    """Convert seconds to MM:SS format."""
    if seconds < 0:
        return "00:00"
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def compute_pace(elapsed_seconds: int, questions_answered: int, ideal_pace_seconds: int = 120) -> dict:
    """
    Compute current pace vs ideal pace.
    ideal_pace_seconds: seconds per question (default 120 = 2 min/q for exam)
    Returns: {
        "pace_status": "on_pace" | "behind" | "ahead",
        "avg_time_per_q": float,
        "ideal_per_q": int,
        "ideal_total_so_far": int,
        "ahead_or_behind_seconds": int (positive = ahead, negative = behind)
    }
    """
    if questions_answered == 0:
        return {
            "pace_status": "on_pace",
            "avg_time_per_q": 0,
            "ideal_per_q": ideal_pace_seconds,
            "ideal_total_so_far": 0,
            "ahead_or_behind_seconds": 0,
        }
    
    avg_per_q = elapsed_seconds / questions_answered
    ideal_total = ideal_pace_seconds * questions_answered
    diff = ideal_total - elapsed_seconds  # positive = ahead
    
    if diff > 30:  # >30 sec ahead
        pace_status = "ahead"
    elif diff < -30:  # >30 sec behind
        pace_status = "behind"
    else:
        pace_status = "on_pace"
    
    return {
        "pace_status": pace_status,
        "avg_time_per_q": round(avg_per_q, 1),
        "ideal_per_q": ideal_pace_seconds,
        "ideal_total_so_far": ideal_total,
        "ahead_or_behind_seconds": diff,
    }


def initialize_timed_session(mode: str) -> dict:
    """
    Initialize a timed session with metadata.
    mode: "exam_mode" (45Q, 90min) | "speed_drill" (15Q, 20min) | "study" (custom)
    """
    if mode == "exam_mode":
        return {
            "session_id": str(uuid.uuid4()),
            "mode": "exam_mode",
            "num_questions": 45,
            "time_limit_seconds": 5400,  # 90 minutes
            "ideal_pace_seconds": 120,  # 2 min/question
            "started_at": datetime.now(),
            "ended_at": None,
            "flagged_qids": [],
            "question_times": {},  # {qid: seconds}
        }
    elif mode == "speed_drill":
        return {
            "session_id": str(uuid.uuid4()),
            "mode": "speed_drill",
            "num_questions": 15,
            "time_limit_seconds": 1200,  # 20 minutes
            "ideal_pace_seconds": 80,  # 1:20 per question
            "started_at": datetime.now(),
            "ended_at": None,
            "flagged_qids": [],
            "question_times": {},
        }
    else:  # "study" mode (no timer)
        return {
            "session_id": str(uuid.uuid4()),
            "mode": "study",
            "num_questions": None,  # User configurable
            "time_limit_seconds": None,  # No limit
            "ideal_pace_seconds": None,
            "started_at": datetime.now(),
            "ended_at": None,
            "flagged_qids": [],
            "question_times": {},
        }


def save_timed_session_metadata(session_data: dict, questions_correct: int, total_questions: int, path: str = TIMED_SESSIONS_PATH) -> None:
    """
    Save timed session metadata to CSV.
    session_data: dict from initialize_timed_session + updates
    """
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    session_data["ended_at"] = datetime.now()
    total_seconds = int((session_data["ended_at"] - session_data["started_at"]).total_seconds())
    avg_time_per_q = total_seconds / total_questions if total_questions > 0 else 0
    accuracy = questions_correct / total_questions if total_questions > 0 else 0.0
    
    row = pd.DataFrame([{
        "session_id": session_data["session_id"],
        "mode": session_data["mode"],
        "started_at": session_data["started_at"],
        "ended_at": session_data["ended_at"],
        "total_time_seconds": total_seconds,
        "questions_count": total_questions,
        "correct_count": questions_correct,
        "accuracy": accuracy,
        "flagged_count": len(session_data.get("flagged_qids", [])),
        "avg_time_per_question": avg_time_per_q,
        "notes": "",
    }])
    
    write_header = not os.path.exists(path)
    row.to_csv(path, mode="a", header=write_header, index=False)


def load_timed_sessions(path: str = TIMED_SESSIONS_PATH) -> pd.DataFrame:
    """Load timed session history."""
    try:
        df = pd.read_csv(path, parse_dates=["started_at", "ended_at"])
        return df
    except FileNotFoundError:
        return pd.DataFrame(columns=[
            "session_id", "mode", "started_at", "ended_at", "total_time_seconds",
            "questions_count", "correct_count", "accuracy", "flagged_count", "avg_time_per_question", "notes"
        ])


def load_flagged_for_session(session_id: str, flagged_path: str = None) -> list:
    """Load all flagged QIDs for a session."""
    import os
    if flagged_path is None:
        flagged_path = r"C:\dbx-study-app\data\session_flagged.csv"
    
    if not os.path.exists(flagged_path):
        return []
    
    df = pd.read_csv(flagged_path)
    session_flagged = df[df["session_id"] == str(session_id)]
    return [int(qid) for qid in session_flagged["QID"].unique()]
