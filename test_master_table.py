import app
import pandas as pd

questions = app.load_questions(r'C:\dbx-study-app\data\DBx_Questions.xlsx')
attempts = app.load_attempts()

stats = app.add_performance(questions, attempts)
stats = app.compute_priority(stats)

# Check previously_missed flag
previously_missed = stats[stats['previously_missed']]
print(f'✓ Previously missed (IncorrectCount == 1): {len(previously_missed)}')
print(f'\nSample questions:')
print(previously_missed[['QID', 'Topic', 'IncorrectCount', 'priority', 'accuracy']].head(10))
