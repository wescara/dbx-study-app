import pandas as pd

questions = pd.read_excel(r'C:\dbx-study-app\data\DBx_Questions.xlsx', sheet_name='QuestionBank', nrows=1)
print("Columns in QuestionBank:")
print(questions.columns.tolist())
