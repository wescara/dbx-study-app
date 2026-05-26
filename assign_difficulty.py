import pandas as pd
import shutil
import os

df = pd.read_excel('data/DCDEA_Practice_Exam_2_Questions.xlsx')
dcdea = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)].copy()

# Map questions to difficulty based on content analysis
difficulty_map = {
    2045: 'Easy',      # Lakeflow Connect basic connection
    2046: 'Medium',    # Join operations with conditions
    2047: 'Medium',    # DLT syntax and best practices
    2048: 'Hard',      # Performance tuning scenarios
    2049: 'Easy',      # Notebook capabilities - basic
    2050: 'Medium',    # Lakehouse architecture concepts
    2051: 'Medium',    # Spark SQL operations
    2052: 'Easy',      # Auto Loader basic setup
    2053: 'Medium',    # Auto Loader with options
    2054: 'Medium',    # Lakeflow Connect with parameters
    2055: 'Medium',    # DLT quality metrics/guarantees
    2056: 'Easy',      # Notebook features - basic
    2057: 'Hard',      # ABAC permissions and security
    2058: 'Hard',      # Optimize data layout
    2059: 'Medium',    # Lakehouse architecture details
    2060: 'Medium',    # Nested data handling
    2061: 'Hard',      # Performance optimization
    2062: 'Medium',    # Auto Loader behavior
    2063: 'Hard',      # Cost management strategies
    2064: 'Medium',    # Complex join scenario
    2065: 'Medium',    # DLT pipeline design
    2066: 'Hard',      # DLT advanced features
    2067: 'Medium',    # Spark SQL operations
    2068: 'Hard',      # Spark UI optimization
    2069: 'Hard',      # Streaming real-time data
    2070: 'Medium',    # Structured Streaming basics
    2071: 'Medium',    # Structured Streaming parameters
    2072: 'Medium',    # PySpark operations
    2073: 'Hard',      # Performance tuning advanced
    2074: 'Easy',      # Auto Loader basic
    2075: 'Medium',    # Spark SQL analysis
    2076: 'Hard',      # Performance optimization
    2077: 'Easy',      # Notebook features
    2078: 'Hard',      # Data layout optimization
    2079: 'Easy',      # Auto Loader basic setup
    2080: 'Hard',      # Streaming with advanced concepts
    2081: 'Medium',    # Structured Streaming operations
    2082: 'Hard',      # Performance tuning strategies
    2083: 'Medium',    # Notebook capabilities
    2084: 'Medium',    # Join operations
    2085: 'Medium',    # Schema enforcement concepts
    2086: 'Hard',      # DLT advanced usage
    2087: 'Medium',    # Compute selection criteria
    2088: 'Medium',    # Join operations
    2089: 'Hard',      # Streaming real-time scenarios
}

# Apply difficulty assignments
for qid, difficulty in difficulty_map.items():
    idx = df[df['QID'] == qid].index[0]
    df.loc[idx, 'Difficulty'] = difficulty

# Save updated file to temp, then move
temp_file = 'data/DCDEA_Practice_Exam_2_Questions_TEMP.xlsx'
df.to_excel(temp_file, index=False)

final_file = 'data/DCDEA_Practice_Exam_2_Questions.xlsx'
if os.path.exists(final_file):
    try:
        os.remove(final_file)
    except:
        pass
shutil.move(temp_file, final_file)

# Print summary
dcdea_updated = df[(df['QID'] >= 2045) & (df['QID'] <= 2089)]
print("✓ Difficulty levels assigned\n")
print(f"Easy:   {(dcdea_updated['Difficulty'] == 'Easy').sum()} questions")
print(f"Medium: {(dcdea_updated['Difficulty'] == 'Medium').sum()} questions")
print(f"Hard:   {(dcdea_updated['Difficulty'] == 'Hard').sum()} questions")

print("\n" + "="*60)
for idx in [0, 22, 44]:
    row = dcdea_updated.iloc[idx]
    print(f"\nQ{int(row['Number'])} (QID {int(row['QID'])})")
    print(f"  Topic: {row['Topic']}")
    print(f"  Difficulty: {row['Difficulty']}")
    print(f"  Question: {row['Question'][:80]}...")
