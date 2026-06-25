from pathlib import Path
import json

SCRIPT_DIR = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

OUTPUT_DIR = PROJECT_ROOT / "output"
NUGGET_DIR = OUTPUT_DIR / "nuggets"
QA_DIR = OUTPUT_DIR / "nugget_qa"

total_nuggets = 0
total_questions = 0

for nugget_file in NUGGET_DIR.rglob("*.json"):
    with open(nugget_file, encoding="utf-8") as f:
        nuggets = json.load(f)

    total_nuggets += len(nuggets)

for qa_file in QA_DIR.rglob("*.jsonl"):
    with open(qa_file, encoding="utf-8") as f:
        total_questions += sum(1 for line in f if line.strip())

print("Total nuggets:", total_nuggets)
print("Total questions:", total_questions)

if total_nuggets:
    print(
        "Questions per nugget:",
        round(total_questions / total_nuggets, 2)
    )

print("\nNugget files:")
for f in sorted(NUGGET_DIR.rglob("*.json")):
    print(f)

print("\nQA files:")
for f in sorted(QA_DIR.rglob("*.jsonl")):
    print(f)

print("SCRIPT_DIR:", SCRIPT_DIR)
print("PROJECT_ROOT:", PROJECT_ROOT)
print("OUTPUT_DIR:", OUTPUT_DIR)
print("NUGGET_DIR:", NUGGET_DIR)
print("NUGGET_QA_DIR:", QA_DIR)