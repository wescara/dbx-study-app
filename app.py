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
def load_questions(xlsx_path: str, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
    excluded = load_excluded_qids()
    if excluded:
        df = df[~df["QID"].isin(excluded)]
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
    # ROI-ish: low accuracy + harder + flagged-for-review + staleness boost
    work["priority"] = (1 - work["accuracy"]) * 2 + work["diff_w"] + work["flag_w"] + work["stale_w"]
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
    if use_random:
        # For timed modes: randomly select questions
        import numpy as np
        work = stats.sample(n=min(int(n), len(stats)), random_state=None).reset_index(drop=True)
    else:
        # For study mode: sort by priority (low accuracy, flagged, harder, stale)
        work = stats.sort_values("priority", ascending=False).head(int(n)).reset_index(drop=True)
    
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
            "Explanation": r.get("Explanation", ""),
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
# Navigation (fixes StreamlitAPIException)
# =============================
if "nav_mode" not in st.session_state:
    st.session_state.nav_mode = "Study Mode"

# Apply nav_request BEFORE widget instantiation
if st.session_state.get("nav_request"):
    st.session_state.nav_mode = st.session_state.nav_request
    st.session_state.nav_request = None

# =============================
# Streamlit UI
# =============================
st.set_page_config(page_title="Databricks Associate Engineer Study App", layout="wide")
st.title("Databricks Associate Engineer Study App")

# Sidebar navigation (do not mutate nav_mode after this widget exists)
mode = st.sidebar.radio("Mode", ["Study Mode", "Weakness Dashboard"], key="nav_mode")

st.sidebar.markdown("### Settings")
confirmed_only = st.sidebar.checkbox("Confirmed only (recommended)", value=True)
hide_mastered = st.sidebar.checkbox("Hide mastered (≥85% and ≥3 attempts)", value=True)
show_qid = st.sidebar.checkbox("Show key (QID)", value=True)
session_n = st.sidebar.number_input("Questions per session", min_value=5, max_value=50, value=15, step=5)
show_debug = st.sidebar.checkbox("Show debug tables", value=False)

st.sidebar.markdown("### Jump to QID")
jump_qid = st.sidebar.number_input("Enter QID:", min_value=0, value=0, step=1, key="jump_qid_input")
if st.sidebar.button("Go", key="jump_qid_btn") and jump_qid > 0:
    st.session_state.jump_to_qid = int(jump_qid)

with st.expander("Startup status", expanded=True):
    st.write("Working directory:", os.getcwd())
    st.write("Excel path:", DATA_PATH)
    st.write("Attempts path:", ATTEMPTS_PATH)

try:
    if not os.path.exists(DATA_PATH):
        st.error("❌ Excel file not found.")
        st.info(r"Expected: C:\dbx-study-app\data\DBx_Questions.xlsx")
        st.stop()

    questions = load_questions(DATA_PATH, SHEET_NAME)
    attempts = load_attempts()

    # Today's stats in sidebar
    if not attempts.empty:
        today = pd.Timestamp.now().normalize()
        today_attempts = attempts[attempts["timestamp"] >= today]
        today_count = len(today_attempts)
        today_correct = int(today_attempts["correct"].sum()) if today_count > 0 else 0
        today_missed = today_count - today_correct
        today_acc = f"{today_correct / today_count:.0%}" if today_count > 0 else "–"
        st.sidebar.markdown("### Today's Progress")
        st.sidebar.metric("Answered today", today_count)
        st.sidebar.metric("Missed today", today_missed)
        st.sidebar.metric("Today's accuracy", today_acc)
    else:
        st.sidebar.markdown("### Today's Progress")
        st.sidebar.caption("No attempts yet.")

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

        attempted = stats[stats["attempts"] > 0].copy()
        if attempted.empty:
            st.info("No attempts recorded yet. Switch to Study Mode and answer ~10–15 questions first.")
            st.stop()

        # Overall
        st.subheader("✅ Overall Progress")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Questions Attempted", attempted["QID"].nunique())
        with c2:
            st.metric("Overall Accuracy", f"{attempted['accuracy'].mean():.1%}")
        with c3:
            mastered_count = int(((attempted["accuracy"] >= 0.85) & (attempted["attempts"] >= 3)).sum())
            st.metric("Mastered (≥85% & ≥3)", mastered_count)
        with c4:
            risky = attempted[(attempted["Difficulty"].isin(["Medium", "Hard"])) & (attempted["accuracy"] < 0.6)]
            st.metric("High‑Risk (M/H & <60%)", len(risky))

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

        # Weakest Topics
        st.subheader("🔴 Weakest Topics")
        topic_weak = (
            attempted.groupby("Topic")
            .agg(questions=("QID", "count"), avg_accuracy=("accuracy", "mean"))
            .sort_values("avg_accuracy")
            .reset_index()
        )
        st.dataframe(topic_weak, width='stretch')

        # Weakest Subtopics
        st.subheader("🔴 Weakest Subtopics (Top 15)")
        subtopic_weak = (
            attempted.groupby(["Topic", "Subtopic"])
            .agg(questions=("QID", "count"), avg_accuracy=("accuracy", "mean"))
            .sort_values("avg_accuracy")
            .reset_index()
        )
        st.dataframe(subtopic_weak.head(15), width='stretch')

        # High-risk questions
        st.subheader("🔥 High‑Risk Questions (Medium/Hard + <60% accuracy)")
        high_risk = attempted[
            (attempted["Difficulty"].isin(["Medium", "Hard"])) &
            (attempted["accuracy"] < 0.6)
        ].copy().sort_values(["accuracy", "attempts"], ascending=[True, False])

        notes_df = load_notes()
        high_risk["Note"] = high_risk["QID"].apply(lambda x: get_note_for_qid(x, notes_df))
        cols = ["QID", "Topic", "Subtopic", "Difficulty", "attempts", "accuracy", "priority", "Note"]
        cols = [c for c in cols if c in high_risk.columns]
        st.dataframe(high_risk[cols].head(25), width='stretch')

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

        if show_debug:
            st.subheader("Debug: attempted sample")
            st.dataframe(attempted.head(50), width='stretch')

        st.stop()

    # =============================
    # Study Mode (Two-stage)
    # =============================
    st.header("🧠 Study Mode")

    # ===== MODE SELECTION =====
    st.subheader("Select your study mode:")
    mode_col1, mode_col2, mode_col3 = st.columns(3)
    
    with mode_col1:
        if st.button("🧠 Study Mode (Custom)", use_container_width=True, key="btn_study_mode"):
            reset_study_session()
            st.session_state.session_mode = "study"
            st.rerun()
    
    with mode_col2:
        if st.button("⚡ Speed Drill (15Q × 20min)", use_container_width=True, key="btn_speed_drill"):
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
        if st.button("📝 Exam Sim (45Q × 90min)", use_container_width=True, key="btn_exam_mode"):
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
    )

    if st.session_state.get("session_key") != session_key or not st.session_state.get("session_qids"):
        st.session_state.session_key = session_key
        st.session_state.session_attempts_start = len(attempts)
        # Use random selection for timed modes, priority-based for study mode
        use_random = current_session_mode in ["exam_mode", "speed_drill"]
        build_study_session(focused, num_questions, use_random=use_random)

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
                st.rerun()

            if submitted:
                correct_letter = q.get("CorrectLetter")
                is_correct = (choice == correct_letter)

                # Track time spent on this question (for timed modes)
                if is_timed and st.session_state.session_time_started:
                    elapsed = int((datetime.now() - st.session_state.session_time_started).total_seconds())
                    time_on_q = elapsed - sum(st.session_state.session_question_times.get(qid, 0) for qid in st.session_state.session_question_times)
                    st.session_state.session_question_times[current_qid] = time_on_q
                else:
                    time_on_q = 0

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
                st.error(f"❌ Incorrect — correct answer is **{rv.get('correct_letter')}**")

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
                st.info(existing_note)

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

    if show_debug:
        st.subheader("Debug: session qids")
        st.write(qids)

except Exception as e:
    st.error("❌ App crashed. Here’s the error:")
    st.exception(e)
    st.code(traceback.format_exc())
