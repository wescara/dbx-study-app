import pandas as pd

questions = pd.read_excel('data/DBx_Questions.xlsx', sheet_name='QuestionBank')
attempts = pd.read_csv('data/attempts.csv')
attempts['timestamp'] = pd.to_datetime(attempts['timestamp'], format='mixed')

now = pd.Timestamp.now()
att = attempts.copy()
att['days_ago'] = (now - att['timestamp']).dt.total_seconds() / 86400
att['weight'] = 0.5 ** (att['days_ago'] / 14)
att['weighted_correct'] = att['correct'].astype(float) * att['weight']

agg = att.groupby('QID').agg(
    attempts=('correct', 'count'),
    correct_total=('correct', 'sum'),
    weighted_correct=('weighted_correct', 'sum'),
    weighted_total=('weight', 'sum'),
).reset_index()
agg['accuracy'] = agg['weighted_correct'] / agg['weighted_total']

stats = questions.merge(agg, on='QID', how='left')
stats = stats.fillna({'attempts': 0, 'correct_total': 0, 'accuracy': 0.0, 'ExamWeight': 0.15})

# Confirmed only
if 'VerificationStatus' in stats.columns:
    stats = stats[stats['VerificationStatus'] == 'Confirmed'].copy()

# Get attempted
attempted = stats[stats['attempts'] > 0].copy()

# High-risk: Medium/Hard + <60% accuracy
hr = attempted[(attempted['Difficulty'].isin(['Medium', 'Hard'])) & (attempted['accuracy'] < 0.6)].copy()
hr = hr.sort_values(['accuracy', 'Difficulty'], ascending=[True, False])

print(f"Total High-Risk: {len(hr)}")
print()
print(f"{'QID':>4} | {'Diff':<6} | {'Acc%':>5} | {'Att':>3} | {'Topic':<30} | Subtopic")
print("-" * 100)
for _, r in hr.iterrows():
    qid = int(r['QID'])
    diff = r['Difficulty']
    acc = r['accuracy'] * 100
    att_count = int(r['attempts'])
    topic = str(r.get('Topic', ''))[:30]
    subtopic = str(r.get('Subtopic', ''))[:40]
    print(f"{qid:>4} | {diff:<6} | {acc:5.1f}% | {att_count:>3} | {topic:<30} | {subtopic}")
