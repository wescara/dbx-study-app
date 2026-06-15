import pandas as pd

qb = pd.read_excel(r'c:\dbx-study-app\data\DBx_Questions.xlsx','QuestionBank')
att = pd.read_csv(r'c:\dbx-study-app\data\attempts.csv')

# Compute stats
stats = att.groupby('QID').agg(
    attempts=('correct', 'count'),
    correct=('correct', 'sum')
).reset_index()
stats['accuracy'] = stats['correct'] / stats['attempts']

# Merge with questions
out = qb.merge(stats, on='QID', how='left')
out = out.fillna({'attempts': 0, 'correct': 0, 'accuracy': 0.0})

# Filter for attempted only
attempted = out[out['attempts'] > 0].copy()

print(f'Total attempted: {len(attempted)}')
print(f'Has VerificationStatus: {"VerificationStatus" in attempted.columns}')

if 'VerificationStatus' in attempted.columns:
    confirmed = attempted[attempted['VerificationStatus'] == 'Confirmed'].copy()
    print(f'Confirmed only: {len(confirmed)}')
    
    high_risk_all = attempted[(attempted['Difficulty'].isin(['Medium', 'Hard'])) & (attempted['accuracy'] < 0.6)]
    high_risk_confirmed = confirmed[(confirmed['Difficulty'].isin(['Medium', 'Hard'])) & (confirmed['accuracy'] < 0.6)]
    
    print(f'High-risk (all): {len(high_risk_all)}')
    print(f'High-risk (confirmed): {len(high_risk_confirmed)}')
    print(f'Difference: {len(high_risk_all) - len(high_risk_confirmed)}')
else:
    high_risk = attempted[(attempted['Difficulty'].isin(['Medium', 'Hard'])) & (attempted['accuracy'] < 0.6)]
    print(f'High-risk: {len(high_risk)}')
