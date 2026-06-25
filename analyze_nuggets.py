import json
from pathlib import Path
from collections import defaultdict

# NUGGET_DIR = Path("data/output/nuggets")
# NUGGET_QA_DIR = Path("data/output/nugget_qa")

SCRIPT_DIR = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_DIR.parent.parent

OUTPUT_DIR = PROJECT_ROOT / "output"
NUGGET_DIR = OUTPUT_DIR / "nuggets"
NUGGET_QA_DIR = OUTPUT_DIR / "nugget_qa"

REPORT_DIR = Path("reports")
REPORT_PATH = REPORT_DIR / "nugget_analysis.md"


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path: Path):
    records = []

    if not path.exists():
        return records

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line:
                records.append(json.loads(line))

    return records


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    total_nuggets = 0
    total_questions = 0
    total_files = len(list(NUGGET_DIR.glob("*.json")))

    with REPORT_PATH.open("w", encoding="utf-8") as md:
        print("=== Nugget Analizi ===\n")
        md.write("# Nugget Analizi\n\n")

        for nugget_file in sorted(NUGGET_DIR.glob("*.json")):
            article_name = nugget_file.stem
            qa_file = NUGGET_QA_DIR / f"{article_name}.jsonl"

            nuggets = load_json(nugget_file)
            qa_pairs = load_jsonl(qa_file)

            qa_by_nugget = defaultdict(list)

            for qa in qa_pairs:
                nugget_id = qa.get("nugget_id")
                question = qa.get("question")
                answer = qa.get("answer", "")

                if nugget_id and question:
                    qa_by_nugget[nugget_id].append({
                        "question": question,
                        "answer": answer,
                    })

            print(f"Dosya: {nugget_file.name}")
            print(f"Nugget sayısı: {len(nuggets)}")
            print(f"Soru sayısı: {len(qa_pairs)}")
            print()

            md.write(f"## Dosya: {nugget_file.name}\n\n")
            md.write(f"**Nugget sayısı:** {len(nuggets)}  \n")
            md.write(f"**Soru sayısı:** {len(qa_pairs)}\n\n")

            for nugget in nuggets:
                nugget_id = nugget.get("nugget_id", "UNKNOWN")
                nugget_text = nugget.get("text", "")

                qa_items = qa_by_nugget.get(nugget_id, [])

                print(f"  Nugget ID: {nugget_id}")
                print(f"  Nugget: {nugget_text}")
                print(f"  Sorular: {len(qa_items)}")

                md.write(f"### Nugget ID: `{nugget_id}`\n\n")
                md.write("**Nugget:**  \n")
                md.write(f"{nugget_text}\n\n")
                md.write(f"**Sorular:** {len(qa_items)}\n\n")

                for i, qa in enumerate(qa_items, start=1):
                    print(f"    {i}. Soru: {qa['question']}")
                    print(f"       Cevap: {qa['answer']}")

                    md.write(f"{i}. **Soru:** {qa['question']}  \n")
                    md.write(f"   **Cevap:** {qa['answer']}\n\n")

                print()
                md.write("---\n\n")

            total_nuggets += len(nuggets)
            total_questions += len(qa_pairs)

            print("-" * 80)
            print()

        print("=== Genel Özet ===")
        print(f"Toplam nugget dosyası: {total_files}")
        print(f"Toplam nugget: {total_nuggets}")
        print(f"Toplam soru: {total_questions}")

        md.write("# Genel Özet\n\n")
        md.write(f"- **Toplam nugget dosyası:** {total_files}\n")
        md.write(f"- **Toplam nugget:** {total_nuggets}\n")
        md.write(f"- **Toplam soru:** {total_questions}\n")

        if total_nuggets > 0:
            avg_questions = total_questions / total_nuggets
            print(f"Nugget başına ortalama soru: {avg_questions:.2f}")
            md.write(f"- **Nugget başına ortalama soru:** {avg_questions:.2f}\n")

    print(f"\nMarkdown raporu oluşturuldu: {REPORT_PATH}")


if __name__ == "__main__":
    main()