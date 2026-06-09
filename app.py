import os
import traceback
from datetime import datetime

import pandas as pd
import streamlit as st
from study_engine import format_time_remaining, compute_pace

# =============================
# Config
# =============================
DATA_PATH = r"C:\dbx-study-app\data\DBx_Questions.xlsx"
SHEET_NAME = "QuestionBank"
ATTEMPTS_PATH = r"C:\dbx-study-app\data\attempts.csv"
NOTES_PATH = r"C:\dbx-study-app\data\notes.csv"
SYNTAX_QUESTIONS_PATH = r"C:\dbx-study-app\data\syntax_questions_for_review.csv"

DIFF_WEIGHT = {"Easy": 0, "Medium": 1, "Hard": 2}
EXCLUDED_QIDS_PATH = r"C:\dbx-study-app\data\excluded_qids.txt"


def load_excluded_qids(path=EXCLUDED_QIDS_PATH) -> set:
    if os.path.exists(path):
        with open(path) as f:
            return {int(line.strip()) for line in f if line.strip().isdigit()}
    return set()


# =============================
# Attempts persistence
# =============================
def load_attempts(path=ATTEMPTS_PATH) -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="mixed", errors="coerce")
        # Handle missing time_spent column for old records
        if "time_spent" not in df.columns:
            df["time_spent"] = 0
        else:
            df["time_spent"] = df["time_spent"].fillna(0)
        return df
    return pd.DataFrame(columns=["QID", "timestamp", "selected", "correct", "time_spent"])


def record_attempt(qid: int, selected: str, correct: bool, path=ATTEMPTS_PATH, time_spent: int | None = None) -> None:
    import time
    os.makedirs(os.path.dirname(path), exist_ok=True)
    write_header = not os.path.exists(path)
    row = pd.DataFrame([{
        "QID": int(qid),
        "timestamp": datetime.now(),
        "selected": selected,
        "correct": bool(correct),
        "time_spent": int(time_spent) if time_spent is not None else 0,
    }])
    
    # Retry logic for file lock issues
    max_retries = 3
    for attempt in range(max_retries):
        try:
            row.to_csv(path, mode="a", header=write_header, index=False)
            return
        except (PermissionError, OSError) as e:
            if attempt < max_retries - 1:
                time.sleep(0.2)  # Wait 200ms before retrying
            else:
                st.warning(f"⚠️ Could not save attempt (file may be locked). Please close Excel or other programs accessing the data folder.")
                raise


# =============================
# Flagged Questions (Session-Level Review)
# =============================
def save_flagged_attempt(qid: int, session_id: str, flagged_path: str = None) -> None:
    """Save a question flagged during a timed session for review later."""
    if flagged_path is None:
        flagged_path = r"C:\dbx-study-app\data\session_flagged.csv"
    
    os.makedirs(os.path.dirname(flagged_path), exist_ok=True)
    write_header = not os.path.exists(flagged_path)
    row = pd.DataFrame([{
        "QID": int(qid),
        "session_id": str(session_id),
        "timestamp": datetime.now(),
        "reviewed": False,
    }])
    row.to_csv(flagged_path, mode="a", header=write_header, index=False)


def load_flagged_for_session(session_id: str, flagged_path: str = None) -> list:
    """Load all flagged QIDs for a session."""
    if flagged_path is None:
        flagged_path = r"C:\dbx-study-app\data\session_flagged.csv"
    
    if not os.path.exists(flagged_path):
        return []
    
    df = pd.read_csv(flagged_path)
    session_flagged = df[df["session_id"] == str(session_id)]
    return [int(qid) for qid in session_flagged["QID"].unique()]


# =============================
# Notes persistence
# =============================
def load_notes(path=NOTES_PATH) -> pd.DataFrame:
    if os.path.exists(path):
        return pd.read_csv(path, parse_dates=["timestamp"])
    return pd.DataFrame(columns=["QID", "timestamp", "note"])


def save_note(qid: int, note: str, path=NOTES_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    notes = load_notes(path)
    # Keep only one note per QID (latest wins)
    notes = notes[notes["QID"] != int(qid)]
    new_row = pd.DataFrame([{
        "QID": int(qid),
        "timestamp": datetime.now(),
        "note": note,
    }])
    notes = pd.concat([notes, new_row], ignore_index=True)
    notes.to_csv(path, index=False)


def get_note_for_qid(qid: int, notes_df: pd.DataFrame) -> str:
    match = notes_df[notes_df["QID"] == int(qid)]
    if not match.empty:
        return str(match.iloc[-1]["note"])
    return ""


# =============================
# Syntax Questions persistence
# =============================
def load_syntax_questions(path=SYNTAX_QUESTIONS_PATH) -> pd.DataFrame:
    """Load syntax questions, merge with full question bank, calculate miss_count and auto-rotate based on recent attempts."""
    if not os.path.exists(path):
        return pd.DataFrame()
    
    # Load syntax metadata
    syntax_metadata = pd.read_csv(path)
    
    # Load full question bank
    full_questions = load_questions(DATA_PATH, SHEET_NAME)
    
    # Merge to get full question details
    syntax_df = syntax_metadata[["QID"]].merge(
        full_questions, 
        on="QID", 
        how="inner"
    )
    
    # Merge back the syntax metadata (CorrectAnswer, MemoryHook)
    syntax_df = syntax_df.merge(
        syntax_metadata[["QID", "CorrectAnswer", "MemoryHook"]],
        on="QID",
        how="left"
    )
    
    # Calculate miss count for each QID (all-time misses)
    attempts_df = load_attempts()
    if not attempts_df.empty:
        miss_counts = attempts_df[attempts_df["correct"] == False].groupby("QID").size().to_dict()
        syntax_df["miss_count"] = syntax_df["QID"].map(miss_counts).fillna(0).astype(int)
        
        # Get most recent attempt for each QID to determine sort order
        # Group by QID and get the last attempt
        attempts_df_sorted = attempts_df.sort_values("timestamp")
        latest_attempts = attempts_df_sorted.groupby("QID").tail(1)
        
        # Create a mapping of QID -> most recent result (1 = correct, 0 = incorrect)
        # Questions with incorrect recent attempt get priority (0), correct get deprioritized (1)
        recent_correct = latest_attempts.set_index("QID")["correct"].to_dict()
        syntax_df["recent_correct"] = syntax_df["QID"].map(recent_correct).fillna(-1)  # -1 = never attempted
        
        # Sort by: recent incorrect first (0), then never attempted (-1), then recent correct (1), then by miss_count
        syntax_df = syntax_df.sort_values(
            by=["recent_correct", "miss_count"],
            ascending=[True, False]  # Ascending recent_correct puts 0 (incorrect) first, then descending miss_count
        )
    else:
        syntax_df["miss_count"] = 0
        syntax_df["recent_correct"] = -1
        syntax_df = syntax_df.sort_values("miss_count", ascending=False)
    
    return syntax_df


# =============================
# Notebook links persistence
# =============================
# =============================
# Flashcard (Quizlet) persistence
# =============================
FLASHCARDS_PATH = r"C:\dbx-study-app\data\flashcards.csv"


def load_flashcards(path=FLASHCARDS_PATH) -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["timestamp"])
        # Migrate old column names
        if "question" in df.columns and "front" not in df.columns:
            df = df.rename(columns={"question": "front", "correct_answer": "back"})
        return df
    return pd.DataFrame(columns=["QID", "timestamp", "front", "back"])


