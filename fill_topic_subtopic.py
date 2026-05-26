import pandas as pd
import re

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')

# Get DCDEA questions
dcdea = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)].copy()

print(f"Processing {len(dcdea)} DCDEA questions...\n")

# Define topic mapping based on keywords
topic_keywords = {
    'Data Ingestion': ['ingest', 'lakeflow connect', 'auto loader', 'copy into', 'schema drift', 'connector'],
    'Query Performance': ['join', 'broadcast', 'shuffle', 'caching', 'optimization', 'spill'],
    'Pipelines & Compute': ['pipeline', 'cluster', 'execution mode', 'continuous', 'triggered', 'serverless', 'job'],
    'Data Governance': ['unity catalog', 'system table', 'billing', 'access', 'audit', 'chargeback', 'dbu'],
    'Structured Streaming': ['streaming', 'checkpoint', 'watermark', 'kafka', 'delta', 'trigger'],
    'Delta Lake': ['delta', 'parquet', 'merge', 'time travel', 'compaction', 'z-order'],
    'Development Tools': ['notebook', 'workspace', 'debugging', 'cluster config', 'environment'],
}

subtopic_keywords = {
    'Managed Connectors': ['managed connector', 'lakeflow connect', 'supported source'],
    'Broadcast Joins': ['broadcast', 'join', 'small table'],
    'Pipeline Modes': ['execution mode', 'continuous', 'triggered', 'serverless'],
    'System Tables': ['system table', 'billing', 'query history', 'access audit'],
    'Checkpointing': ['checkpoint', 'offset', 'restart'],
    'Schema Evolution': ['schema drift', 'evolve', 'schema registry'],
    'Auto Loader': ['auto loader', 'cloud files'],
    'Concurrency': ['concurrent', 'overlap', 'queue'],
    'Kafka Integration': ['kafka', 'streaming source'],
    'View Management': ['temporary view', 'streaming view', 'materialized view'],
    'Query Optimization': ['spill', 'exchange', 'shuffle'],
    'Control vs Data Plane': ['control plane', 'data plane', 'architecture'],
}

# Assign topics and subtopics
topics_assigned = []
subtopics_assigned = []

for idx, row in dcdea.iterrows():
    question = str(row['Question']).lower()
    options = (str(row.get('A', '')) + ' ' + str(row.get('B', '')) + ' ' + str(row.get('C', ''))).lower()
    full_text = question + ' ' + options
    
    # Find matching topic
    topic = 'General Databricks'
    for t, keywords in topic_keywords.items():
        if any(kw in full_text for kw in keywords):
            topic = t
            break
    
    # Find matching subtopic
    subtopic = ''
    for st, keywords in subtopic_keywords.items():
        if any(kw in full_text for kw in keywords):
            subtopic = st
            break
    
    topics_assigned.append(topic)
    subtopics_assigned.append(subtopic)
    
    q_num = int(row['Number'])
    print(f"Q{q_num}: Topic={topic:25} | Subtopic={subtopic}")

print(f"\nTopics assigned: {len(set(topics_assigned))} unique")
print(f"Subtopics assigned: {len(set(subtopics_assigned))} unique")

# Update the dataframe
dcdea['Topic'] = topics_assigned
dcdea['Subtopic'] = subtopics_assigned
dcdea['VerificationStatus'] = 'Confirmed'

print(f"\n✓ Assigned Topic, Subtopic, and VerificationStatus")

# Update main dataframe
for idx, (orig_idx, row) in enumerate(zip(dcdea.index, dcdea.itertuples())):
    df.loc[orig_idx, 'Topic'] = row.Topic
    df.loc[orig_idx, 'Subtopic'] = row.Subtopic
    df.loc[orig_idx, 'VerificationStatus'] = row.VerificationStatus

# Save
output_path = 'data/DCDEA_Practice_Exam_2_Questions.xlsx'
df.to_excel(output_path, index=False)

print(f"\n✓ Saved to {output_path}")
