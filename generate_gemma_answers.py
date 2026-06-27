import json
from pathlib import Path

from evaluation.ollama_client import OllamaClient
from evaluation.hf_client import HFClient
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parent

INPUT_DIR = ROOT / "data" / "output" / "nugget_qa_paraphrased"

OUTPUT_DIR = ROOT / "data" / "output" / "gemma_answers"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


#client = OllamaClient()
client = HFClient()

PROMPT = """
You are a factual question answering assistant.

Answer the following question.

Rules:
- Answer only the question.
- Do NOT repeat or rewrite the question.
- Be concise.
- If you do not know the answer, write exactly:
Bilmiyorum

Question:

{question}
"""

def process_qa(qa):

    questions = {
        "original": qa["question"],
        "direct": qa["paraphrases"]["direct"],
        "conversational": qa["paraphrases"]["conversational"],
        "indirect": qa["paraphrases"]["indirect"],
    }

    answers = {}

    for key, question in questions.items():

        prompt = PROMPT.format(
            question=question,
        )

        answers[key] = client.generate(prompt)

    qa["gemma_answers"] = answers

    return qa

def load_jsonl(path: Path):

    with path.open("r", encoding="utf-8") as f:

        for line in f:

            line = line.strip()

            if line:

                yield json.loads(line)


qa_files = sorted(INPUT_DIR.glob("*.jsonl"))

print(f"Found {len(qa_files)} files")


for file_no, qa_file in enumerate(qa_files, start=1):

    output_file = OUTPUT_DIR / qa_file.name

    if output_file.exists():

        print(f"[{file_no}/{len(qa_files)}] Skipping {qa_file.name}")

        continue

    print(f"[{file_no}/{len(qa_files)}] {qa_file.name}")


    with output_file.open("w", encoding="utf-8") as fout:

        total = sum(1 for _ in load_jsonl(qa_file))

        # records = list(load_jsonl(qa_file))

        # with ThreadPoolExecutor(max_workers=8) as executor:

        #     futures = [
        #         executor.submit(process_qa, qa)
        #         for qa in records
        #     ]

        #     for qa_no, future in enumerate(as_completed(futures), start=1):

        #         qa = future.result()

        #         print(
        #             f"    QA {qa_no}/{len(records)}",
        #             end="\r",
        #         )

        #         fout.write(
        #             json.dumps(
        #                 qa,
        #                 ensure_ascii=False,
        #             ) + "\n"
        #         )

        #         fout.flush()

        for qa_no, qa in enumerate(load_jsonl(qa_file), start=1):

            print(
                f"    QA {qa_no}/{total}",
                end="\r",
            )

            questions = {
                "original": qa["question"],
                "direct": qa["paraphrases"]["direct"],
                "conversational": qa["paraphrases"]["conversational"],
                "indirect": qa["paraphrases"]["indirect"],
            }

            answers = {}

            for key, question in questions.items():

                prompt = PROMPT.format(
                    question=question,
                )

                try:

                    answer = client.generate(prompt)

                except Exception:

                    print(f"\nFailed on {qa_file.name}")
                    raise

                # Remove markdown fences if the model adds them
                answer = answer.strip()

                if answer.startswith("```"):
                    lines = answer.splitlines()

                    if lines[0].startswith("```"):
                        lines = lines[1:]

                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]

                    answer = "\n".join(lines).strip()

                answers[key] = answer

            qa["gemma_answers"] = answers

            fout.write(
                json.dumps(
                    qa,
                    ensure_ascii=False,
                )
                + "\n"
            )

            fout.flush()

    print()