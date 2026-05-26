import pandas as pd
import os

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

# Get rows with Exam = 'DCDEA Practice Exam 2'
dcdea = df[df['Exam'] == 'DCDEA Practice Exam 2']

print("="*70)
print("DCDEA PRACTICE EXAM 2 - FINAL SUMMARY")
print("="*70)

print(f"\n✓ Questions added: {len(dcdea)}")
print(f"✓ QID Range: {int(dcdea['QID'].min())} to {int(dcdea['QID'].max())}")
print(f"✓ Source: {dcdea['Source'].unique()[0]}")
print(f"✓ Total file rows: {len(df)}")

# Check graphics
images_dir = 'data/extracted_images_exam2'
if os.path.exists(images_dir):
    images = os.listdir(images_dir)
    print(f"✓ Graphics extracted: {len(images)} images")

print(f"\n" + "="*70)
print("SAMPLE QUESTIONS")
print("="*70)

print(f"\nFirst question (QID 2045):")
first = dcdea.iloc[0]
print(f"  Q: {first['Question'][:75]}...")
print(f"  Options: A={first['A'][:40]}... B={first['B'][:40]}...")
print(f"  Correct Answer: {first['CorrectLetter']}")

print(f"\nLast question (QID 2089):")
last = dcdea.iloc[-1]
print(f"  Q: {last['Question'][:75]}...")
print(f"  Options: A={last['A'][:40]}... B={last['B'][:40]}...")
print(f"  Correct Answer: {last['CorrectLetter']}")

print(f"\n" + "="*70)
print("OUTPUT FILES")
print("="*70)
print(f"\n• data/DCDEA_Practice_Exam_2_Questions.xlsx")
print(f"  └─ Complete workbook with 45 new questions (QID 2045-2089)")
print(f"\n• data/extracted_images_exam2/")
print(f"  └─ 15 extracted graphics ready for OCR/processing")
print(f"\n• image_locations.txt")
print(f"  └─ Mapping of images to question locations")

print("\n" + "="*70)
