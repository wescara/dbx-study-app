import pandas as pd

attempts = pd.read_csv(r'data/attempts.csv')
new_qs = attempts[attempts['QID'].isin(range(2090, 2135))]

if len(new_qs) > 0:
    print(f'Total attempts on Q2090-2134: {len(new_qs)}')
    print(f'Correct: {int(new_qs["correct"].sum())}')
    print(f'Incorrect: {len(new_qs) - int(new_qs["correct"].sum())}')
    accuracy = new_qs['correct'].sum() / len(new_qs) * 100
    print(f'Accuracy: {accuracy:.1f}%')
    print()
    
    # Group by QID
    qid_stats = new_qs.groupby('QID').agg({
        'correct': ['count', 'sum']
    }).round(2)
    qid_stats.columns = ['attempts', 'correct']
    qid_stats['accuracy'] = (qid_stats['correct'] / qid_stats['attempts'] * 100).round(1)
    print(qid_stats.to_string())
else:
    print('No attempts yet on questions 2090-2134')
