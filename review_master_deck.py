import pandas as pd

df = pd.read_excel('c:\\dbx-study-app\\data\\DBx_Questions.xlsx')

print("Total questions in master deck:", len(df))
print("\n" + "="*80)
print("ANALYZING COVERAGE: HEAVILY TESTED TOPICS (per exam feedback)")
print("="*80)

# Keywords for the 5 heavily tested topics
heavy_topics = {
    'Auto Loader': ['auto loader', 'autoloader', 'directory listing', 'file notification', 'schema evolution', 'mergeschema', 'rescued', 'ingest'],
    'Lazy Evaluation': ['lazy', 'transformation', 'action', 'cache', 'persist', 'collect', 'show', 'executed'],
    'Lakeflow/DLT': ['lakeflow', 'delta live', 'dlt', 'expectation', 'streaming table', 'materialized view', '@dlt', 'quality', 'expect'],
    'Unity Catalog Permissions': ['grant', 'permission', 'privilege', 'access', 'acl', 'role', 'ownership', 'princi'],
    'MERGE INTO': ['merge', 'upsert', 'matched', 'deduplication', 'slowly changing', 'scd', 'when matched', 'when not matched']
}

# Count questions
def count_topic_matches(df, topic_dict):
    results = {}
    for topic, keywords in topic_dict.items():
        matches = []
        for idx, row in df.iterrows():
            question = str(row['Question']).lower() if pd.notna(row['Question']) else ''
            options = ''
            for col in ['A', 'B', 'C', 'D', 'E', 'F']:
                if pd.notna(row[col]):
                    options += ' ' + str(row[col]).lower()
            explanation = str(row['Explanation']).lower() if pd.notna(row['Explanation']) else ''
            
            combined_text = question + ' ' + options + ' ' + explanation
            
            if any(kw in combined_text for kw in keywords):
                matches.append((row['Number'], row['Question'][:70]))
        
        results[topic] = matches
    return results

heavy_matches = count_topic_matches(df, heavy_topics)

for topic, matches in sorted(heavy_matches.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{topic}: {len(matches)} questions")
    if matches:
        for qnum, qtxt in matches[:3]:
            print(f"  Q{qnum}: {qtxt}...")
        if len(matches) > 3:
            print(f"  ... and {len(matches) - 3} more")
    else:
        print("  ⚠️  COVERAGE GAP - NO QUESTIONS FOUND")

print("\n" + "="*80)
print("LIGHTLY TESTED TOPICS (may not need heavy focus)")
print("="*80)

light_topics = {
    'Cluster Configuration': ['cluster', 'config', 'autoscale', 'worker', 'driver'],
    'Architecture/Control Plane': ['control plane', 'data plane', 'workspace', 'metastore'],
    'Delta Sharing': ['delta sharing', 'share', 'recipient'],
    'Spark Internals': ['shuffle', 'stage', 'task', 'executor']
}

light_matches = count_topic_matches(df, light_topics)

for topic, matches in sorted(light_matches.items(), key=lambda x: len(x[1]), reverse=True):
    print(f"\n{topic}: {len(matches)} questions")
    if matches:
        for qnum, qtxt in matches[:2]:
            print(f"  Q{qnum}: {qtxt}...")

print("\n" + "="*80)
print("SUMMARY & RECOMMENDATIONS")
print("="*80)

heavy_total = sum(len(v) for v in heavy_matches.values())
light_total = sum(len(v) for v in light_matches.values())

print(f"\nCoverage of heavily-tested topics: {heavy_total} questions ({heavy_total/len(df)*100:.1f}%)")
print(f"Coverage of lightly-tested topics: {light_total} questions ({light_total/len(df)*100:.1f}%)")

print("\n📊 GAPS TO ADDRESS:")
for topic, matches in heavy_matches.items():
    if len(matches) == 0:
        print(f"  ❌ {topic}: 0 questions - CREATE NEW QUESTIONS")
    elif len(matches) < 3:
        print(f"  ⚠️  {topic}: Only {len(matches)} question(s) - ADD MORE PRACTICE")
    else:
        print(f"  ✓ {topic}: {len(matches)} questions - Good coverage")
