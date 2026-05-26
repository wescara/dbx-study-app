import app
import pandas as pd

questions = app.load_questions(r'C:\dbx-study-app\data\DBx_Questions.xlsx')
attempts = app.load_attempts()

stats = app.add_performance(questions, attempts)
stats = app.compute_priority(stats)

previously_missed = stats[stats['previously_missed']]
print(f'✓ Previously missed (1 incorrect): {len(previously_missed)}')
print(f'\nTop 10 previously-missed questions by priority:')
print(previously_missed[['QID', 'Topic', 'incorrect_count', 'priority', 'accuracy']].sort_values('priority', ascending=False).head(10))

print(f'\n✓ Sample with missed_boost column:')
print(stats[stats['previously_missed']][['QID', 'missed_boost', 'priority']].head(5))
