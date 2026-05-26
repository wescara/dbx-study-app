import pandas as pd

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

# Data corrections for the 6 problem questions
corrections = {
    2046: {  # Q2
        'CorrectLetter': 'B',
    },
    2050: {  # Q6
        'CorrectLetter': 'B',
        'A': 'Based on the Databricks architecture and the logs provided, which statement best explains this failure?',
        'B': 'The Data Plane executes the query; failure is due to the Databricks worker subnet lacking outbound network permissions.',
        'C': 'The Data Plane executes the query; failure is due to insufficient cloud resources allocated to the cluster.',
        'D': 'The Control Plane executes the query; failure is due to the Unity Catalog metadata store being unavailable.',
        'E': 'The Control Plane executes the query; failure is due to a bug in the Databricks Spark runtime optimizer.',
    },
    2054: {  # Q10
        'CorrectLetter': 'A,B',
        'A': 'Which two scenarios are the strongest candidates for Lakeflow Connect?',
        'B': 'Ingesting from a supported SaaS or database source using a managed connector.',
        'C': 'Ingesting supported external data sources when the team wants a Databricks-native, fully-governed solution.',
        'D': 'Reading a small CSV file once with a simple SQL command.',
        'E': 'Querying an external MySQL or PostgreSQL database directly from Databricks without ingesting it.',
    },
    2064: {  # Q20
        'CorrectLetter': 'D',
    },
    2066: {  # Q22
        'CorrectLetter': 'B',
        'A': 'The pipeline includes this Python definition:',
        'B': 'When the pipeline is deployed and executed, what kind of object does the variable `view` represent?',
        'C': 'A temporary Spark session view created only for the current notebook session.',
        'D': 'A temporary pipeline view whose results are computed when queried and cached for future use.',
        'E': 'A continuously updating streaming view.',
    },
    2079: {  # Q35
        'CorrectLetter': 'C',
        'A': 'In which scenario should the data engineer choose Auto Loader over the COPY INTO command?',
        'B': 'When performing a one-time historical backfill with a stable schema.',
        'C': 'When loading a small, static set of files from cloud storage using a simple SQL command.',
        'D': 'When the source schema is expected to evolve over time and the pipeline needs to adapt automatically.',
        'E': 'When the environment cannot persist Structured Streaming checkpoints.',
    }
}

print("Updating Excel with missing data...\n")

for qid, data in corrections.items():
    row_idx = df[df['QID'] == qid].index[0]
    for col, val in data.items():
        df.loc[row_idx, col] = val
        print(f"QID {qid}: Updated {col} = {val[:50]}...")

# Save updated file
output_path = 'data/DCDEA_Practice_Exam_2_Questions.xlsx'
df.to_excel(output_path, index=False)

print(f"\n✓ Updated file saved")

# Verify
dcdea = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)]
missing = dcdea['CorrectLetter'].isna().sum()
print(f"\nQuestions with correct answers: {45 - missing}/45")
