import pandas as pd
import os

# Load the original master file to see existing topics
df_master = pd.read_excel('data/DBx_Questions.xlsx')

# Get unique topic/subtopic combinations
existing_topics = df_master[df_master['Topic'].notna()]['Topic'].unique()
existing_subtopics = df_master[df_master['Subtopic'].notna()]['Subtopic'].unique()

print("Existing Topics in Master List:")
for topic in sorted(set(existing_topics)):
    print(f"  • {topic}")

print(f"\nExisting Subtopics in Master List:")
for subtopic in sorted(set(existing_subtopics)):
    if pd.notna(subtopic) and subtopic.strip():
        print(f"  • {subtopic}")

# Now load DCDEA file
df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
dcdea = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)].copy()

print(f"\n\nAnalyzing {len(dcdea)} DCDEA questions...")

# Manual mapping based on question content to existing topics/subtopics
mappings = {
    2045: ('Data Ingestion and Loading', 'Lakeflow Connect'),
    2046: ('Data Processing & Transformations', 'Joins'),
    2047: ('Productionizing Pipelines', 'Lakeflow Spark Declarative Pipelines'),
    2048: ('Troubleshooting, Monitoring, and Optimization', 'Performance Tuning'),
    2049: ('Development and Ingestion', 'Understand notebook capabilities'),
    2050: ('Development and Ingestion', 'Lakehouse Architecture'),
    2051: ('Data Processing & Transformations', 'Spark SQL and PySpark'),
    2052: ('Data Ingestion and Loading', 'Auto Loader'),
    2053: ('Data Ingestion and Loading', 'Auto Loader'),
    2054: ('Data Ingestion and Loading', 'Lakeflow Connect'),
    2055: ('Productionizing Pipelines', 'Delta Live Tables'),
    2056: ('Development and Ingestion', 'Understand notebook capabilities'),
    2057: ('Governance and Security', 'ABAC'),
    2058: ('Troubleshooting, Monitoring, and Optimization', 'Optimize data layout and query performance'),
    2059: ('Development and Ingestion', 'Lakehouse Architecture'),
    2060: ('Data Processing & Transformations', 'Nested Data'),
    2061: ('Troubleshooting, Monitoring, and Optimization', 'Optimize data layout and query performance'),
    2062: ('Data Ingestion and Loading', 'Auto Loader'),
    2063: ('Observability and Optimization', 'Cost Management'),
    2064: ('Data Processing & Transformations', 'Joins'),
    2065: ('Productionizing Pipelines', 'Lakeflow Spark Declarative Pipelines'),
    2066: ('Productionizing Pipelines', 'Delta Live Tables'),
    2067: ('Data Processing & Transformations', 'Spark SQL and PySpark'),
    2068: ('Troubleshooting, Monitoring, and Optimization', 'Spark UI optimization'),
    2069: ('Productionizing Pipelines', 'Streaming and Real-Time Data'),
    2070: ('Data Ingestion and Loading', 'Structured Streaming'),
    2071: ('Data Ingestion and Loading', 'Structured Streaming'),
    2072: ('Data Processing & Transformations', 'Spark SQL and PySpark'),
    2073: ('Troubleshooting, Monitoring, and Optimization', 'Performance Tuning'),
    2074: ('Data Ingestion and Loading', 'Auto Loader'),
    2075: ('Data Processing & Transformations', 'Spark SQL and PySpark'),
    2076: ('Troubleshooting, Monitoring, and Optimization', 'Performance Tuning'),
    2077: ('Development and Ingestion', 'Understand notebook capabilities'),
    2078: ('Troubleshooting, Monitoring, and Optimization', 'Optimize data layout and query performance'),
    2079: ('Data Ingestion and Loading', 'Auto Loader'),
    2080: ('Productionizing Pipelines', 'Streaming and Real-Time Data'),
    2081: ('Data Ingestion and Loading', 'Structured Streaming'),
    2082: ('Troubleshooting, Monitoring, and Optimization', 'Performance Tuning'),
    2083: ('Development and Ingestion', 'Understand notebook capabilities'),
    2084: ('Data Processing & Transformations', 'Joins'),
    2085: ('Data Ingestion and Loading', 'Schema Enforcement and Evolution'),
    2086: ('Productionizing Pipelines', 'Delta Live Tables'),
    2087: ('Development and Ingestion', 'Select appropriate compute'),
    2088: ('Data Processing & Transformations', 'Joins'),
    2089: ('Productionizing Pipelines', 'Streaming and Real-Time Data'),
}

print("\nMapping DCDEA questions to existing topics/subtopics:\n")

for qid, (topic, subtopic) in mappings.items():
    if qid in df.index or any(df['QID'] == qid):
        row_idx = df[df['QID'] == qid].index[0] if len(df[df['QID'] == qid]) > 0 else None
        if row_idx is not None:
            df.loc[row_idx, 'Topic'] = topic
            df.loc[row_idx, 'Subtopic'] = subtopic
            df.loc[row_idx, 'VerificationStatus'] = 'Confirmed'
            q_num = int(df.loc[row_idx, 'Number'])
            print(f"Q{q_num} (QID {qid}): {topic:35} | {subtopic}")

# Save to temp file first, then replace
temp_path = 'data/DCDEA_Practice_Exam_2_Questions_UPDATED.xlsx'
output_path = 'data/DCDEA_Practice_Exam_2_Questions.xlsx'

df.to_excel(temp_path, index=False)

print(f"\n✓ Successfully updated all topics, subtopics, and VerificationStatus")
print(f"✓ Saved to {temp_path}")
print(f"\nNote: Please close the original Excel file, then rename:")
print(f"  FROM: {temp_path}")
print(f"  TO:   {output_path}")
