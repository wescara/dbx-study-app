import pandas as pd

df = pd.read_excel('c:\\dbx-study-app\\data\\DCDEA_Practice_Exam_2_NEW_QUESTIONS.xlsx')

# Keywords for the 5 heavily tested topics
heavy_topics = {
    'Auto Loader': ['auto loader', 'autoloader', 'directory listing', 'file notification', 'schema evolution', 'mergeschema', '50,000', 'ingestion method'],
    'Lazy Evaluation': ['lazy', 'transformation', 'action', 'cache', 'persist', 'collect', 'show', 'nothing happens'],
    'Lakeflow/DLT': ['lakeflow', 'delta live', 'dlt', 'expectation', 'streaming table', 'materialized view', '@dlt', 'quality', 'expect'],
    'Unity Catalog Permissions': ['grant', 'permission', 'access', 'privilege', 'acl', 'unity catalog', 'role', 'user', 'schema', 'table', 'owner'],
    'MERGE INTO': ['merge', 'upsert', 'matched', 'deduplication', 'slowly changing', 'scd', 'when matched', 'when not matched', 'insert', 'update', 'delete']
}

light_topics = {
    'Cluster Configuration': ['cluster', 'config', 'node', 'autoscale', 'worker', 'driver', 'instance type'],
    'Architecture/Control Plane': ['control plane', 'data plane', 'architecture', 'workspace', 'metastore'],
    'Delta Sharing': ['delta sharing', 'share', 'recipient', 'shareable object'],
    'Spark Internals': ['shuffle', 'stage', 'task', 'executor', 'partition', 'wide transformation']
}

# Count questions
def count_topic_matches(df, topic_dict):
    results = {}
    for topic, keywords in topic_dict.items():
        matches = []
        for idx, row in df.iterrows():
            question = str(row['Question']).lower()
            options = str(row['A']).lower() + ' ' + str(row['B']).lower() + ' ' + str(row['C']).lower() + ' ' + str(row['D']).lower()
            explanation = str(row['Explanation']).lower() if pd.notna(row['Explanation']) else ''
            
            combined_text = question + ' ' + options + ' ' + explanation
            
            if any(kw in combined_text for kw in keywords):
                matches.append(row['Number'])
        
        results[topic] = matches
    return results

print("=" * 80)
print("HEAVILY TESTED TOPICS (per exam review feedback)")
print("=" * 80)
heavy_matches = count_topic_matches(df, heavy_topics)
for topic, q_nums in sorted(heavy_matches.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{topic}: {len(q_nums)} questions")
    if q_nums:
        print(f"  Questions: {', '.join(map(str, sorted(q_nums)))}")
    else:
        print("  ⚠️  NO QUESTIONS FOUND")

print("\n" + "=" * 80)
print("LIGHTLY TESTED TOPICS (per exam review feedback)")
print("=" * 80)
light_matches = count_topic_matches(df, light_topics)
for topic, q_nums in sorted(light_matches.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{topic}: {len(q_nums)} questions")
    if q_nums:
        print(f"  Questions: {', '.join(map(str, sorted(q_nums)))}")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
heavy_total = sum(len(v) for v in heavy_matches.values())
light_total = sum(len(v) for v in light_matches.values())
print(f"Total heavy-topic questions: {heavy_total}/{len(df)}")
print(f"Total light-topic questions: {light_total}/{len(df)}")
print(f"Coverage: {(heavy_total/len(df)*100):.1f}% on heavily tested topics")
print(f"          {(light_total/len(df)*100):.1f}% on lightly tested topics")
