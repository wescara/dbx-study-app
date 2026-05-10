with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
print(f"Total blocks: {len(blocks)}\n")

# Show first 3 blocks
for i in range(min(3, len(blocks))):
    print(f"=== Block {i+1} ===")
    lines = blocks[i].split('\n')
    print(f"Lines in block: {len(lines)}")
    for j, line in enumerate(lines[:12]):  # Show first 12 lines
        print(f"{j}: {repr(line)}")
    print()
