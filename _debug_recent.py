import pandas as pd
df = pd.read_excel('data/DBx_Questions.xlsx', sheet_name='QuestionBank')
att = pd.read_csv('data/attempts.csv')
att['timestamp'] = pd.to_datetime(att['timestamp'], format='ISO8601', errors='coerce')
att = att.sort_values('timestamp')

def seq_acc(g):
    n = len(g)
    w = [0.5**i for i in range(n-1, -1, -1)]
    c = g['correct'].values
    return sum(wi*ci for wi, ci in zip(w, c)) / sum(w)

wacc = att.groupby('QID').apply(seq_acc).rename('accuracy')
agg = att.groupby('QID').agg(attempts=('correct','count')).reset_index()
agg = agg.merge(wacc, on='QID', how='left')
q = df.merge(agg, on='QID', how='left').fillna({'attempts': 0, 'accuracy': 0.0})

remaining = [1084, 1365, 1377, 1386, 1521, 1783, 1827, 1839, 1974, 2050]
for qid in remaining:
    row = q[q['QID'] == qid]
    if not row.empty:
        r = row.iloc[0]
        mastered = r['accuracy'] >= 0.85 and r['attempts'] >= 3
        print(f"QID {qid}: acc={r['accuracy']:.2f}, attempts={int(r['attempts'])}, mastered={mastered}")
