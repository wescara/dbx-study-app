import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
dcdea = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)]

print("✓ DCDEA Questions Updated Successfully\n")
print(f"Total questions: {len(dcdea)}")
print(f"QID range: {int(dcdea['QID'].min())} - {int(dcdea['QID'].max())}")
print(f"Source: {dcdea['Source'].unique()[0]}")
print(f"Exam: {int(dcdea['Exam'].unique()[0])}")

print(f"\nTopic/Subtopic/VerificationStatus Coverage:")
print(f"  Questions with Topic: {dcdea['Topic'].notna().sum()}/45")
print(f"  Questions with Subtopic: {dcdea['Subtopic'].notna().sum()}/45")
print(f"  Questions with VerificationStatus='Confirmed': {(dcdea['VerificationStatus'] == 'Confirmed').sum()}/45")

print(f"\nSample data:")
for idx in [0, 22, 44]:
    row = dcdea.iloc[idx]
    print(f"\n  Q{int(row['Number'])} (QID {int(row['QID'])}):")
    print(f"    Topic: {row['Topic']}")
    print(f"    Subtopic: {row['Subtopic']}")
    print(f"    VerificationStatus: {row['VerificationStatus']}")
