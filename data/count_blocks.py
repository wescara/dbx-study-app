with open('UDQuestionsAnswers.txt', 'r', encoding='utf-8') as f:
    content = f.read()

blocks = [b.strip() for b in content.split('\n\n') if b.strip()]
print(f"Total blocks: {len(blocks)}")

# Count how many start with "A." (these are option blocks)
option_blocks = sum(1 for b in blocks if b.startswith('A.'))
print(f"Option blocks (starting with 'A.'): {option_blocks}")

# Assuming each question needs 1 question block + 1 option block
print(f"Estimated questions based on option blocks: {option_blocks}")

# Show distribution
print("\nBlock types:")
for i in range(min(100, len(blocks))):
    first_line = blocks[i].split('\n')[0][:60]
    starts_with_option = "OPTION" if blocks[i].startswith('A.') else "TEXT"
    if i < 50 or (i >= 100 and i < 150) or i >= len(blocks) - 20:
        print(f"{i}: [{starts_with_option}] {first_line}")
    elif i == 50:
        print("...")
