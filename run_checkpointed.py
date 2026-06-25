import json
from pathlib import Path
import time

from src.graph.workflow import build_graph
from src.category_loader import load_categories


CHECKPOINT_DIR = Path("data/checkpoints")
CHECKPOINT_PATH = CHECKPOINT_DIR / "category_progress.json"


def load_checkpoint():
    if not CHECKPOINT_PATH.exists():
        return {
            "next_category_index": 0,
            "completed_categories": [],
        }

    with CHECKPOINT_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_checkpoint(next_category_index, completed_categories):
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

    with CHECKPOINT_PATH.open("w", encoding="utf-8") as f:
        json.dump(
            {
                "next_category_index": next_category_index,
                "completed_categories": completed_categories,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )


def main():
    app = build_graph()
    categories = load_categories()

    checkpoint = load_checkpoint()

    next_index = checkpoint["next_category_index"]
    completed_categories = checkpoint["completed_categories"]

    if next_index >= len(categories):
        print("All categories are already completed.")
        return

    while next_index < len(categories):
        category = categories[next_index]
        category_name = category["name"]

        print("=" * 80)
        print(f"Processing category {next_index + 1}/{len(categories)}: {category_name}")
        print("=" * 80)

        result = app.invoke({
            "categories": [category],

            "articles_per_focus": 2,
            "extra_articles_per_category": 2,

            "max_articles": 50,
            "max_chunks_per_article": 30,
            "max_nuggets_per_chunk": 10,
            "max_nuggets_per_article": 40,

            "enable_raw_qa": False,
            "errors": [],
        })

        completed_categories.append(category_name)
        next_index += 1

        save_checkpoint(
            next_category_index=next_index,
            completed_categories=completed_categories,
        )

        print()
        print(f"Completed category: {category_name}")
        print(f"Checkpoint saved: {CHECKPOINT_PATH}")
        print("Errors:", result.get("errors"))
        print()

        if next_index >= len(categories):
            print("All categories completed.")
            break

        # user_input = input("Type 'ok' to continue to the next category, or anything else to stop: ")

        # if user_input.strip().lower() != "ok":
        #     print("Stopped. You can continue later by running this script again.")
        #     break
        
        time.sleep(10)
        print("Continuing with the next category...")

if __name__ == "__main__":
    main()
