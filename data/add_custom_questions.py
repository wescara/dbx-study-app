import pandas as pd
from datetime import datetime
import openpyxl

# Read the existing QuestionBank to get the max QID
df_existing = pd.read_excel('DBx_Questions.xlsx', sheet_name='QuestionBank')
max_qid = df_existing['QID'].max()
start_qid = max_qid + 1

# Define the two new questions
questions = [
    {
        'Source': 'UD',
        'QID': start_qid,
        'Exam': 1,
        'Number': 768,  # Manual numbering
        'Topic': 'Development and Ingestion',
        'Subtopic': 'Repos - Git Operations',
        'Difficulty': 'Medium',
        'Question': 'In Databricks Repos, which of the following operations a data engineer can use to update the local version of a repo from its remote Git repository?',
        'A': 'Clone',
        'B': 'Commit',
        'C': 'Merge',
        'D': 'Push',
        'E': 'Pull',
        'F': None,
        'CorrectLetter': 'E',
        'Explanation': 'Pull is used to fetch and integrate changes from the remote repository into your local version. Clone creates a copy, Commit saves local changes, Merge combines branches, and Push uploads local changes.',
        'Notes': None,
        'LastReviewed': datetime.now().date(),
        'CorrectCount': 0,
        'IncorrectCount': 0,
        'FlagForReview': False,
        'Tags': 'Git, Repos',
        'Graphic': None,
        'Deeper Dive': None,
        'VerifiedAnswer': 'E',
        'VerificationStatus': 'Confirmed',
        'AnswerMatchesWorkbook': None,
        'VerificationNotes': 'Custom question added for practice',
        'VerificationSourceKeys': None,
        'VerifiedOn': None,
    },
    {
        'Source': 'UD',
        'QID': start_qid + 1,
        'Exam': 1,
        'Number': 769,  # Manual numbering
        'Topic': 'Databricks Intelligence Platform',
        'Subtopic': 'Lakehouse Architecture',
        'Difficulty': 'Medium',
        'Question': 'According to the Databricks Lakehouse architecture, which of the following is located in the customer\'s cloud account?',
        'A': 'Databricks web application',
        'B': 'Notebooks',
        'C': 'Repos',
        'D': 'Cluster virtual machines',
        'E': 'Workflows',
        'F': None,
        'CorrectLetter': 'D',
        'Explanation': 'Cluster virtual machines run in the customer\'s cloud account. The Databricks web application, Notebooks, Repos, and Workflows are managed by Databricks (they run on Databricks infrastructure).',
        'Notes': None,
        'LastReviewed': datetime.now().date(),
        'CorrectCount': 0,
        'IncorrectCount': 0,
        'FlagForReview': False,
        'Tags': 'Architecture, Lakehouse',
        'Graphic': None,
        'Deeper Dive': None,
        'VerifiedAnswer': 'D',
        'VerificationStatus': 'Confirmed',
        'AnswerMatchesWorkbook': None,
        'VerificationNotes': 'Custom question added for practice',
        'VerificationSourceKeys': None,
        'VerifiedOn': None,
    }
]

# Create a new DataFrame with the custom questions
df_new = pd.DataFrame(questions)

# Save to a new Excel workbook for testing
output_file = 'Custom_Questions_Test.xlsx'
df_new.to_excel(output_file, sheet_name='Custom Questions', index=False)

print(f"✓ Created test workbook: {output_file}")
print(f"✓ Added {len(questions)} questions")
print(f"✓ QIDs: {start_qid} to {start_qid + len(questions) - 1}")
print("\nQuestions added:")
for q in questions:
    print(f"  - QID {q['QID']}: {q['Topic']} > {q['Subtopic']}")
