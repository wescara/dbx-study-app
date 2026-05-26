import pandas as pd

questions = pd.read_excel(r'C:\dbx-study-app\data\DBx_Questions.xlsx', sheet_name='QuestionBank')

# Check previously_missed flag (IncorrectCount == 1)
previously_missed = questions[questions['IncorrectCount'] == 1]
print(f'✓ Previously missed (IncorrectCount == 1): {len(previously_missed)}')
print(f'\nSample questions:')
print(previously_missed[['QID', 'Topic', 'IncorrectCount', 'Difficulty']].head(10))
