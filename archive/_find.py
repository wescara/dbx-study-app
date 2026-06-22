lines = open('app.py', encoding='utf-8').readlines()
for i, l in enumerate(lines, 1):
    if 'critical' in l or 'Critical' in l or 'topic_scores' in l:
        print(i, repr(l[:120]))