def save_flashcard(qid: int, front: str, back: str, path=FLASHCARDS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fc = load_flashcards(path)
    # Only deduplicate for question-linked cards (QID > 0); custom cards (QID=0) can stack
    if int(qid) > 0:
        fc = fc[fc["QID"] != int(qid)]
    new_row = pd.DataFrame([{
        "QID": int(qid),
        "timestamp": datetime.now(),
        "front": front,
        "back": back,
    }])
    fc = pd.concat([fc, new_row], ignore_index=True) if not fc.empty else new_row
    fc.to_csv(path, index=False)


def remove_flashcard(qid: int, path=FLASHCARDS_PATH, row_index: int | None = None) -> None:
    if not os.path.exists(path):
        return
    fc = load_flashcards(path)
    if row_index is not None:
        fc = fc.drop(index=row_index).reset_index(drop=True)
    else:
        fc = fc[fc["QID"] != int(qid)]
    fc.to_csv(path, index=False)


def is_flashcard(qid: int, fc_df: pd.DataFrame) -> bool:
    return int(qid) in fc_df["QID"].values


NOTEBOOKS_PATH = r"C:\dbx-study-app\data\notebooks.csv"


def load_notebooks(path=NOTEBOOKS_PATH) -> pd.DataFrame:
    if os.path.exists(path):
        df = pd.read_csv(path, parse_dates=["timestamp"])
        # Migrate old "label" column to "url"
        if "label" in df.columns and "url" not in df.columns:
            df = df.rename(columns={"label": "url"})
        if "url" not in df.columns:
            df["url"] = ""
        return df
    return pd.DataFrame(columns=["QID", "timestamp", "url"])


def save_notebook_link(qid: int, url: str = "", path=NOTEBOOKS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    nbs = load_notebooks(path)
    nbs = nbs[nbs["QID"] != int(qid)]
    new_row = pd.DataFrame([{
        "QID": int(qid),
        "timestamp": datetime.now(),
        "url": url if url else "",
    }])
    if nbs.empty:
        nbs = new_row
    else:
        nbs = pd.concat([nbs, new_row], ignore_index=True)
    nbs.to_csv(path, index=False)


def remove_notebook_link(qid: int, path=NOTEBOOKS_PATH) -> None:
    if not os.path.exists(path):
        return
    nbs = load_notebooks(path)
    nbs = nbs[nbs["QID"] != int(qid)]
    nbs.to_csv(path, index=False)


def has_notebook(qid: int, nbs_df: pd.DataFrame) -> bool:
    return int(qid) in nbs_df["QID"].values


def get_notebook_url(qid: int, nbs_df: pd.DataFrame) -> str:
    match = nbs_df[nbs_df["QID"] == int(qid)]
    if not match.empty:
        val = match.iloc[-1]["url"]
        if pd.notna(val) and str(val).strip():
            return str(val).strip()
    return ""


# =============================
# Questions + metrics
# =============================
@st.cache_data(show_spinner=False)
def remove_emojis(text: str) -> str:
    """Remove emoji and special characters from text."""
    if pd.isna(text):
        return text
    text = str(text)
    # Remove emoji characters (Unicode ranges for emoji)
    import re
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Symbols & pictographs
        "\U0001F680-\U0001F6FF"  # Transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # Flags (iOS)
        "\U00002500-\U00002BEF"  # Chinese characters
        "\U00002702-\U000027B0"  # Dingbats
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "\U0001f926-\U0001f937"  # Additional emoticons
        "\U00010000-\U0010ffff"  # Other characters
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"
        "\u3030"
        "]+", flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)


def load_questions(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    excluded = load_excluded_qids()
    if excluded:
        df = df[~df["QID"].isin(excluded)]
    
    # Remove emojis from all text columns
    text_columns = ["Question", "CorrectAnswer", "Explanation", "A", "B", "C", "D", "E", "F"]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].apply(remove_emojis)
    
    return df


# =============================
# Exam Weight Mapping (May 2026)
# =============================
EXAM_WEIGHTS = {
    # Topic-level weights (fallback for subtopics not explicitly listed)
    "Development and Ingestion": 0.30,
    "Data Processing & Transformations": 0.31,
    "Productionizing Pipelines": 0.18,
    "Data Governance & Quality": 0.11,
    "Databricks Intelligence Platform": 0.10,
    
    # Development and Ingestion (30%)
    "Ingestion": 0.30,
    "Auto Loader": 0.30,
    "Streaming": 0.30,
    "COPY INTO": 0.30,
    
    # Data Processing & Transformations (31%)
    "SQL": 0.31,
    "Spark SQL": 0.31,
    "DataFrame": 0.31,
    "Array Functions": 0.31,
    "Transformations": 0.31,
    "Aggregations": 0.31,
    "Joins": 0.31,
    
    # Productionizing Pipelines (18%)
    "Workflows": 0.18,
    "Delta Live Tables": 0.18,
    "DLT": 0.18,
    "Jobs": 0.18,
    "Scheduling": 0.18,
    "Orchestration": 0.18,
    "OPTIMIZE": 0.18,
    "Performance": 0.18,
    
    # Data Governance & Quality (11%)
    "Unity Catalog": 0.11,
    "Governance": 0.11,
    "Access Control": 0.11,
    "Security": 0.11,
    "Data Quality": 0.11,
    "RBAC": 0.11,
    
    # Databricks Intelligence Platform (10%)
    "Lakehouse": 0.10,
    "Architecture": 0.10,
    "Workspace": 0.10,
}

def get_exam_weight(topic: str, subtopic: str = None) -> float:
    """Get exam weight for a topic/subtopic. Default 0.15 if not explicitly mapped."""
    # Check subtopic first (more specific)
    if subtopic and subtopic in EXAM_WEIGHTS:
        return EXAM_WEIGHTS[subtopic]
    # Fall back to topic
    if topic in EXAM_WEIGHTS:
        return EXAM_WEIGHTS[topic]
    # Default weight if not found
    return 0.15

def add_exam_weights(df: pd.DataFrame) -> pd.DataFrame:
    """Add exam weight column to questions DataFrame."""
    df = df.copy()
    df["ExamWeight"] = df.apply(
        lambda row: get_exam_weight(row.get("Topic", ""), row.get("Subtopic", "")),
        axis=1
    )
    return df


def add_performance(questions: pd.DataFrame, attempts: pd.DataFrame) -> pd.DataFrame:
    q = questions.copy()
    if attempts.empty:
        q["attempts"] = 0
        q["correct_total"] = 0
        q["accuracy"] = 0.0
        return q

    att = attempts.copy()
    # Time-decay: half-life of 14 days — recent attempts count more
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


def compute_priority(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["diff_w"] = work["Difficulty"].map(DIFF_WEIGHT).fillna(0)
    work["flag_w"] = work["FlagForReview"].fillna(0).clip(upper=1) * 2
    # LastReviewed staleness: more days since last review → higher boost (cap at 1.5)
    if "LastReviewed" in work.columns:
        now = pd.Timestamp.now()
        work["last_rev"] = pd.to_datetime(work["LastReviewed"], errors="coerce")
        days_since = (now - work["last_rev"]).dt.total_seconds() / 86400
        work["stale_w"] = (days_since.fillna(180) / 90).clip(upper=1.5)
    else:
        work["stale_w"] = 0
    # Recently added boost: new questions get priority for first 7 days (max 2.0x boost)
    if "DateAdded" in work.columns:
        now = pd.Timestamp.now()
        work["date_added"] = pd.to_datetime(work["DateAdded"], errors="coerce")
        days_since_added = (now - work["date_added"]).dt.total_seconds() / 86400
        # Linear decay: full boost for 0 days, zero boost after 7 days
        work["new_boost"] = (1 - (days_since_added / 7).clip(0, 1)) * 2.0
    else:
        work["new_boost"] = 0
    # Boost for previously-missed questions (exactly 1 incorrect from master table): 3.0x boost for high-ROI review
    work["previously_missed"] = work.get("IncorrectCount", 0).fillna(0) == 1
    work["missed_boost"] = work["previously_missed"].astype(float) * 3.0
    # ROI-ish: low accuracy + harder + flagged-for-review + staleness boost + newly added boost + missed boost
    work["priority"] = (1 - work["accuracy"]) * 2 + work["diff_w"] + work["flag_w"] + work["stale_w"] + work["new_boost"] + work["missed_boost"]
    return work


def get_options(row: pd.Series) -> dict:
    opts = {}
    for letter in ["A", "B", "C", "D", "E", "F"]:
        if letter in row.index and pd.notna(row.get(letter)):
            opts[letter] = row.get(letter)
    return opts


def reset_study_session():
    st.session_state.session_key = None
    st.session_state.session_qids = []
    st.session_state.session_map = {}
    st.session_state.i = 0
    st.session_state.step = "answer"   # answer | review
    st.session_state.review = None
    st.session_state.session_attempts_start = None
    
    # Timed session state
    st.session_state.session_mode = "study"  # study | speed_drill | exam_mode
    st.session_state.study_variant = "normal"  # normal | deep_dive | untouched | random | recent_misses
    st.session_state.study_deep_dive_topic = None
    st.session_state.study_untouched_topic = None
    st.session_state.session_time_started = None
    st.session_state.session_time_limit = None
    st.session_state.session_time_ideal_pace = None
    st.session_state.session_flagged_qids = []
    st.session_state.session_skipped_qids = []  # Questions skipped during review (to reanswer at end)
    st.session_state.session_question_times = {}  # {qid: time_in_seconds}
    st.session_state.session_auto_submitted = False
    st.session_state.session_current_q_start_time = None
    st.session_state.session_id = None


def apply_focus_filters(df: pd.DataFrame) -> pd.DataFrame:
    focus_type = st.session_state.get("focus_type")
    study_variant = st.session_state.get("study_variant", "normal")
    
    # Handle study variants (these override focus_type for Study Mode)
    if study_variant == "deep_dive":
        topic = st.session_state.get("study_deep_dive_topic")
        if topic:
            work = df[df["Topic"] == topic].copy()
            # Sort by weakness (low accuracy first)
            work = work.sort_values("accuracy", ascending=True)
            return work
    
    elif study_variant == "untouched":
        # Questions with 0 attempts
        work = df[df["attempts"] == 0].copy()
        # Filter by topic if selected
        topic = st.session_state.get("study_untouched_topic")
        if topic:
            work = work[work["Topic"] == topic]
        # Sort by difficulty (harder first) then by stale weight
        return work.sort_values(["Difficulty"], ascending=False, key=lambda x: x.map({"Hard": 0, "Medium": 1, "Easy": 2}) if x.name == "Difficulty" else x)
    
    elif study_variant == "random":
        # Will be handled in build_study_session with use_random=True
        return df
    
    elif study_variant == "recent_misses":
        # Questions answered incorrectly in the last 24 hours
        import pandas as pd
        now = pd.Timestamp.now()
        cutoff = now - pd.Timedelta(hours=24)
        
        # Get all attempts data - need to load fresh to get latest
        attempts_recent = load_attempts()
        if not attempts_recent.empty:
            attempts_recent['timestamp'] = pd.to_datetime(attempts_recent['timestamp'], format='mixed', errors='coerce')
            recent_misses = attempts_recent[(attempts_recent['timestamp'] >= cutoff) & (attempts_recent['correct'] == False)]
            missed_qids = set(recent_misses['QID'].unique())
            work = df[df['QID'].isin(missed_qids)].copy()
            # Sort by number of times missed (most missed first)
            miss_counts = recent_misses.groupby('QID').size().to_dict()
            work['miss_count'] = work['QID'].map(miss_counts)
            work = work.sort_values('miss_count', ascending=False)
            return work
        return df
    
    # Default: apply focus filters if any
    if not focus_type:
        return df

    work = df.copy()

    if focus_type == "weakest_topic":
        t = st.session_state.get("focus_topic")
        if t:
            work = work[work["Topic"] == t]

    elif focus_type == "weakest_subtopic":
        t = st.session_state.get("focus_topic")
        s = st.session_state.get("focus_subtopic")
        if t and s:
            work = work[(work["Topic"] == t) & (work["Subtopic"] == s)]

    elif focus_type == "high_risk":
        work = work[
            (work["Difficulty"].isin(["Medium", "Hard"])) &
            (work["attempts"] > 0) &
            (work["accuracy"] < 0.6)
        ]

    elif focus_type == "flagged":
        work = work[work["FlagForReview"].fillna(0) == 1]

    return work


def build_study_session(stats: pd.DataFrame, n: int, use_random: bool = False) -> None:
    """
    Build a stable session list of QIDs + a snapshot map {qid -> question dict}.
    Prevents reordering mid-session when attempts are recorded.
    
    Args:
        stats: DataFrame with question stats
        n: Number of questions to select
        use_random: If True, randomly select questions. If False, use priority sorting (default).
    """
    study_variant = st.session_state.get("study_variant", "normal")
    
    if use_random or study_variant == "random":
        # For timed modes and random mode: randomly select questions
        import numpy as np
        work = stats.sample(n=min(int(n), len(stats)), random_state=None).reset_index(drop=True)
    else:
        # For study mode: sort by priority (low accuracy, flagged, harder, stale)
        # For deep_dive and untouched: already sorted by apply_focus_filters
        if "priority" in stats.columns:
            work = stats.sort_values("priority", ascending=False).head(int(n)).reset_index(drop=True)
        else:
            work = stats.head(int(n)).reset_index(drop=True)
    
    qids = [int(x) for x in work["QID"].tolist()]

    qmap = {}
    for _, r in work.iterrows():
        qid = int(r["QID"])
        qmap[qid] = {
            "QID": qid,
            "Topic": r.get("Topic", ""),
            "Subtopic": r.get("Subtopic", ""),
            "Difficulty": r.get("Difficulty", ""),
            "Question": r.get("Question", ""),
            "CorrectLetter": r.get("CorrectLetter", ""),
            "Explanation": r.get("Explanation", "") if "Explanation" in r.index else r.get("CorrectAnswer", ""),
            "VerificationNotes": r.get("VerificationNotes", None),
            "Options": get_options(r),
        }

    st.session_state.session_qids = qids
    st.session_state.session_map = qmap
    st.session_state.i = 0
    st.session_state.step = "answer"
    st.session_state.review = None


def build_session_summary(attempts_now: pd.DataFrame, start_index: int, qmap: dict) -> dict:
    """
    Session-only summary from attempts added since start_index, limited to this session qmap.
    """
    if attempts_now.empty or start_index is None or start_index >= len(attempts_now):
        return {"answered": 0}

    sess = attempts_now.iloc[start_index:].copy()
    sess["QID"] = sess["QID"].astype(int)
    sess = sess[sess["QID"].isin(set(qmap.keys()))].copy()

    if sess.empty:
        return {"answered": 0}

    answered = len(sess)
    correct = int(sess["correct"].sum())
    accuracy = correct / answered if answered else 0.0

    # enrich with metadata for breakdowns
    def meta(qid, field, default=""):
        return qmap.get(int(qid), {}).get(field, default)

    sess["Difficulty"] = sess["QID"].apply(lambda x: meta(x, "Difficulty"))
    sess["Topic"] = sess["QID"].apply(lambda x: meta(x, "Topic"))
    sess["Subtopic"] = sess["QID"].apply(lambda x: meta(x, "Subtopic"))
    sess["CorrectLetter"] = sess["QID"].apply(lambda x: meta(x, "CorrectLetter"))

    diff_breakdown = (
        sess.groupby("Difficulty")["correct"]
        .agg(answered="count", correct="sum")
        .reset_index()
    )
    diff_breakdown["accuracy"] = diff_breakdown["correct"] / diff_breakdown["answered"]

    topic_breakdown = (
        sess.groupby("Topic")["correct"]
        .agg(answered="count", correct="sum")
        .reset_index()
        .sort_values("answered", ascending=False)
        .head(10)
    )
    topic_breakdown["accuracy"] = topic_breakdown["correct"] / topic_breakdown["answered"]

    subtopic_breakdown = (
        sess.groupby(["Topic", "Subtopic"])["correct"]
        .agg(answered="count", correct="sum")
        .reset_index()
    )
    subtopic_breakdown["accuracy"] = subtopic_breakdown["correct"] / subtopic_breakdown["answered"]

    # weakest subtopic this session (min accuracy; tie-break by most answered)
    weakest_sub = (
        subtopic_breakdown.sort_values(["accuracy", "answered"], ascending=[True, False]).iloc[0]
        if not subtopic_breakdown.empty else None
    )

    missed = sess[sess["correct"] == False].copy()
    missed_view = missed[["QID", "selected", "CorrectLetter", "Topic", "Subtopic", "Difficulty"]].copy()

    # Attach notes to missed questions
    notes_df = load_notes()
    missed_view["Note"] = missed_view["QID"].apply(lambda x: get_note_for_qid(x, notes_df))

    return {
        "answered": answered,
        "correct": correct,
        "accuracy": accuracy,
        "diff_breakdown": diff_breakdown.sort_values("Difficulty"),
        "topic_breakdown": topic_breakdown,
        "subtopic_breakdown": subtopic_breakdown.sort_values(["accuracy", "answered"], ascending=[True, False]),
        "weakest_subtopic": weakest_sub,
        "missed": missed_view
    }


# =============================
# Search Functionality
# =============================
def search_content(questions: pd.DataFrame, keyword: str, case_sensitive: bool = False, confirmed_only: bool = False) -> list:
    """
    Search for keyword across questions, answers, notes, flashcards, and notebooks.
    Returns a list of dicts with matching results.
    
    Args:
        questions: DataFrame with questions
        keyword: Search keyword (can be substring)
        case_sensitive: Whether search is case-sensitive
        confirmed_only: Only include confirmed questions
    
    Returns:
        List of dicts with QID, matching_field, matching_text, note, flashcard_front, flashcard_back, notebook_url
    """
    results = []
    
    # Prepare keyword
    search_key = keyword if case_sensitive else keyword.lower()
    
    # Load auxiliary data
    notes_df = load_notes()
    flashcards_df = load_flashcards()
    notebooks_df = load_notebooks()
    
    # Filter to confirmed questions if requested
    search_df = questions.copy()
    if confirmed_only and "VerificationStatus" in search_df.columns:
        search_df = search_df[search_df["VerificationStatus"] == "Confirmed"].copy()
    
    # Build a map for quick lookups
    notes_map = {int(qid): note for qid, note in zip(notes_df["QID"], notes_df["note"]) if pd.notna(note)}
    flashcard_map = {}  # {qid: [(front, back, index), ...]}
    for idx, row in flashcards_df.iterrows():
        qid = int(row["QID"])
        if qid not in flashcard_map:
            flashcard_map[qid] = []
        flashcard_map[qid].append((row["front"], row["back"], idx))
    
    notebook_map = {int(qid): url for qid, url in zip(notebooks_df["QID"], notebooks_df["url"]) if pd.notna(url)}
    
    # Search through questions
    for _, row in search_df.iterrows():
        qid = int(row["QID"])
        matched_fields = []
        
        # Search Question field
        q_text = str(row.get("Question", ""))
        q_text_search = q_text if case_sensitive else q_text.lower()
        if search_key in q_text_search:
            matched_fields.append({
                "field": "Question",
                "text": q_text,
                "snippet": q_text[:200] if len(q_text) > 200 else q_text
            })
        
        # Search Answer field (correct answer)
        if "CorrectAnswer" in row.index:
            correct_ans = str(row.get("CorrectAnswer", ""))
            correct_ans_search = correct_ans if case_sensitive else correct_ans.lower()
            if search_key in correct_ans_search:
                matched_fields.append({
                    "field": "CorrectAnswer",
                    "text": correct_ans,
                    "snippet": correct_ans[:200] if len(correct_ans) > 200 else correct_ans
                })
        
        # Search option fields (A, B, C, D, E, F)
        for letter in ["A", "B", "C", "D", "E", "F"]:
            if letter in row.index:
                opt_text = str(row.get(letter, ""))
                opt_text_search = opt_text if case_sensitive else opt_text.lower()
                if search_key in opt_text_search:
                    matched_fields.append({
                        "field": f"Option {letter}",
                        "text": opt_text,
                        "snippet": opt_text[:200] if len(opt_text) > 200 else opt_text
                    })
        
        # Search Note field if exists
        if "Note" in row.index:
            note_text = str(row.get("Note", ""))
            note_text_search = note_text if case_sensitive else note_text.lower()
            if search_key in note_text_search:
                matched_fields.append({
                    "field": "Note (Question)",
                    "text": note_text,
                    "snippet": note_text[:200] if len(note_text) > 200 else note_text
                })
        
        # Search Explanation field if exists
        if "Explanation" in row.index:
            expl_text = str(row.get("Explanation", ""))
            expl_text_search = expl_text if case_sensitive else expl_text.lower()
            if search_key in expl_text_search:
                matched_fields.append({
                    "field": "Explanation",
                    "text": expl_text,
                    "snippet": expl_text[:200] if len(expl_text) > 200 else expl_text
                })
        
        # Search user notes (notes.csv)
        if qid in notes_map:
            user_note = notes_map[qid]
            user_note_search = user_note if case_sensitive else user_note.lower()
            if search_key in user_note_search:
                matched_fields.append({
                    "field": "User Note",
                    "text": user_note,
                    "snippet": user_note[:200] if len(user_note) > 200 else user_note
                })
        
        # Search flashcard front/back
        if qid in flashcard_map:
            for front, back, fc_idx in flashcard_map[qid]:
                front_search = front if case_sensitive else front.lower()
                back_search = back if case_sensitive else back.lower()
                if search_key in front_search:
                    matched_fields.append({
                        "field": "Flashcard (Front)",
                        "text": front,
                        "snippet": front[:200] if len(front) > 200 else front
                    })
                if search_key in back_search:
                    matched_fields.append({
                        "field": "Flashcard (Back)",
                        "text": back,
                        "snippet": back[:200] if len(back) > 200 else back
                    })
        
        # If any matches found, add to results
        if matched_fields:
            result = {
                "QID": qid,
                "Topic": row.get("Topic", "N/A"),
                "Subtopic": row.get("Subtopic", "N/A"),
                "Difficulty": row.get("Difficulty", "N/A"),
                "matched_fields": matched_fields,
                "question_text": str(row.get("Question", ""))[:300],
                "correct_answer": str(row.get("CorrectAnswer", "")),
                "correct_letter": row.get("CorrectLetter", ""),
                "options": get_options(row),
                "notebook_url": notebook_map.get(qid, ""),
                "has_flashcard": qid in flashcard_map,
                "has_user_note": qid in notes_map
            }
            results.append(result)
    
    return results


# =============================
# Navigation (fixes StreamlitAPIException)
# =============================
if "nav_mode" not in st.session_state:
    st.session_state.nav_mode = "Study Mode"

# Callback for search jump
def jump_to_question(qid):
    st.session_state.jump_to_qid = qid
    st.session_state.jump_from_search = True

# Apply nav_request BEFORE widget instantiation
if st.session_state.get("nav_request"):
    st.session_state.nav_mode = st.session_state.nav_request
    st.session_state.nav_request = None

# Handle jump_from_search navigation (before radio button is created)
if st.session_state.get("jump_from_search"):
    st.session_state.nav_mode = "Study Mode"
    st.session_state.jump_from_search = False

# Check for pending jumps (from button clicks) and rerun
if st.session_state.get("pending_jump_qid") is not None:
    st.session_state.jump_to_qid = st.session_state.pop("pending_jump_qid")
    st.session_state.jump_from_search = st.session_state.pop("pending_jump_from_search", False)
    st.rerun()

# =============================
# Streamlit UI
# =============================
st.set_page_config(page_title="Databricks Associate Engineer Study App", layout="wide", page_icon="favicon_pass_exam.ico")
st.title("Databricks Associate Engineer Study App")

# Calculate days until exam
exam_date = pd.Timestamp("2026-06-17")
today = pd.Timestamp.now()
days_until_exam = (exam_date - today).days

# Display exam countdown in sidebar with visual emphasis (green success style)
if days_until_exam > 0:
    st.sidebar.markdown(f"<div style='text-align: center; padding: 20px; background-color: rgba(0, 200, 100, 0.2); border-radius: 10px; border: 2px solid #00C864;'><p style='margin: 0; font-size: 14px; color: #999;'>📌 EXAM: JUNE 17</p><p style='margin: 10px 0 0 0; font-size: 36px; font-weight: bold; color: #00C864;'>{days_until_exam}</p><p style='margin: 5px 0 0 0; font-size: 12px; color: #999;'>days left</p></div>", unsafe_allow_html=True)
else:
    st.sidebar.warning("⚠️ Exam is today or past!")
st.sidebar.markdown("---")

# Load data early to display today's progress at top of sidebar
questions = load_questions(DATA_PATH, SHEET_NAME)
questions = add_exam_weights(questions)  # Add exam weight column
attempts = load_attempts()

# Display today's progress card prominently at top of sidebar
if not attempts.empty:
    today = pd.Timestamp.now().normalize()
    today_attempts = attempts[attempts["timestamp"] >= today]
    today_count = len(today_attempts)
    today_correct = int(today_attempts["correct"].sum()) if today_count > 0 else 0
    today_missed = today_count - today_correct
    today_acc = f"{today_correct / today_count:.0%}" if today_count > 0 else "–"
    
    # Today's Progress card
    progress_html = f"<div style='text-align: center; padding: 20px; background-color: rgba(79, 172, 254, 0.2); border-radius: 10px; border: 2px solid #4FACFE;'><p style='margin: 0; font-size: 14px; color: #999;'>📊 TODAY'S PROGRESS</p><p style='margin: 15px 0 5px 0; font-size: 28px; font-weight: bold; color: #4FACFE;'>{today_count}</p><p style='margin: 0 0 15px 0; font-size: 12px; color: #999;'>answered</p><div style='display: flex; justify-content: space-around; margin: 15px 0 0 0; padding-top: 15px; border-top: 1px solid rgba(79, 172, 254, 0.3);'><div><p style='margin: 0; font-size: 18px; font-weight: bold; color: #FF6B6B;'>{today_missed}</p><p style='margin: 3px 0 0 0; font-size: 11px; color: #999;'>missed</p></div><div><p style='margin: 0; font-size: 18px; font-weight: bold; color: #51CF66;'>{today_acc}</p><p style='margin: 3px 0 0 0; font-size: 11px; color: #999;'>accuracy</p></div></div></div>"
    st.sidebar.markdown(progress_html, unsafe_allow_html=True)
else:
    no_attempts_html = "<div style='text-align: center; padding: 20px; background-color: rgba(79, 172, 254, 0.2); border-radius: 10px; border: 2px solid #4FACFE;'><p style='margin: 0; font-size: 14px; color: #999;'>📊 TODAY'S PROGRESS</p><p style='margin: 15px 0 0 0; font-size: 12px; color: #999;'>No attempts yet.</p></div>"
    st.sidebar.markdown(no_attempts_html, unsafe_allow_html=True)

st.sidebar.markdown("---")

# Sidebar navigation (do not mutate nav_mode after this widget exists)
mode = st.sidebar.radio("Mode", ["Study Mode", "Weakness Dashboard", "Notes Review", "Syntax Reference", "Search"], key="nav_mode")

st.sidebar.markdown("### Settings")
confirmed_only = st.sidebar.checkbox("Confirmed only (recommended)", value=True)
hide_mastered = st.sidebar.checkbox("Hide mastered (≥85% and ≥3 attempts)", value=True)
show_qid = st.sidebar.checkbox("Show key (QID)", value=True)
session_n = st.sidebar.number_input("Questions per session", min_value=5, max_value=50, value=15, step=5)


st.sidebar.markdown("### Jump to QID")
jump_qid = st.sidebar.number_input("Enter QID:", min_value=0, value=0, step=1, key="jump_qid_input")
if st.sidebar.button("Go", key="jump_qid_btn") and jump_qid > 0:
    st.session_state.jump_to_qid = int(jump_qid)
    st.session_state.nav_request = "Study Mode"
    st.rerun()

with st.expander("Startup status", expanded=False):
    st.write("Working directory:", os.getcwd())
    st.write("Excel path:", DATA_PATH)
    st.write("Attempts path:", ATTEMPTS_PATH)

try:
    if not os.path.exists(DATA_PATH):
        st.error("❌ Excel file not found.")
        st.info(r"Expected: C:\dbx-study-app\data\DBx_Questions.xlsx")
        st.stop()

    st.success(f"✅ Loaded {len(questions)} questions from {SHEET_NAME}")
    st.caption(f"Attempts recorded: {len(attempts)} (stored in {ATTEMPTS_PATH})")

    stats = add_performance(questions, attempts)

    # Confirmed-only filter
    if confirmed_only and "VerificationStatus" in stats.columns:
        stats = stats[stats["VerificationStatus"] == "Confirmed"].copy()

    # Mastery filter
    stats["mastered"] = (stats["accuracy"] >= 0.85) & (stats["attempts"] >= 3)
    if hide_mastered:
        stats = stats[~stats["mastered"] | (stats["FlagForReview"].fillna(0) == 1)].copy()

    # Priority
    stats = compute_priority(stats)

    # =============================
    # Weakness Dashboard
    # =============================
    if mode == "Weakness Dashboard":
        st.header("📊 Weakness Dashboard")

        # Show active focus filter
        focus_type = st.session_state.get("focus_type")
        if focus_type == "weakest_topic":
            st.info(f"🎯 Active focus: Weakest Topic → {st.session_state.get('focus_topic')}")
        elif focus_type == "weakest_subtopic":
            st.info(f"🎯 Active focus: Weakest Subtopic → {st.session_state.get('focus_topic')} / {st.session_state.get('focus_subtopic')}")
        elif focus_type == "high_risk":
            st.info("🎯 Active focus: High‑Risk (Medium/Hard + <60% accuracy)")
        elif focus_type == "flagged":
            st.info("🎯 Active focus: Flagged for Review")
        else:
            st.caption("No active focus filter — studying general pool.")
        
        # Exam weight info
        st.info(
            "📚 **New for May 2026 Exam:** Topics are now weighted by exam importance. "
            "**Priority Score** = (100% - Your Accuracy) × Exam Weight. "
            "Focus on high-priority topics first to maximize exam points! "
            "**Weights:** Development/Ingestion 30% • Data Processing 31% • Pipelines 18% • Governance 11% • Platform 10%"
        )

        attempted = stats[stats["attempts"] > 0].copy()
        if attempted.empty:
            st.info("No attempts recorded yet. Switch to Study Mode and answer ~10–15 questions first.")
            st.stop()

        # Overall Progress
        st.subheader("✅ Overall Progress")
        c1, c2, c3, c4, c5 = st.columns(5, gap="medium")
        
        # Calculate metrics
        total_questions = stats["QID"].nunique()
        questions_attempted = attempted["QID"].nunique()
        unanswered = total_questions - questions_attempted
        overall_acc = attempted["accuracy"].mean()
        on_track = int((attempted["accuracy"] >= 0.80).sum())
        risky = attempted[(attempted["Difficulty"].isin(["Medium", "Hard"])) & (attempted["accuracy"] < 0.6)]
        risky_count = len(risky)
        
        with c1:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                color: white;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">📚</div>
                <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">{questions_attempted}</div>
                <div style="font-size: 14px; opacity: 0.9;">Questions Attempted</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c2:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                color: white;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">🎯</div>
                <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">{overall_acc:.1%}</div>
                <div style="font-size: 14px; opacity: 0.9;">Overall Accuracy</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c3:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                color: white;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">✅</div>
                <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">{on_track}</div>
                <div style="font-size: 14px; opacity: 0.9;">On Track (≥80%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c4:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                color: white;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">🚨</div>
                <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">{risky_count}</div>
                <div style="font-size: 14px; opacity: 0.9;">High-Risk (M/H & <60%)</div>
            </div>
            """, unsafe_allow_html=True)
        
        with c5:
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
                border-radius: 12px;
                padding: 24px;
                text-align: center;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                color: #333;
            ">
                <div style="font-size: 28px; margin-bottom: 8px;">📭</div>
                <div style="font-size: 32px; font-weight: bold; margin-bottom: 4px;">{unanswered}</div>
                <div style="font-size: 14px; opacity: 0.9;">Unanswered</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # =============================
        # 🎯 EXAM READINESS (10-Day Sprint)
        # =============================
        st.subheader("🎯 Exam Readiness — 10-Day Sprint")
        
        # Calculate estimated test score
        overall_accuracy = attempted["accuracy"].mean()
        accuracy_pct = overall_accuracy * 100
        goal_pct = 80
        gap_pct = goal_pct - accuracy_pct
        
        # Display readiness cards
        ex1, ex2 = st.columns(2)
        with ex1:
            if gap_pct <= 0:
                st.metric("🎉 Estimated Score", f"{accuracy_pct:.1f}%", f"✅ Goal reached!")
            else:
                st.metric("📊 Estimated Score", f"{accuracy_pct:.1f}%", f"Need +{gap_pct:.1f}%")
        with ex2:
            st.metric("🎯 Goal", "80%")

        # Topic-by-topic breakdown
        st.subheader("📋 Topic Scorecard")
        topic_scores = (
            attempted.groupby("Topic")
            .agg(
                accuracy=("accuracy", "mean"),
                questions=("QID", "count"),
                exam_weight=("ExamWeight", "mean")
            )
            .reset_index()
        )
        topic_scores = topic_scores.sort_values("accuracy")
        
        # Calculate gap to 80% for each topic
        topic_scores["gap_to_80"] = 80 - (topic_scores["accuracy"] * 100)
        
        # Create colored display
        display_df = topic_scores.copy()
        display_df["accuracy"] = display_df["accuracy"].apply(lambda x: f"{x:.1%}")
        display_df["exam_weight"] = display_df["exam_weight"].apply(lambda x: f"{x:.0%}")
        display_df["gap_to_80"] = topic_scores["gap_to_80"].apply(
            lambda x: f"✅ Done" if x <= 0 else f"+{x:.1f}pts"
        )
        
        st.dataframe(
            display_df[["Topic", "accuracy", "questions", "exam_weight", "gap_to_80"]].rename(
                columns={
                    "Topic": "Topic",
                    "accuracy": "Current Acc",
                    "questions": "Q Count",
                    "exam_weight": "Weight",
                    "gap_to_80": "Path to 80%"
                }
            ),
            width='stretch',
            hide_index=True
        )
        
        st.markdown("---")
        
        # Quick Wins
        st.subheader("⚡ Quick Wins (75–79% → 80%)")
        quick_wins = topic_scores[(topic_scores["accuracy"] >= 0.75) & (topic_scores["accuracy"] < 0.80)]
        if not quick_wins.empty:
            quick_wins = quick_wins.sort_values("questions", ascending=False)
            qw_df = quick_wins.copy()
            qw_df["accuracy"] = qw_df["accuracy"].apply(lambda x: f"{x:.1%}")
            qw_df["gap_to_80"] = (80 - quick_wins["accuracy"] * 100).apply(lambda x: f"+{x:.1f}pts")
            st.info(
                f"🎯 {len(quick_wins)} topic(s) close to 80%! Small study boost = big score gain.\n\n"
                + "Click 'Study Mode' and focus on these topics to cross the finish line."
            )
            st.dataframe(
                qw_df[["Topic", "accuracy", "questions", "gap_to_80"]].rename(
                    columns={"Topic": "Topic", "accuracy": "Current", "questions": "Q's", "gap_to_80": "Lift"}
                ),
                width='stretch',
                hide_index=True
            )
        else:
            st.success("✅ No quick wins needed — you're above 80% everywhere!")
        
        # Critical Gaps
        st.subheader("🚨 Critical Gaps (<70% accuracy)")
        critical = topic_scores[topic_scores["accuracy"] < 0.70]
        if not critical.empty:
            critical = critical.sort_values("exam_weight", ascending=False)
            crit_df = critical.copy()
            crit_df["accuracy"] = crit_df["accuracy"].apply(lambda x: f"{x:.1%}")
            crit_df["exam_weight"] = crit_df["exam_weight"].apply(lambda x: f"{x:.0%}")
            crit_df["potential_impact"] = (
                (0.70 - critical["accuracy"]) * critical["exam_weight"] * 100
            ).apply(lambda x: f"+{x:.1f}pts if fixed")
            
            st.warning(
                f"⚠️ {len(critical)} topic(s) below 70%! These will drag your exam score.\n\n"
                "**Priority: Study these topics first for maximum exam impact.**"
            )
            st.dataframe(
                crit_df[["Topic", "accuracy", "exam_weight", "potential_impact"]].rename(
                    columns={
                        "Topic": "Topic",
                        "accuracy": "Current",
                        "exam_weight": "Weight",
                        "potential_impact": "Potential Gain"
                    }
                ),
                width='stretch',
                hide_index=True
            )
        else:
            st.success("✅ Great! No critical gaps — you're above 70% everywhere!")

        # Coverage Gaps
        st.subheader("🕳️ Topic Coverage Gaps")
        all_topics = stats.groupby("Topic")["QID"].count().reset_index().rename(columns={"QID": "total"})
        attempted_topics = attempted.groupby("Topic")["QID"].count().reset_index().rename(columns={"QID": "attempted"})
        coverage = all_topics.merge(attempted_topics, on="Topic", how="left").fillna({"attempted": 0})
        coverage["attempted"] = coverage["attempted"].astype(int)
        coverage["coverage"] = coverage["attempted"] / coverage["total"]
        coverage = coverage.sort_values("coverage")

        untouched_topics = coverage[coverage["attempted"] == 0]
        if not untouched_topics.empty:
            st.warning(f"⚠️ {len(untouched_topics)} topic(s) with ZERO attempts — potential exam blind spots!")
            st.dataframe(untouched_topics[["Topic", "total"]], width='stretch')

        all_subtopics = stats.groupby(["Topic", "Subtopic"])["QID"].count().reset_index().rename(columns={"QID": "total"})
        attempted_subs = attempted.groupby(["Topic", "Subtopic"])["QID"].count().reset_index().rename(columns={"QID": "attempted"})
        sub_coverage = all_subtopics.merge(attempted_subs, on=["Topic", "Subtopic"], how="left").fillna({"attempted": 0})
        sub_coverage["attempted"] = sub_coverage["attempted"].astype(int)
        sub_coverage["coverage"] = sub_coverage["attempted"] / sub_coverage["total"]
        untouched_subs = sub_coverage[sub_coverage["attempted"] == 0].sort_values("total", ascending=False)
        if not untouched_subs.empty:
            st.caption(f"{len(untouched_subs)} subtopic(s) never attempted:")
            st.dataframe(untouched_subs[["Topic", "Subtopic", "total"]].head(20), width='stretch')
        else:
            st.success("All topics and subtopics have been attempted!")

        st.markdown("---")

        # Weakest Topics (sorted by priority: impact on exam score)
        st.subheader("🎯 Weakest Topics (by Exam Priority)")
        topic_weak = (
            attempted.groupby("Topic")
            .agg(
                questions=("QID", "count"),
                avg_accuracy=("accuracy", "mean"),
                exam_weight=("ExamWeight", "mean")
            )
            .reset_index()
        )
        topic_weak["priority_score"] = (1 - topic_weak["avg_accuracy"]) * topic_weak["exam_weight"] * 100
        topic_weak = topic_weak.sort_values("priority_score", ascending=False)
        topic_weak["avg_accuracy"] = topic_weak["avg_accuracy"].apply(lambda x: f"{x:.1%}")
        topic_weak["exam_weight"] = topic_weak["exam_weight"].apply(lambda x: f"{x:.0%}")
        topic_weak["priority_score"] = topic_weak["priority_score"].apply(lambda x: f"{x:.1f}")
        st.dataframe(topic_weak, width='stretch')

        # Weakest Subtopics (sorted by priority)
        st.subheader("🔴 Weakest Subtopics (by Exam Priority, Top 15)")
        subtopic_weak = (
            attempted.groupby(["Topic", "Subtopic"])
            .agg(
                questions=("QID", "count"),
                avg_accuracy=("accuracy", "mean"),
                exam_weight=("ExamWeight", "mean")
            )
            .reset_index()
        )
        subtopic_weak["priority_score"] = (1 - subtopic_weak["avg_accuracy"]) * subtopic_weak["exam_weight"] * 100
        subtopic_weak = subtopic_weak.sort_values("priority_score", ascending=False)
        subtopic_weak["avg_accuracy"] = subtopic_weak["avg_accuracy"].apply(lambda x: f"{x:.1%}")
        subtopic_weak["exam_weight"] = subtopic_weak["exam_weight"].apply(lambda x: f"{x:.0%}")
        subtopic_weak["priority_score"] = subtopic_weak["priority_score"].apply(lambda x: f"{x:.1f}")
        st.dataframe(subtopic_weak.head(15), width='stretch')

        # High-risk questions (prioritized by exam weight)
        st.subheader("🔥 High‑Risk Questions (Medium/Hard + <60% accuracy, by Exam Impact)")
        high_risk = attempted[
            (attempted["Difficulty"].isin(["Medium", "Hard"])) &
            (attempted["accuracy"] < 0.6)
        ].copy()
        
        # Calculate priority: (1 - accuracy) * exam_weight
        high_risk["priority"] = (1 - high_risk["accuracy"]) * high_risk["ExamWeight"]
        high_risk = high_risk.sort_values("priority", ascending=False)
        
        notes_df = load_notes()
        high_risk["Note"] = high_risk["QID"].apply(lambda x: get_note_for_qid(x, notes_df))
        
        # Format display columns
        display_cols = ["QID", "Topic", "Subtopic", "Difficulty", "attempts", "accuracy", "ExamWeight", "priority", "Note"]
        display_cols = [c for c in display_cols if c in high_risk.columns]
        
        high_risk_display = high_risk[display_cols].head(25).copy()
        high_risk_display["accuracy"] = high_risk_display["accuracy"].apply(lambda x: f"{x:.1%}")
        high_risk_display["ExamWeight"] = high_risk_display["ExamWeight"].apply(lambda x: f"{x:.0%}")
        high_risk_display["priority"] = high_risk_display["priority"].apply(lambda x: f"{x:.3f}")
        
        # Display with clickable QID column
        st.markdown("_Click on a QID to study that question_")
        cols = st.columns([1.2, 2, 2, 1, 1, 1, 1, 1])
        col_headers = ["QID", "Topic", "Subtopic", "Difficulty", "Attempts", "Accuracy", "Exam Weight", "Priority"]
        for i, header in enumerate(col_headers):
            cols[i].markdown(f"**{header}**")
        
        for _, row in high_risk_display.iterrows():
            cols = st.columns([1.2, 2, 2, 1, 1, 1, 1, 1])
            
            # Make QID clickable
            if cols[0].button(str(int(row["QID"])), key=f"qid_{row['QID']}_btn", use_container_width=True):
                st.session_state.jump_to_qid = int(row["QID"])
                st.session_state.nav_request = "Study Mode"
                st.rerun()
            
            cols[1].write(row["Topic"])
            cols[2].write(row["Subtopic"])
            cols[3].write(row["Difficulty"])
            cols[4].write(str(int(row["attempts"])))
            cols[5].write(row["accuracy"])
            cols[6].write(row["ExamWeight"])
            cols[7].write(row["priority"])

        # Progress Over Time
        st.subheader("📈 Progress Over Time")
        if not attempts.empty:
            att_copy = attempts.copy()
            att_copy["date"] = att_copy["timestamp"].dt.date
            daily = att_copy.groupby("date").agg(
                answered=("correct", "count"),
                correct=("correct", "sum")
            ).reset_index()
            daily["accuracy"] = daily["correct"] / daily["answered"]
            daily["cumulative_answered"] = daily["answered"].cumsum()
            daily["cumulative_correct"] = daily["correct"].cumsum()
            daily["cumulative_accuracy"] = daily["cumulative_correct"] / daily["cumulative_answered"]

            col_daily, col_cum = st.columns(2)
            with col_daily:
                st.caption("Daily accuracy")
                st.line_chart(daily.set_index("date")["accuracy"])
            with col_cum:
                st.caption("Cumulative accuracy")
                st.line_chart(daily.set_index("date")["cumulative_accuracy"])

            st.caption(f"Study days: {len(daily)} | Total attempts: {int(daily['answered'].sum())}")
        else:
            st.info("No attempts yet — progress charts will appear after your first session.")

        st.markdown("---")

        # Actions
        st.subheader("🎯 Actions (Jump into focused Study Mode)")
        weakest_topic = topic_weak.iloc[0]["Topic"]
        weakest_sub = subtopic_weak.iloc[0]
        weakest_sub_topic = weakest_sub["Topic"]
        weakest_sub_subtopic = weakest_sub["Subtopic"]

        b1, b2, b3, b4, b5 = st.columns(5)

        with b1:
            if st.button("Study weakest Topic"):
                st.session_state.focus_type = "weakest_topic"
                st.session_state.focus_topic = weakest_topic
                st.session_state.focus_subtopic = None
                reset_study_session()
                st.session_state.nav_request = "Study Mode"
                st.rerun()

        with b2:
            if st.button("Study weakest Subtopic"):
                st.session_state.focus_type = "weakest_subtopic"
                st.session_state.focus_topic = weakest_sub_topic
                st.session_state.focus_subtopic = weakest_sub_subtopic
                reset_study_session()
                st.session_state.nav_request = "Study Mode"
                st.rerun()

        with b3:
            if st.button("Study High‑Risk"):
                st.session_state.focus_type = "high_risk"
                st.session_state.focus_topic = None
                st.session_state.focus_subtopic = None
                reset_study_session()
                st.session_state.nav_request = "Study Mode"
                st.rerun()

        with b4:
            if st.button("Study Flagged"):
                st.session_state.focus_type = "flagged"
                st.session_state.focus_topic = None
                st.session_state.focus_subtopic = None
                reset_study_session()
                st.session_state.nav_request = "Study Mode"
                st.rerun()

        with b5:
            if st.button("Clear focus"):
                st.session_state.focus_type = None
                st.session_state.focus_topic = None
                st.session_state.focus_subtopic = None
                reset_study_session()
                st.rerun()

        # Quizlet Flashcards section
        st.markdown("---")
        st.subheader("🃏 Quizlet Flashcards")

        # Add custom flashcard form
        with st.expander("➕ Add custom flashcard", expanded=False):
            custom_front = st.text_input("Front (question/prompt):", key="custom_fc_front",
                                         placeholder="e.g. Slow ONE query? →")
            custom_back = st.text_input("Back (answer):", key="custom_fc_back",
                                        placeholder="e.g. Increase SQL warehouse SIZE")
            if st.button("Add flashcard", key="add_custom_fc"):
                if custom_front.strip() and custom_back.strip():
                    save_flashcard(0, custom_front.strip(), custom_back.strip())
                    st.success("Custom flashcard added! 🃏")
                    st.rerun()
                else:
                    st.warning("Both front and back are required.")

        fc_df_dash = load_flashcards()
        if fc_df_dash.empty:
            st.caption("No flashcards yet. Flag them during review or add custom ones above.")
        else:
            st.write(f"**{len(fc_df_dash)} flashcard(s)** for Quizlet.")
            display_fc = fc_df_dash.copy()
            display_fc["Source"] = display_fc["QID"].apply(lambda x: f"QID {x}" if x > 0 else "Custom")
            st.dataframe(
                display_fc[["Source", "front", "back", "timestamp"]].sort_values("timestamp", ascending=False),
                width='stretch',
            )

            # Delete individual flashcards
            with st.expander("🗑️ Remove a flashcard"):
                fc_options = {i: f"{r['front'][:60]}..." if len(str(r['front'])) > 60 else str(r['front'])
                              for i, r in fc_df_dash.iterrows()}
                del_idx = st.selectbox("Select flashcard to remove:", options=list(fc_options.keys()),
                                       format_func=lambda x: fc_options[x], key="fc_del_select")
                if st.button("Remove selected", key="fc_del_btn"):
                    remove_flashcard(0, row_index=del_idx)
                    st.success("Flashcard removed.")
                    st.rerun()

            # Tab-separated export for Quizlet import
            st.markdown("#### Export for Quizlet (copy & paste)")
            st.caption("Quizlet import format: paste into Quizlet → Import → set separator to **Tab** and rows to **Newline**.")
            export_lines = []
            for _, row in fc_df_dash.iterrows():
                front = str(row["front"]).replace("\t", " ").replace("\n", " ")
                back = str(row["back"]).replace("\t", " ").replace("\n", " ")
                export_lines.append(f"{front}\t{back}")
            export_text = "\n".join(export_lines)
            st.code(export_text, language=None)



        st.stop()

    # =============================
    # Notes Review Mode
    # =============================
    if mode == "Notes Review":
        st.header("📝 Notes Review")
        st.markdown("Review all your study notes organized by topic. Click on a QID to study that question.")
        
        notes_df = load_notes()
        
        if notes_df.empty:
            st.info("📭 No notes yet. Create notes while studying to see them here!")
        else:
            # Join notes with questions to get topic and question text
            notes_with_context = notes_df.merge(
                questions[["QID", "Topic", "Subtopic", "Question"]],
                on="QID",
                how="left"
            )
            
            # Topic filter
            all_topics = sorted(notes_with_context["Topic"].dropna().unique().tolist())
            selected_topics = st.multiselect(
                "Filter by topic (leave blank for all):",
                options=all_topics,
                default=None,
                key="notes_topic_filter"
            )
            
            if selected_topics:
                filtered_notes = notes_with_context[notes_with_context["Topic"].isin(selected_topics)]
            else:
                filtered_notes = notes_with_context.copy()
            
            # Sort by date (newest first)
            filtered_notes = filtered_notes.sort_values("timestamp", ascending=False)
            
            # Display stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Notes", len(filtered_notes))
            with col2:
                st.metric("Topics Covered", filtered_notes["Topic"].nunique())
            with col3:
                st.metric("Subtopics Covered", filtered_notes["Subtopic"].nunique())
            
            st.markdown("---")
            
            # Display notes in expandable sections by topic
            for topic in sorted(filtered_notes["Topic"].unique()):
                topic_notes = filtered_notes[filtered_notes["Topic"] == topic]
                with st.expander(f"**{topic}** ({len(topic_notes)} notes)", expanded=False):
                    for _, row in topic_notes.iterrows():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if st.button(
                                f"QID {int(row['QID'])}",
                                key=f"notes_qid_{row['QID']}_btn",
                                use_container_width=True
                            ):
                                st.session_state.jump_to_qid = int(row["QID"])
                                st.session_state.nav_request = "Study Mode"
                                st.rerun()
                        with col2:
                            st.write(f"**{row['Subtopic']}**")
                            note_display = row['note'].replace('\n', '  \n')  # Markdown line breaks
                            st.markdown(f"📝 {note_display}")
                            if pd.notna(row["Question"]):
                                st.caption(f"Q: {str(row['Question'])[:100]}...")
                            st.markdown("---")

    # =============================
    # Syntax Reference Page
    # =============================
    if mode == "Syntax Reference":
        st.header("⚙️ Syntax Quick Reference")
        st.markdown("Review syntax patterns. Click **Study** to practice the full question.")
        
        syntax_df = load_syntax_questions()
        
        if syntax_df.empty:
            st.info("📭 No syntax questions file found.")
        else:
            # Filter by miss count
            col1, col2 = st.columns([2, 1])
            with col1:
                filter_option = st.radio(
                    "Filter by miss count:",
                    ["All", "High (5+)", "Medium (2-4)", "Low (1)"],
                    horizontal=True,
                    key="syntax_filter"
                )
            
            if filter_option == "High (5+)":
                filtered_syntax = syntax_df[syntax_df["miss_count"] >= 5]
                filter_color = "🔴"
            elif filter_option == "Medium (2-4)":
                filtered_syntax = syntax_df[(syntax_df["miss_count"] >= 2) & (syntax_df["miss_count"] < 5)]
                filter_color = "🟡"
            elif filter_option == "Low (1)":
                filtered_syntax = syntax_df[syntax_df["miss_count"] == 1]
                filter_color = "🟢"
            else:
                filtered_syntax = syntax_df
                filter_color = ""
            
            if filtered_syntax.empty:
                st.info(f"No syntax questions in the '{filter_option}' category.")
            else:
                # Count only questions that still need work (not recently correct)
                needs_work = filtered_syntax[filtered_syntax["recent_correct"] != 1]
                
                # Stats (only for questions still needing work)
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Still Need Work", len(needs_work))
                with col2:
                    st.metric("Never Attempted", len(needs_work[needs_work["recent_correct"] == -1]))
                with col3:
                    st.metric("Total Misses", int(needs_work["miss_count"].sum()) if not needs_work.empty else 0)
                with col4:
                    st.metric("Topics", needs_work["Topic"].nunique() if not needs_work.empty else 0)
                
                st.markdown("---")
                
                # Display each syntax pattern
                for idx, (_, row) in enumerate(filtered_syntax.iterrows()):
                    qid = int(row["QID"])
                    miss_count = int(row["miss_count"])
                    topic = row.get("Topic", "")
                    subtopic = row.get("Subtopic", "")
                    note = row.get("Note", "")
                    correct_answer = row.get("CorrectAnswer", "")
                    memory_hook = row.get("MemoryHook", "")
                    recent_correct = row.get("recent_correct", -1)
                    
                    # Color code by miss frequency
                    if miss_count >= 5:
                        miss_color = "🔴"
                    elif miss_count >= 2:
                        miss_color = "🟡"
                    else:
                        miss_color = "🟢"
                    
                    # Status indicator for most recent attempt
                    if recent_correct == 1:
                        status = "✅ Last: Correct"
                    elif recent_correct == 0:
                        status = "❌ Last: Incorrect"
                    else:
                        status = "⭕ Never attempted"
                    
                    # Create expander for each pattern
                    with st.expander(
                        f"{miss_color} QID {qid} • {topic} • {subtopic} (missed {miss_count}x) — {status}",
                        expanded=False
                    ):
                        # Display syntax (correct answer)
                        st.write("**💾 Syntax:**")
                        st.code(correct_answer, language="sql")
                        
                        # Display memory hook if available
                        if memory_hook and memory_hook != "":
                            st.write("**🧠 Memory Hook:**")
                            st.info(memory_hook)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("📚 Study Question", key=f"syntax_study_{qid}", use_container_width=True):
                                st.session_state.jump_to_qid = qid
                                st.session_state.nav_request = "Study Mode"
                                st.rerun()
                        with col2:
                            st.caption(f"QID: {qid}")
                        with col3:
                            st.caption(f"Misses: {miss_count}")

    # =============================
    # Search Mode
    # =============================
    if mode == "Search" and not st.session_state.get("jump_to_qid"):
        st.header("🔍 Search Questions")
        
        # Callback to trigger search on Enter key
        def trigger_search():
            st.session_state.trigger_search_flag = True
        
        # Search input (Enter key triggers search via on_change callback)
        search_keyword = st.text_input(
            "Enter keyword to search (e.g. 'collect_set'):",
            placeholder="Type a keyword, phrase, or technical term...",
            key="search_keyword_input",
            on_change=trigger_search
        )
        
        # Options and button on same line
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            case_sensitive = st.checkbox("Case sensitive", value=False, key="search_case_sensitive")
        
        with col2:
            st.write("")  # Spacer
        
        with col3:
            perform_search = st.button("🔍 Search", use_container_width=True, key="btn_perform_search")
        
        # Perform search if button clicked or Enter pressed in search box
        perform_search = perform_search or st.session_state.get("trigger_search_flag", False)
        
        if perform_search and search_keyword.strip():
            st.session_state.trigger_search_flag = False  # Reset flag
            st.markdown("---")
            with st.spinner("Searching..."):
                results = search_content(questions, search_keyword.strip(), case_sensitive=case_sensitive, confirmed_only=confirmed_only)
            
            if results:
                st.success(f"Found **{len(results)}** question(s) matching '{search_keyword}'")
                st.markdown("---")
                
                for idx, result in enumerate(results, 1):
                    with st.expander(
                        f"QID {result['QID']} | {result['Topic']} → {result['Subtopic']} | {result['Difficulty']}",
                        expanded=(idx == 1)  # Expand first result by default
                    ):
                        # Question text
                        st.markdown("**❓ Question:**")
                        st.write(result["question_text"])
                        
                        # Answer options
                        st.markdown("**📋 Options:**")
                        for letter, text in result["options"].items():
                            st.write(f"**{letter})** {text}")
                        
                        # Additional metadata (flashcard only)
                        if result["has_flashcard"]:
                            st.info("🃏 Has flashcard")
                        
                        # Action button
                        st.button(
                            "🎯 Study this Question",
                            key=f"go_q_{result['QID']}",
                            on_click=jump_to_question,
                            args=(result['QID'],)
                        )
            else:
                st.warning(f"No questions found matching '{search_keyword}'. Try a different keyword.")
        elif not search_keyword.strip() and perform_search:
            st.warning("Please enter a search keyword first.")
        
        st.markdown("---")
        st.caption("💡 **Tips:**")
        st.caption("- Search is case-insensitive by default (use checkbox to toggle)")
        st.caption("- Searches through: Questions, Answers, Options, User Notes, Flashcards, Explanations")
        st.caption("- Example: 'collect_set', 'ADLS', 'performance', 'Databricks SQL'")
        
        st.stop()

    # =============================
    # Study Mode (Two-stage)
    # =============================
    st.header("🧠 Study Mode")

    # ===== MODE SELECTION =====
    st.subheader("Select your study mode:")
    mode_col1, mode_col2, mode_col3 = st.columns(3)
    
    current_mode = st.session_state.get("session_mode", "study")
    
    with mode_col1:
        study_label = ("✓ " if current_mode == "study" else "") + "🧠 Study Mode (Custom)"
        if st.button(study_label, use_container_width=True, key="btn_study_mode"):
            reset_study_session()
            st.session_state.session_mode = "study"
            st.rerun()
    
    with mode_col2:
        drill_label = ("✓ " if current_mode == "speed_drill" else "") + "⚡ Speed Drill (15Q × 20min)"
        if st.button(drill_label, use_container_width=True, key="btn_speed_drill"):
            reset_study_session()
            st.session_state.session_mode = "speed_drill"
            from study_engine import initialize_timed_session
            timed = initialize_timed_session("speed_drill")
            st.session_state.session_id = timed["session_id"]
            st.session_state.session_time_started = timed["started_at"]
            st.session_state.session_time_limit = timed["time_limit_seconds"]
            st.session_state.session_time_ideal_pace = timed["ideal_pace_seconds"]
            st.rerun()
    
    with mode_col3:
        exam_label = ("✓ " if current_mode == "exam_mode" else "") + "📝 Exam Sim (45Q × 90min)"
        if st.button(exam_label, use_container_width=True, key="btn_exam_mode"):
            reset_study_session()
            st.session_state.session_mode = "exam_mode"
            from study_engine import initialize_timed_session
            timed = initialize_timed_session("exam_mode")
            st.session_state.session_id = timed["session_id"]
            st.session_state.session_time_started = timed["started_at"]
            st.session_state.session_time_limit = timed["time_limit_seconds"]
            st.session_state.session_time_ideal_pace = timed["ideal_pace_seconds"]
            st.rerun()
    
    st.markdown("---")
    
    # Study Mode Variants (only show if in study mode)
    if current_mode == "study":
        st.subheader("📚 Study Variant:")
        variant_row1 = st.columns(3)
        variant_row2 = st.columns(2)
        
        current_variant = st.session_state.get("study_variant", "normal")
        
        with variant_row1[0]:
            variant_label = ("✓ " if current_variant == "normal" else "") + "📊 Priority (weak first)"
            if st.button(variant_label, use_container_width=True, key="btn_variant_normal"):
                st.session_state.study_variant = "normal"
                st.session_state.session_key = None  # Rebuild session
                st.rerun()
        
        with variant_row1[1]:
            variant_label = ("✓ " if current_variant == "untouched" else "") + "🆕 Untouched (0 attempts)"
            if st.button(variant_label, use_container_width=True, key="btn_variant_untouched"):
                st.session_state.study_variant = "untouched"
                st.session_state.study_untouched_topic = None  # Reset topic to force new selection
                st.session_state.pop("untouched_topic_select", None)  # Clear selectbox cache
                st.session_state.session_key = None
                st.rerun()
        
        with variant_row1[2]:
            variant_label = ("✓ " if current_variant == "recent_misses" else "") + "📕 Recent Misses"
            if st.button(variant_label, use_container_width=True, key="btn_variant_recent_misses"):
                st.session_state.study_variant = "recent_misses"
                st.session_state.session_key = None
                st.rerun()
        
        with variant_row2[0]:
            variant_label = ("✓ " if current_variant == "random" else "") + "🎲 Random"
            if st.button(variant_label, use_container_width=True, key="btn_variant_random"):
                st.session_state.study_variant = "random"
                st.session_state.session_key = None
                st.rerun()
        
        with variant_row2[1]:
            variant_label = ("✓ " if current_variant == "deep_dive" else "") + "🎯 Topic Deep Dive"
            if st.button(variant_label, use_container_width=True, key="btn_variant_deep_dive"):
                st.session_state.study_variant = "deep_dive"
                st.session_state.study_deep_dive_topic = None  # Reset topic to force new selection
                st.session_state.pop("deep_dive_topic_select", None)  # Clear selectbox cache
                st.session_state.session_key = None
                st.rerun()
        
        # Topic selector for Deep Dive mode
        if current_variant == "deep_dive":
            # Sort topics by average accuracy (weakest first = lowest accuracy)
            topic_stats = stats.groupby("Topic").agg({
                "accuracy": "mean",
                "attempts": "sum"
            }).reset_index().sort_values("accuracy", ascending=True)
            topics = topic_stats["Topic"].tolist()
            
            # Create display names with accuracy indicators
            topic_display = {}
            for _, row in topic_stats.iterrows():
                t = row["Topic"]
                acc = row["accuracy"]
                topic_display[t] = f"{t} ({acc:.0%})"
            
            # If no topic selected, show placeholder and default to index 0
            if not st.session_state.get("study_deep_dive_topic"):
                selected_topic = st.selectbox(
                    "Select topic to deep dive:",
                    options=[None] + topics,
                    format_func=lambda x: "— Choose a topic —" if x is None else topic_display[x],
                    key="deep_dive_topic_select"
                )
                if selected_topic:
                    st.session_state.study_deep_dive_topic = selected_topic
                    st.session_state.session_key = None
                    st.rerun()
            else:
                # Topic already selected, show it in selectbox
                selected_topic = st.session_state.get("study_deep_dive_topic")
                current_index = topics.index(selected_topic) if selected_topic in topics else 0
                selected_topic = st.selectbox(
                    "Select topic to deep dive:",
                    options=topics,
                    index=current_index,
                    format_func=lambda x: topic_display[x],
                    key="deep_dive_topic_select"
                )
                if selected_topic != st.session_state.get("study_deep_dive_topic"):
                    st.session_state.study_deep_dive_topic = selected_topic
                    st.session_state.session_key = None
                    st.rerun()
            
            # Display topic stats
            if st.session_state.get("study_deep_dive_topic"):
                topic_questions = stats[stats["Topic"] == st.session_state.get("study_deep_dive_topic")]
                weak_count = len(topic_questions[topic_questions["accuracy"] < 0.85])
                st.caption(f"📊 {len(topic_questions)} total | {weak_count} below 85% accuracy")
        
        # Topic selector for Untouched mode
        if current_variant == "untouched":
            # Get untouched questions by topic
            untouched = stats[stats["attempts"] == 0].copy()
            untouched_by_topic = untouched.groupby("Topic")["QID"].count().sort_values(ascending=False)
            topics = untouched_by_topic.index.tolist()
            
            # Create display names with count indicators
            topic_display = {}
            for t in topics:
                count = untouched_by_topic[t]
                topic_display[t] = f"{t} ({count} untouched)"
            
            # Always show the same selectbox structure
            selected_topic = st.selectbox(
                "Select topic to study (untouched questions):",
                options=topics,
                format_func=lambda x: topic_display[x],
                key="untouched_topic_select"
            )
            if selected_topic != st.session_state.get("study_untouched_topic"):
                st.session_state.study_untouched_topic = selected_topic
                st.session_state.session_key = None
                st.rerun()
            
            # Display topic stats
            if selected_topic:
                topic_untouched = untouched[untouched["Topic"] == selected_topic]
                st.caption(f"🆕 {len(topic_untouched)} untouched questions in this topic")
    
    st.markdown("---")

    if "step" not in st.session_state:
        reset_study_session()

    # apply focus filters
    focused = apply_focus_filters(stats)
    if focused.empty:
        st.warning("Focus filter produced no questions. Falling back to general set.")
        focused = stats.copy()

    # Determine number of questions based on session mode
    current_session_mode = st.session_state.get("session_mode", "study")
    if current_session_mode == "exam_mode":
        num_questions = 45
    elif current_session_mode == "speed_drill":
        num_questions = 15
    else:  # study mode
        num_questions = int(session_n)

    # build stable session when settings/focus change
    session_key = (
        num_questions,
        bool(confirmed_only),
        bool(hide_mastered),
        st.session_state.get("focus_type"),
        st.session_state.get("focus_topic"),
        st.session_state.get("focus_subtopic"),
        current_session_mode,
        st.session_state.get("study_variant", "normal"),
        st.session_state.get("study_deep_dive_topic"),
        st.session_state.get("study_untouched_topic"),
    )

    if st.session_state.get("session_key") != session_key or not st.session_state.get("session_qids"):
        # Preserve session state during rebuild (don't lose position or review!)
        preserved_step = st.session_state.get("step")
        preserved_review = st.session_state.get("review")
        preserved_i = st.session_state.get("i", 0)
        
        # RESET all session state when topic changes in deep_dive or untouched mode
        if st.session_state.get("study_variant") == "deep_dive":
            # If session_key is None or the topic changed, do a full reset
            old_key = st.session_state.get("session_key")
            if old_key is None or (old_key and old_key[8] != session_key[8]):
                preserved_i = 0  # Reset position
                preserved_step = "answer"  # Reset to answer phase
                preserved_review = None  # Clear review state
        
        elif st.session_state.get("study_variant") == "untouched":
            # If session_key is None or the topic changed, do a full reset
            old_key = st.session_state.get("session_key")
            if old_key is None or (old_key and old_key[9] != session_key[9]):
                preserved_i = 0  # Reset position
                preserved_step = "answer"  # Reset to answer phase
                preserved_review = None  # Clear review state
        
        st.session_state.session_key = session_key
        st.session_state.session_attempts_start = len(attempts)
        # Use random selection for timed modes, priority-based for study mode
        use_random = current_session_mode in ["exam_mode", "speed_drill"]
        build_study_session(focused, num_questions, use_random=use_random)
        
        # Restore session state if we're actively in a session (don't reset mid-session!)
        # Only reset if this is a fresh session start
        if preserved_step or preserved_review:
            st.session_state.step = preserved_step
            st.session_state.review = preserved_review
            # Keep position if we're navigating (i > 0 means we're past the first question)
            if preserved_i > 0:
                st.session_state.i = min(preserved_i, len(st.session_state.session_qids) - 1)

    # Handle jump-to-QID request
    jump_target = st.session_state.pop("jump_to_qid", None)
    if jump_target is not None:
        jump_target = int(jump_target)
        # Check if the QID exists in the loaded questions
        if jump_target in questions["QID"].values:
            # Inject into front of session if not already present
            qids_current = st.session_state.session_qids
            if jump_target not in qids_current:
                st.session_state.session_qids.insert(st.session_state.i, jump_target)
                # Build snapshot for the jumped question
                row = questions[questions["QID"] == jump_target].iloc[0]
                st.session_state.session_map[jump_target] = {
                    "QID": jump_target,
                    "Topic": row.get("Topic", ""),
                    "Subtopic": row.get("Subtopic", ""),
                    "Difficulty": row.get("Difficulty", ""),
                    "Question": row.get("Question", ""),
                    "CorrectLetter": row.get("CorrectLetter", ""),
                    "Explanation": row.get("Explanation", ""),
                    "VerificationNotes": row.get("VerificationNotes", None),
                    "Options": get_options(row),
                }
            else:
                # Jump to existing position
                st.session_state.i = qids_current.index(jump_target)
            st.session_state.step = "answer"
            st.session_state.review = None
            st.rerun()
        else:
            st.warning(f"QID {jump_target} not found in question bank.")

    qids = st.session_state.session_qids
    qmap = st.session_state.session_map

    # focus banner
    focus_type = st.session_state.get("focus_type")
    if focus_type == "weakest_topic":
        st.info(f"Focus: Weakest Topic → {st.session_state.get('focus_topic')}")
    elif focus_type == "weakest_subtopic":
        st.info(f"Focus: Weakest Subtopic → {st.session_state.get('focus_topic')} / {st.session_state.get('focus_subtopic')}")
    elif focus_type == "high_risk":
        st.info("Focus: High‑Risk (Medium/Hard + <60% accuracy)")
    elif focus_type == "flagged":
        st.info("Focus: Flagged for Review (211 questions you marked)")

    # session complete -> check if there are skipped questions to reanswer
    session_mode = st.session_state.get("session_mode", "study")
    skipped_qids = st.session_state.get("session_skipped_qids", [])
    
    if st.session_state.i >= len(qids) and skipped_qids and session_mode in ["exam_mode", "speed_drill"]:
        # Loop back to reanswer skipped questions
        st.session_state.session_qids = skipped_qids
        st.session_state.i = 0
        st.session_state.step = "answer"
        st.session_state.review = None
        st.session_state.session_skipped_qids = []  # Clear skipped list to avoid re-looping
        st.info("📋 **Reanswering skipped questions...**")
        st.rerun()
    
    if st.session_state.i >= len(qids):
        st.success("✅ Session complete! Great work.")

        attempts_now = load_attempts()
        start_idx = st.session_state.get("session_attempts_start", None)
        summary = build_session_summary(attempts_now, start_idx, qmap)

        if summary.get("answered", 0) == 0:
            st.info("No recorded attempts found for this session.")
        else:
            st.subheader("📈 Session Summary")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Answered", summary["answered"])
            with c2:
                st.metric("Correct", summary["correct"])
            with c3:
                st.metric("Accuracy", f"{summary['accuracy']:.1%}")

            st.subheader("By Difficulty")
            st.dataframe(summary["diff_breakdown"], width='stretch')

            st.subheader("Top Topics Covered")
            st.dataframe(summary["topic_breakdown"], width='stretch')

            if summary["weakest_subtopic"] is not None:
                ws = summary["weakest_subtopic"]
                st.subheader("🎯 Weakest Subtopic This Session")
                st.write(f"**{ws['Topic']} → {ws['Subtopic']}** (accuracy {ws['accuracy']:.1%} over {int(ws['answered'])} attempts)")

            if not summary["missed"].empty:
                st.subheader("Missed Questions (to review)")
                st.dataframe(summary["missed"], width='stretch')

            # ===== FLAGGED QUESTIONS REVIEW (Timed Modes) =====
            current_session_mode = st.session_state.get("session_mode", "study")
            if current_session_mode in ["exam_mode", "speed_drill"] and st.session_state.session_id:
                from study_engine import load_flagged_for_session
                flagged_qids = load_flagged_for_session(st.session_state.session_id)
                
                if flagged_qids:
                    st.markdown("---")
                    st.subheader(f"🚩 Flagged for Review ({len(flagged_qids)} questions)")
                    st.caption("These are questions you flagged during the session. Review them below to understand why you flagged them.")
                    
                    # Display flagged questions
                    flagged_display = []
                    for qid in flagged_qids:
                        if qid in qmap:
                            q_info = qmap[qid]
                            flagged_display.append({
                                "QID": qid,
                                "Topic": q_info.get("Topic", ""),
                                "Subtopic": q_info.get("Subtopic", ""),
                                "Difficulty": q_info.get("Difficulty", ""),
                            })
                    
                    if flagged_display:
                        flagged_df = pd.DataFrame(flagged_display)
                        st.dataframe(flagged_df, width='stretch')
                    
                    # Option to review flagged questions
                    if st.button("📖 Review flagged questions in detail", key="btn_review_flagged"):
                        # Create a flagged-only review session with full question data
                        if flagged_qids:
                            # Rebuild session to contain only flagged questions
                            flagged_qmap = {}
                            for qid in flagged_qids:
                                if qid in qmap:
                                    flagged_qmap[qid] = qmap[qid]
                            
                            # Set up flagged review session
                            st.session_state.session_qids = flagged_qids
                            st.session_state.session_map = flagged_qmap
                            st.session_state.i = 0
                            st.session_state.step = "answer"
                            st.session_state.review = None
                            st.session_state.review_mode = "flagged_only"
                            st.rerun()

            # ===== TIME ANALYTICS (Timed Modes) =====
            if current_session_mode in ["exam_mode", "speed_drill"]:
                attempts_now = load_attempts()
                start_idx = st.session_state.get("session_attempts_start", None)
                
                if not attempts_now.empty and start_idx is not None and start_idx < len(attempts_now):
                    st.markdown("---")
                    st.subheader("⏱️ Time Analytics")
                    
                    sess = attempts_now.iloc[start_idx:].copy()
                    sess["QID"] = sess["QID"].astype(int)
                    sess = sess[sess["QID"].isin(set(qmap.keys()))].copy()
                    
                    if not sess.empty and "time_spent" in sess.columns:
                        total_time = sess["time_spent"].sum()
                        avg_time_per_q = sess["time_spent"].mean()
                        
                        # Overall time metrics
                        tc1, tc2, tc3 = st.columns(3)
                        with tc1:
                            time_str = format_time_remaining(int(total_time))
                            st.metric("Total Time", time_str)
                        with tc2:
                            st.metric("Avg/Question", f"{avg_time_per_q:.1f}s")
                        with tc3:
                            ideal_pace = st.session_state.get("session_time_ideal_pace", 120)
                            if avg_time_per_q < ideal_pace:
                                st.metric("vs Ideal", f"✅ {ideal_pace - avg_time_per_q:.0f}s faster")
                            else:
                                st.metric("vs Ideal", f"⚠️ {avg_time_per_q - ideal_pace:.0f}s slower")
                        
                        # Time breakdown by difficulty
                        if "Difficulty" in sess.columns:
                            st.subheader("Time by Difficulty")
                            diff_time = sess.groupby("Difficulty")["time_spent"].agg(
                                ["count", "mean", "sum"]
                            ).round(1).reset_index()
                            diff_time.columns = ["Difficulty", "Questions", "Avg (sec)", "Total (sec)"]
                            st.dataframe(diff_time, width='stretch', use_container_width=True)
                        
                        # Time breakdown by topic
                        if "Topic" in sess.columns:
                            st.subheader("Time by Topic (Top 10)")
                            topic_time = sess.groupby("Topic")["time_spent"].agg(
                                ["count", "mean"]
                            ).sort_values("mean", ascending=False).head(10).reset_index()
                            topic_time.columns = ["Topic", "Questions", "Avg (sec)"]
                            topic_time["Avg (sec)"] = topic_time["Avg (sec)"].round(1)
                            st.dataframe(topic_time, width='stretch', use_container_width=True)

        colA, colB, colC, colD = st.columns(4)

        with colA:
            if st.button("Restart session"):
                reset_study_session()
                st.rerun()

        with colB:
            if st.button("Go to Weakness Dashboard"):
                st.session_state.nav_request = "Weakness Dashboard"
                st.rerun()

        with colC:
            if st.button("Clear focus + new session"):
                st.session_state.focus_type = None
                st.session_state.focus_topic = None
                st.session_state.focus_subtopic = None
                reset_study_session()
                st.rerun()

        with colD:
            if st.button("Continue weakest subtopic") and summary.get("weakest_subtopic") is not None:
                ws = summary["weakest_subtopic"]
                st.session_state.focus_type = "weakest_subtopic"
                st.session_state.focus_topic = ws["Topic"]
                st.session_state.focus_subtopic = ws["Subtopic"]
                reset_study_session()
                st.rerun()

        st.stop()

    # current question snapshot
    current_qid = qids[st.session_state.i]
    q = qmap.get(current_qid)
    if not q:
        st.error("Could not load current question from session map.")
        st.stop()

    question_box = st.container(border=True)
    review_box = st.container(border=True)

    # Load notebooks and flashcards once for display
    nbs_df = load_notebooks()
    fc_df = load_flashcards()

    # ===== TIMER LOGIC (for timed modes) =====
    session_mode = st.session_state.get("session_mode", "study")
    is_timed = session_mode in ["exam_mode", "speed_drill"]
    
    if is_timed and st.session_state.session_time_started is not None:
        from datetime import timedelta
        elapsed_seconds = int((datetime.now() - st.session_state.session_time_started).total_seconds())
        time_limit = st.session_state.session_time_limit or 5400
        remaining_seconds = max(0, time_limit - elapsed_seconds)
        
        # Check for timeout
        if remaining_seconds <= 0 and not st.session_state.session_auto_submitted:
            st.session_state.session_auto_submitted = True
            st.error("⏰ TIME'S UP! Auto-submitting remaining questions...")
            st.session_state.i = len(qids)  # Jump to end of session
            st.rerun()
        
        # Display timer header with refresh button
        timer_col1, timer_col2, timer_col3, timer_col4, timer_col5 = st.columns([2, 2, 1, 1, 0.8])
        
        with timer_col1:
            time_str = format_time_remaining(remaining_seconds)
            st.metric("⏰ Time Remaining", time_str)
        
        with timer_col2:
            pace_info = compute_pace(elapsed_seconds, st.session_state.i, 
                                   st.session_state.session_time_ideal_pace or 120)
            pace_status = pace_info["pace_status"]
            if pace_status == "on_pace":
                st.metric("Pace", "🟢 On pace")
            elif pace_status == "ahead":
                ahead_min = abs(pace_info["ahead_or_behind_seconds"]) // 60
                st.metric("Pace", f"🟢 Ahead {ahead_min}m")
            else:
                behind_min = abs(pace_info["ahead_or_behind_seconds"]) // 60
                st.metric("Pace", f"🟡 Behind {behind_min}m")
        
        with timer_col3:
            st.metric("Answered", f"{st.session_state.i}/{len(qids)}")
        
        with timer_col4:
            mode_label = "Exam" if session_mode == "exam_mode" else "Drill"
            st.metric("Mode", mode_label)
        
        with timer_col5:
            if st.button("🔄", help="Refresh timer", key="timer_refresh"):
                st.rerun()
        
        # Warning if <5 minutes
        if remaining_seconds < 300 and remaining_seconds > 0:
            st.warning(f"⏰ **HURRY UP!** Only {format_time_remaining(remaining_seconds)} left!")

    # Stage 1: Answer
    if st.session_state.step == "answer":
        # Initialize timer for this question if not already started
        if st.session_state.session_current_q_start_time is None:
            st.session_state.session_current_q_start_time = datetime.now()
        
        with question_box:
            header = f"Question {st.session_state.i + 1} of {len(qids)}"
            if has_notebook(current_qid, nbs_df):
                header += " 📓"
            if is_flashcard(current_qid, fc_df):
                header += " 🃏"
            st.subheader(header)
            
            meta_line = f"{q.get('Topic','')} → {q.get('Subtopic','')} | {q.get('Difficulty','')}"
            if show_qid:
                meta_line = f"QID {current_qid} | " + meta_line
            if has_notebook(current_qid, nbs_df):
                nb_url = get_notebook_url(current_qid, nbs_df)
                if nb_url:
                    meta_line += f" | [📓 Notebook]({nb_url})"
                else:
                    meta_line += " | 📓 Notebook"
            if is_flashcard(current_qid, fc_df):
                meta_line += " | 🃏 Quizlet"
            st.caption(meta_line)

            st.markdown(q.get("Question", "").replace("\n", "  \n"))

            options = q.get("Options", {})
            if not options:
                st.error("This question has no answer options (A–F).")
                if st.button("Skip"):
                    current_qid = st.session_state.review.get("qid") if st.session_state.review else None
                    current_session_mode = st.session_state.get("session_mode", "study")
                    if current_session_mode in ["exam_mode", "speed_drill"] and current_qid and current_qid not in st.session_state.session_skipped_qids:
                        st.session_state.session_skipped_qids.append(current_qid)
                    st.session_state.i += 1
                    st.session_state.step = "answer"
                    st.session_state.review = None
                    st.session_state.session_current_q_start_time = None  # Reset timer for next question
                    st.rerun()
                st.stop()

            with st.form(key=f"answer_form_{current_qid}", clear_on_submit=False):
                choice = st.radio(
                    "Choose an answer:",
                    list(options.keys()),
                    format_func=lambda x: f"{x}: {options[x]}"
                )
                
                # Flag for review checkbox (only in timed modes)
                is_timed = session_mode in ["exam_mode", "speed_drill"]
                flag_for_review = False
                if is_timed:
                    st.markdown("---")
                    flag_for_review = st.checkbox("🚩 Flag for review (skip answer & move to next)", key=f"flag_{current_qid}")
                
                # Button behavior depends on flag checkbox
                if is_timed and flag_for_review:
                    # When flagging: only show the flag button
                    submitted = False
                    skip_submitted = st.form_submit_button("✅ Submit & Flag → Next (skip review)", use_container_width=True)
                else:
                    # Normal mode: show review button + Skip button
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        submitted = st.form_submit_button("Submit & Review", use_container_width=True)
                    with btn_col2:
                        skip_clicked = st.form_submit_button("⏭️ Skip", use_container_width=True)
                    skip_submitted = False

            # Handle skip button (new)
            if 'skip_clicked' in locals() and skip_clicked and not submitted:
                # Track skipped question for reanswering
                current_session_mode = st.session_state.get("session_mode", "study")
                if current_qid and current_session_mode in ["exam_mode", "speed_drill"] and current_qid not in st.session_state.session_skipped_qids:
                    st.session_state.session_skipped_qids.append(current_qid)
                
                st.session_state.i += 1
                st.session_state.step = "answer"
                st.session_state.review = None
                st.session_state.session_current_q_start_time = None  # Reset timer for next question
                st.rerun()

            # Handle flagged submission (when flag button is clicked)
            if is_timed and flag_for_review and skip_submitted and not submitted:
                # Track flag and auto-skip
                if st.session_state.session_id:
                    save_flagged_attempt(current_qid, st.session_state.session_id)
                
                # Mark as flagged in session state
                if current_qid not in st.session_state.session_flagged_qids:
                    st.session_state.session_flagged_qids.append(current_qid)
                
                # Record attempt with time (but mark as flagged, don't evaluate)
                if is_timed and st.session_state.session_time_started:
                    elapsed = int((datetime.now() - st.session_state.session_time_started).total_seconds())
                    time_on_q = elapsed - sum(st.session_state.session_question_times.get(qid, 0) for qid in st.session_state.session_question_times)
                else:
                    time_on_q = 0
                
                # Record as "flagged" (don't evaluate correctness yet)
                record_attempt(current_qid, "FLAGGED", False, time_spent=time_on_q)
                
                st.session_state.i += 1
                st.session_state.step = "answer"
                st.session_state.review = None
                st.session_state.session_current_q_start_time = None  # Reset timer for next question
                st.rerun()

            if submitted:
                try:
                    correct_letter = q.get("CorrectLetter")
                    # Handle multiple correct answers (comma-separated, e.g., "A,E")
                    correct_letters = [x.strip() for x in str(correct_letter).split(',') if x.strip()]
                    is_correct = choice in correct_letters
                    
                    # Calculate time spent on this question (with safety check)
                    if st.session_state.session_current_q_start_time is None:
                        st.session_state.session_current_q_start_time = datetime.now()
                    time_on_q_sec = int((datetime.now() - st.session_state.session_current_q_start_time).total_seconds())
                    
                    # Warn if answered too quickly (only in timed modes, not study/deep dive)
                    session_mode = st.session_state.get("session_mode", "study")
                    if session_mode in ["exam_mode", "speed_drill"] and time_on_q_sec < 15:
                        st.warning(f"⚡ **You answered in {time_on_q_sec}s!** Take your time to read carefully. Aim for 30+ seconds.", icon="🚨")
                        st.caption("You can click the Submit button again when you're ready, or change your answer.")
                        # Don't proceed yet - let them re-read
                        st.stop()

                    # Use correct per-question time (same calculation for all modes)
                    time_on_q = time_on_q_sec
                    
                    # Track time in session for timed modes
                    if is_timed:
                        st.session_state.session_question_times[current_qid] = time_on_q

                    record_attempt(current_qid, choice, is_correct, time_spent=time_on_q)

                    st.session_state.review = {
                        "qid": current_qid,
                        "choice": choice,
                        "is_correct": is_correct,
                        "correct_letter": correct_letter,
                        "explanation": q.get("Explanation", "(No explanation provided.)"),
                        "verification_notes": q.get("VerificationNotes", None),
                        "topic": q.get("Topic", ""),
                        "subtopic": q.get("Subtopic", ""),
                        "difficulty": q.get("Difficulty", ""),
                        "question": q.get("Question", ""),
                        "options": options,
                        "time_spent": time_on_q,
                    }
                    st.session_state.step = "review"
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error recording answer: {str(e)}")
                    import traceback
                    st.error(traceback.format_exc())

        with review_box:
            st.info("After you submit, feedback and explanation will appear here.")

    # Stage 2: Review
    else:
        rv = st.session_state.review
        if not rv:
            st.session_state.step = "answer"
            st.rerun()

        with question_box:
            header = f"Question {st.session_state.i + 1} of {len(qids)} (Review)"
            if has_notebook(rv.get('qid'), nbs_df):
                header += " 📓"
            if is_flashcard(rv.get('qid'), fc_df):
                header += " 🃏"
            st.subheader(header)
            meta_line = f"{rv.get('topic','')} → {rv.get('subtopic','')} | {rv.get('difficulty','')}"
            if show_qid:
                meta_line = f"QID {rv.get('qid')} | " + meta_line
            if has_notebook(rv.get('qid'), nbs_df):
                nb_url = get_notebook_url(rv.get('qid'), nbs_df)
                if nb_url:
                    meta_line += f" | [📓 Notebook]({nb_url})"
                else:
                    meta_line += " | 📓 Notebook"
            if is_flashcard(rv.get('qid'), fc_df):
                meta_line += " | 🃏 Quizlet"
            st.caption(meta_line)

            st.markdown(rv.get("question", "").replace("\n", "  \n"))

            st.markdown("**Your selection:** " + str(rv.get("choice")))
            st.markdown("**Options:**")
            for k, v in rv.get("options", {}).items():
                prefix = "👉 " if k == rv.get("choice") else "• "
                st.markdown(f"{prefix}{k}: {v}")

        with review_box:
            if rv.get("is_correct"):
                st.success("✅ Correct!")
            else:
                correct_letter = rv.get('correct_letter', '')
                # Format multiple correct answers nicely (e.g., "A,E" → "A or E")
                correct_letters = [x.strip() for x in str(correct_letter).split(',') if x.strip()]
                if len(correct_letters) > 1:
                    formatted_correct = " or ".join(correct_letters)
                else:
                    formatted_correct = correct_letter
                st.error(f"❌ Incorrect — correct answer is **{formatted_correct}**")
            
            # Show indicator for multi-answer questions
            correct_letter = rv.get('correct_letter', '')
            correct_letters = [x.strip() for x in str(correct_letter).split(',') if x.strip()]
            if len(correct_letters) > 1:
                st.info(f"ℹ️ **This question has {len(correct_letters)} correct answers:** {', '.join(correct_letters)}")

            st.markdown("### Explanation")
            st.markdown(rv.get("explanation", "").replace("\n", "  \n"))

            ver_notes = rv.get("verification_notes")
            if pd.notna(ver_notes):
                st.markdown("### Verification Notes")
                st.markdown(ver_notes)

            # Personal notes
            existing_note = get_note_for_qid(rv.get("qid"), load_notes())
            if existing_note:
                st.markdown("### 📝 Your Note")
                note_display = existing_note.replace('\n', '  \n')  # Markdown line breaks
                st.info(note_display)

            note_text = st.text_area(
                "Add a personal note (e.g. why you missed it, what to remember):",
                value="",
                key=f"note_{rv.get('qid')}",
                placeholder="e.g. Confused MERGE with COPY INTO syntax...",
            )
            if st.button("Save note", key=f"save_note_{rv.get('qid')}"):
                if note_text.strip():
                    save_note(rv.get("qid"), note_text.strip())
                    st.success("Note saved!")
                    st.rerun()

            # Flashcard (Quizlet) toggle
            st.markdown("---")
            rv_qid = rv.get("qid")
            if is_flashcard(rv_qid, fc_df):
                existing_fc = fc_df[fc_df["QID"] == int(rv_qid)].iloc[-1]
                st.info(f"🃏 Quizlet flashcard — *{existing_fc['front']}*")
                if st.button("Remove from Quizlet", key=f"rm_fc_{rv_qid}"):
                    remove_flashcard(rv_qid)
                    st.success("Removed from flashcards.")
                    st.rerun()
            else:
                fc_front = st.text_input(
                    "🃏 Flashcard front (your recall prompt):",
                    key=f"fc_front_{rv_qid}",
                    placeholder="e.g. Trigger to process all available data in multiple batches?",
                )
                if st.button("🃏 Save Quizlet flashcard", key=f"add_fc_{rv_qid}"):
                    correct_letter = rv.get("correct_letter", "")
                    opts = rv.get("options", {})
                    back_text = f"{correct_letter}: {opts.get(correct_letter, '')}"
                    front_text = fc_front.strip() if fc_front.strip() else rv.get("question", "")
                    save_flashcard(rv_qid, front_text, back_text)
                    st.success("Saved flashcard! 🃏")
                    st.rerun()

            # Notebook link toggle
            st.markdown("---")
            if has_notebook(rv_qid, nbs_df):
                nb_url = get_notebook_url(rv_qid, nbs_df)
                if nb_url:
                    st.markdown(f"📓 [Open Databricks notebook]({nb_url})")
                else:
                    st.info("📓 Databricks notebook linked (no URL)")
                if st.button("Remove notebook link", key=f"rm_nb_{rv_qid}"):
                    remove_notebook_link(rv_qid)
                    st.rerun()
            else:
                nb_url_input = st.text_input(
                    "Databricks notebook URL:",
                    key=f"nb_url_{rv_qid}",
                    placeholder="https://adb-xxxx.azuredatabricks.net/...",
                )
                if st.button("📓 Link Databricks notebook", key=f"add_nb_{rv_qid}"):
                    save_notebook_link(rv_qid, nb_url_input.strip())
                    st.success("Notebook linked!")
                    st.rerun()

            c1, c2, c3, c4 = st.columns(4)
            with c1:
                if st.button("Next question"):
                    st.session_state.i += 1
                    st.session_state.step = "answer"
                    st.session_state.review = None
                    st.session_state.session_current_q_start_time = None  # Reset timer for next question
                    st.rerun()
            with c2:
                if st.button("Skip"):
                    current_qid = st.session_state.review.get("qid")
                    # For timed modes, track skipped questions to reanswer at end
                    current_session_mode = st.session_state.get("session_mode", "study")
                    if current_qid and current_session_mode in ["exam_mode", "speed_drill"] and current_qid not in st.session_state.session_skipped_qids:
                        st.session_state.session_skipped_qids.append(current_qid)
                    st.session_state.i += 1
                    st.session_state.step = "answer"
                    st.session_state.review = None
                    st.session_state.session_current_q_start_time = None  # Reset timer for next question
                    st.rerun()
            with c3:
                # For flagged review mode, show "Done reviewing" button
                if st.session_state.get("review_mode") == "flagged_only":
                    if st.button("✅ Done reviewing", key="done_flagged_review"):
                        st.session_state.review_mode = None
                        st.session_state.i = len(st.session_state.session_qids)  # Jump to end of session
                        st.rerun()
                else:
                    if st.button("Clear focus"):
                        st.session_state.focus_type = None
                        st.session_state.focus_topic = None
                        st.session_state.focus_subtopic = None
                        reset_study_session()
                        st.rerun()
            with c4:
                if st.button("Go to Dashboard"):
                    st.session_state.nav_request = "Weakness Dashboard"
                    st.rerun()



except Exception as e:
    st.error("❌ App crashed. Here’s the error:")
    st.exception(e)
    st.code(traceback.format_exc())
