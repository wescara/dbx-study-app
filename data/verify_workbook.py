import pandas as pd

df = pd.read_excel('Custom_Questions_All_Test.xlsx')
print(f'Total questions: {len(df)}')
print(f'QID range: {df["QID"].min()} to {df["QID"].max()}')
print(f'All VerificationStatus set to Confirmed: {(df["VerificationStatus"] == "Confirmed").all()}')
print(f'\nSample question:')
row = df.iloc[0]
print(f'  QID: {row["QID"]}')
print(f'  Question: {row["Question"][:80]}...')
print(f'  Answer: {row["CorrectLetter"]}')
print(f'  Options: A={row["A"][:30]}..., B={row["B"][:30]}...')
