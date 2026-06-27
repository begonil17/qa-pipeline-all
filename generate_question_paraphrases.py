import json
from pathlib import Path

from src.config import NUGGET_QA_MODEL
from src.llm.client import generate_json
from src.llm.schemas import QUESTION_PARAPHRASE_SCHEMA

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR

OUTPUT_ROOT = PROJECT_ROOT / "output"

INPUT_DIR = OUTPUT_ROOT / "nugget_qa"
OUTPUT_DIR = OUTPUT_ROOT / "nugget_qa_paraphrased"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


BATCH_SIZE = 10

processed = 0

PROMPT_TEMPLATE = """
You are rewriting a Turkish question.

Original question:

"{question}"

Expected answer:

"{answer}"

Generate three semantically equivalent questions.

Requirements:

- Ask for exactly the same information.
- Do NOT change the expected answer.
- Do NOT introduce new information.
- Keep the language Turkish.
- Each question should sound natural.
- The three questions should be stylistically different.

Styles:

1. direct
   - Minimal wording changes.

2. conversational
   - How an average Turkish speaker would naturally ask.

3. indirect
   - A more descriptive formulation asking for the same fact.

Return ONLY valid JSON.
"""


def batch(items, batch_size):

    for i in range(0, len(items), batch_size):
        yield items[i:i + batch_size]

def load_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)

def build_prompt(batch):

    prompt = """
You will receive multiple Turkish question-answer pairs.

For EACH pair generate exactly three semantically equivalent questions.

The output MUST contain exactly one paraphrase object for every input question.

The output MUST preserve the IDs.

The output order does NOT matter because IDs will be used for matching.

Rules:

- Preserve the meaning exactly.
- Do NOT change the expected answer.
- Do NOT introduce new facts.
- Keep Turkish.
- All three questions should sound natural.
- The three questions should be stylistically different.
- The number of returned objects MUST exactly equal the number of input questions.
- Do not skip any question.
- If you cannot generate a paraphrase for one question, still return an object for it.
- Every input ID must appear exactly once.

Styles:

- direct
- conversational
- indirect

Return ONLY valid JSON.

Questions:

"""

    for i, qa in enumerate(batch):

        prompt += f"""

Question ID: {i}

Original:
{qa["question"]}

Expected answer:
{qa["answer"]}

"""

    return prompt


def main():

    qa_files = sorted(INPUT_DIR.glob("*.jsonl"))

    print(f"Found {len(qa_files)} QA files.\n")

    for file_index, qa_file in enumerate(qa_files, start=1):

        output_file = OUTPUT_DIR / qa_file.name

        if output_file.exists():
            print(f"[{file_index}/{len(qa_files)}] Skipping {qa_file.name}")
            continue

        print(f"[{file_index}/{len(qa_files)}] Processing {qa_file.name}")

        records = list(load_jsonl(qa_file))

        with output_file.open("w", encoding="utf-8") as fout:

            for batch_records in batch(records, BATCH_SIZE):

                print(
                    f"    QA {processed + 1}-{min(processed + len(batch_records), len(records))}/{len(records)}",
                    end="\r",
                )

                prompt = build_prompt(batch_records)

                response = generate_json(
                    prompt=prompt,
                    model_name=NUGGET_QA_MODEL,
                    schema=QUESTION_PARAPHRASE_SCHEMA,
                )

                paraphrase_batch = response["paraphrases"]

                if len(paraphrase_batch) != len(batch_records):
                    raise ValueError(
                        f"Expected {len(batch_records)} paraphrase objects "
                        f"but got {len(paraphrase_batch)}."
                    )

                paraphrase_map = {
                    item["id"]: item
                    for item in paraphrase_batch
                }

                for idx, qa in enumerate(batch_records):

                    if idx not in paraphrase_map:
                        raise ValueError(
                            f"Missing paraphrases for Question ID {idx}."
                        )

                    p = paraphrase_map[idx]

                    qa["paraphrases"] = {
                        "direct": p["direct"],
                        "conversational": p["conversational"],
                        "indirect": p["indirect"],
                    }

                    fout.write(
                        json.dumps(
                            qa,
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

                processed += len(batch_records)

        print(f"\nFinished {qa_file.name}\n")

    print("Done.")


if __name__ == "__main__":
    main()