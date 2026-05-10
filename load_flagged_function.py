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
