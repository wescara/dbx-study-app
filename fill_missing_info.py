from docx import Document
from docx.oxml import parse_xml
import pandas as pd
import re
from datetime import datetime
import zipfile
import os

doc_path = 'c:\\dbx-study-app\\data\\DCDEA Practice Exam 2.docx'
doc = Document(doc_path)

# Extract images from Word document
print("Extracting images from Word document...")
images_dir = 'c:\\dbx-study-app\\data\\extracted_images'
os.makedirs(images_dir, exist_ok=True)

with zipfile.ZipFile(doc_path, 'r') as zip_ref:
    for file in zip_ref.namelist():
        if file.startswith('word/media/'):
            zip_ref.extract(file, images_dir)
            image_name = file.split('/')[-1]
            extracted_path = os.path.join(images_dir, 'word', 'media', image_name)
            print(f"  Extracted: {image_name}")

# Track which questions have graphics
question_graphics = {}

for para in doc.paragraphs:
    text = para.text.strip()
    
    # Check if this paragraph is a question
    match = re.match(r'Question (\d+):', text)
    if match:
        q_num = int(match.group(1))
        question_graphics[q_num] = False
    
    # Check for drawing elements (graphics)
    if para.runs:
        for run in para.runs:
            if hasattr(run, '_element'):
                drawings = run._element.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}drawing')
                if drawings:
                    # Find the most recent question number
                    if question_graphics and max(question_graphics.keys()) in question_graphics:
                        question_graphics[max(question_graphics.keys())] = True
                        print(f"Question {max(question_graphics.keys())} has a graphic")

# Now load the existing extracted questions
df = pd.read_excel('c:\\dbx-study-app\\data\\DCDEA_Practice_Exam_2_NEW_QUESTIONS.xlsx')

# Define topic/difficulty mappings based on question keywords
def extract_topic_and_difficulty(question_text):
    """Extract topic and difficulty from question text"""
    question_lower = question_text.lower()
    
    # Topic mapping
    topics = {
        'Development and Ingestion': ['auto loader', 'lakeflow', 'ingest', 'ingestion', 'stream', 'spark sql'],
        'SQL and Transformations': ['sql', 'select', 'join', 'aggregate', 'group by', 'union', 'window', 'pivot'],
        'Data Management': ['delta lake', 'delta', 'table', 'schema', 'column', 'partitioning', 'bucket'],
        'Performance Optimization': ['broadcast', 'cache', 'shuffle', 'partition', 'coalesce', 'repartition', 'performance', 'join'],
        'Governance and Security': ['acl', 'permission', 'access', 'security', 'governance', 'policy', 'unity catalog', 'lineage'],
        'Job Management': ['job', 'task', 'workflow', 'schedule', 'trigger', 'repair', 'run'],
        'Monitoring and Debugging': ['debug', 'monitor', 'log', 'error', 'query', 'profile', 'metrics'],
        'Machine Learning': ['ml', 'model', 'feature', 'training', 'prediction', 'mlflow', 'tuning'],
        'Data Quality': ['quality', 'validation', 'constraint', 'expectation', 'dbt', 'test'],
    }
    
    topic = 'General'
    for t, keywords in topics.items():
        if any(kw in question_lower for kw in keywords):
            topic = t
            break
    
    # Difficulty mapping
    if any(word in question_lower for word in ['which', 'what is', 'identifies', 'describes', 'selects', 'choose']):
        if any(word in question_lower for word in ['best', 'most appropriate', 'correctly']):
            difficulty = 'Medium'
        else:
            difficulty = 'Easy'
    else:
        difficulty = 'Hard'
    
    # More nuanced difficulty assessment
    sentence_complexity = len(question_text.split(';'))
    if 'two statements' in question_lower or 'multiple' in question_lower:
        difficulty = 'Hard'
    elif sentence_complexity > 3:
        difficulty = 'Medium'
    elif difficulty == 'Easy' and len(question_text) > 200:
        difficulty = 'Medium'
    
    return topic, difficulty

# Fill in Topic, Subtopic, and Difficulty
topics_list = []
difficulties_list = []
graphics_list = []
subtopics_list = []

for idx, row in df.iterrows():
    q_num = row['Number']
    question = row['Question']
    question_lower = question.lower()
    
    topic, difficulty = extract_topic_and_difficulty(question)
    
    topics_list.append(topic)
    difficulties_list.append(difficulty)
    graphics_list.append('Yes' if question_graphics.get(q_num, False) else '')
    
    # Subtopic - derived from more specific keywords
    subtopics = {
        'Development and Ingestion': [
            ('Auto Loader and debugging tools', ['auto loader', 'debug', 'rescued']),
            ('Lakeflow Connect', ['lakeflow', 'connector', 'managed', 'saas']),
            ('Streaming Data', ['stream', 'kafka', 'kinesis']),
        ],
        'SQL and Transformations': [
            ('Joins and Aggregations', ['join', 'aggregate', 'group']),
            ('Window Functions', ['window', 'over', 'partition by']),
            ('CTE and Subqueries', ['cte', 'with', 'subquery']),
        ],
        'Data Management': [
            ('Delta Lake Basics', ['delta', 'table', 'schema']),
            ('Partitioning and Bucketing', ['partition', 'bucket', 'clustering']),
            ('Data Organization', ['column', 'format', 'location']),
        ],
        'Performance Optimization': [
            ('Join Optimization', ['broadcast', 'join', 'shuffle']),
            ('Caching and Partitioning', ['cache', 'coalesce', 'repartition']),
            ('Query Tuning', ['optimize', 'performance', 'shuffle']),
        ],
        'Governance and Security': [
            ('Access Control', ['acl', 'permission', 'grant', 'access']),
            ('Unity Catalog', ['unity catalog', 'uc', 'metastore']),
            ('Compliance', ['policy', 'governance', 'audit']),
        ],
        'Job Management': [
            ('Workflow and Scheduling', ['workflow', 'job', 'schedule']),
            ('Task Management', ['task', 'condition', 'repair']),
        ],
    }
    
    subtopic = ''
    for sub_topic, keywords_list in subtopics.get(topic, []):
        if any(kw in question_lower for kw in keywords_list):
            subtopic = sub_topic
            break
    
    subtopics_list.append(subtopic)

# Update DataFrame
df['Topic'] = topics_list
df['Subtopic'] = subtopics_list
df['Difficulty'] = difficulties_list
df['Graphic'] = graphics_list

# Save updated Excel
output_file = 'c:\\dbx-study-app\\data\\DCDEA_Practice_Exam_2_NEW_QUESTIONS.xlsx'
df.to_excel(output_file, index=False, sheet_name='Questions')

print(f"\n✓ Updated Excel file with Topic, Subtopic, Difficulty, and Graphics information")
print(f"\nTopic distribution:")
print(df['Topic'].value_counts())
print(f"\nDifficulty distribution:")
print(df['Difficulty'].value_counts())
print(f"\nQuestions with graphics: {len(df[df['Graphic'] == 'Yes'])}")
print(f"\nSample rows:")
print(df[['Number', 'Question', 'Topic', 'Subtopic', 'Difficulty', 'Graphic']].head(5).to_string())
