import pandas as pd

# Load data
df = pd.read_excel('data/DBx_Questions.xlsx', sheet_name='QuestionBank')
att = pd.read_csv('data/attempts.csv')

att['timestamp'] = pd.to_datetime(att['timestamp'], format='ISO8601', errors='coerce')
att = att.sort_values('timestamp')

# Weighted accuracy per QID
def weighted_acc(group):
    n = len(group)
    weights = [0.5**i for i in range(n-1, -1, -1)]
    correct = group['correct'].values
    return sum(w * c for w, c in zip(weights, correct)) / sum(weights)

qid_wacc = att.groupby('QID').apply(weighted_acc).to_dict()

# Filter M/H with <60%
mh = df[df['Difficulty'].isin(['Medium','Hard'])].copy()
mh['wacc'] = mh['QID'].map(qid_wacc)
mh = mh[mh['wacc'].notna()]
hr = mh[mh['wacc'] < 0.60].copy()

# Stats
last_result = att.groupby('QID')['correct'].last().to_dict()
attempt_counts = att.groupby('QID').size().to_dict()
hr['attempts'] = hr['QID'].map(attempt_counts)
hr['last_correct'] = hr['QID'].map(last_result)
hr['wacc_pct'] = (hr['wacc'] * 100).round(1)

# Old 20
old_20 = {1280,1546,1859,1858,1918,1829,1956,1904,1811,1634,1178,1244,1715,1740,1775,1773,1744,1779,1359,1438}
hr['on_old_list'] = hr['QID'].isin(old_20)
hr = hr.sort_values('wacc')

print(f"Total high-risk: {len(hr)}")
print(f"Still on old list: {hr['on_old_list'].sum()}")
new_ones = hr[~hr['on_old_list']]
print(f"NEW since last time: {len(new_ones)}")
print()

for _, r in hr[['QID','Topic','Subtopic','Difficulty','wacc_pct','attempts','last_correct','on_old_list']].iterrows():
    flag = 'OLD' if r['on_old_list'] else 'NEW'
    last = 'Y' if r['last_correct'] else 'N'
    print(f"[{flag}] QID {r['QID']:>4} | {r['wacc_pct']:>5}% | {r['attempts']:>2} att | last:{last} | {r['Difficulty']:>6} | {r['Topic']} > {r['Subtopic']}")

# Export to Excel
export = hr[['QID','Topic','Subtopic','Difficulty','wacc_pct','attempts','last_correct','on_old_list']].copy()
export.columns = ['QID','Topic','Subtopic','Difficulty','Weighted Acc %','Attempts','Last Correct','On Old List']
export['Status'] = ''
export.to_excel('data/high_risk_study_list.xlsx', index=False, sheet_name='High-Risk')
print(f"\nExported to data/high_risk_study_list.xlsx")
