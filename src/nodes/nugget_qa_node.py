import json
from pathlib import Path

from src.nugget_extractor import update_nuggets_with_chunk
from src.qa_generator import generate_qa_from_nuggets
from src.storage_decision import decide_nugget_storage
from src.fact_validator import validate_nuggets_against_chunk


NUGGET_DIR = Path("data/output/nuggets")
NUGGET_QA_DIR = Path("data/output/nugget_qa")

NUGGET_DIR.mkdir(parents=True, exist_ok=True)
NUGGET_QA_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(title: str) -> str:
    return (
        title
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def completed_outputs_exist(nugget_path: Path, nugget_qa_path: Path) -> bool:
    return (
        nugget_path.exists()
        and nugget_path.stat().st_size > 0
        and nugget_qa_path.exists()
        and nugget_qa_path.stat().st_size > 0
    )


def nugget_importance(nugget):
    try:
        return int(nugget.get("importance", 0))
    except (TypeError, ValueError):
        return 0


def prune_nuggets_by_importance(nuggets, max_nuggets):
    return sorted(
        nuggets,
        key=nugget_importance,
        reverse=True,
    )[:max_nuggets]


def nugget_ids(nuggets):
    return [nugget.get("nugget_id") for nugget in nuggets]


def split_nuggets_for_chunk_validation(current_nuggets, extracted_nuggets):
    current_by_id = {
        nugget.get("nugget_id"): nugget
        for nugget in current_nuggets
        if nugget.get("nugget_id")
    }
    preserved_by_id = {
        nugget_id: dict(nugget)
        for nugget_id, nugget in current_by_id.items()
    }
    nuggets_to_validate = []

    for nugget in extracted_nuggets:
        nugget_id = nugget.get("nugget_id")
        previous = current_by_id.get(nugget_id)

        if previous is None:
            nuggets_to_validate.append(nugget)
            continue

        if nugget.get("text") == previous.get("text"):
            preserved_by_id[nugget_id] = dict(nugget)
        else:
            nuggets_to_validate.append(nugget)

    preserved_nuggets = []
    seen_ids = set()

    for nugget in current_nuggets:
        nugget_id = nugget.get("nugget_id")

        if not nugget_id:
            preserved_nuggets.append(dict(nugget))
            continue

        if nugget_id in preserved_by_id and nugget_id not in seen_ids:
            preserved_nuggets.append(preserved_by_id[nugget_id])
            seen_ids.add(nugget_id)

    return preserved_nuggets, nuggets_to_validate


def merge_validated_nuggets(preserved_nuggets, validated_nuggets):
    merged_nuggets = []
    index_by_id = {}

    for nugget in preserved_nuggets:
        nugget_id = nugget.get("nugget_id")
        if nugget_id and nugget_id not in index_by_id:
            index_by_id[nugget_id] = len(merged_nuggets)
        merged_nuggets.append(dict(nugget))

    for nugget in validated_nuggets:
        nugget_id = nugget.get("nugget_id")

        if nugget_id and nugget_id in index_by_id:
            merged_nuggets[index_by_id[nugget_id]] = dict(nugget)
            continue

        if nugget_id:
            index_by_id[nugget_id] = len(merged_nuggets)
        merged_nuggets.append(dict(nugget))

    return merged_nuggets


def nugget_qa_node(state):
    print("Starting nugget extraction and QA generation...")

    nugget_paths = []
    nugget_qa_paths = []

    for title, chunks in state["article_chunks"].items():
        print(f"Starting nugget pipeline for: {title}")

        nugget_path = NUGGET_DIR / f"{safe_filename(title)}.json"
        nugget_qa_path = NUGGET_QA_DIR / f"{safe_filename(title)}.jsonl"

        if completed_outputs_exist(nugget_path, nugget_qa_path):
            nugget_paths.append(str(nugget_path))
            nugget_qa_paths.append(str(nugget_qa_path))
            print(f"Finished nugget pipeline for: {title} (cached)")
            continue

        nuggets = []

        for chunk_index, chunk in enumerate(chunks, start=1):
            print(
                f"Starting nugget extraction chunk "
                f"{chunk_index}/{len(chunks)} for: {title}"
            )

            extracted_nuggets = update_nuggets_with_chunk(
                article_title=title,
                chunk=chunk,
                current_nuggets=nuggets,
                max_nuggets=state.get("max_nuggets_per_chunk", 5),
            )

            print(
                f"Finished nugget extraction chunk "
                f"{chunk_index}/{len(chunks)} for: {title}. "
                f"Extracted {len(extracted_nuggets)} nuggets."
            )
            print(
                f"After chunk extraction for: {title}, "
                f"chunk {chunk_index}/{len(chunks)}. "
                f"Current count before extraction: {len(nuggets)}. "
                f"Extracted/updated IDs: {nugget_ids(extracted_nuggets)}"
            )

            preserved_nuggets, nuggets_to_validate = (
                split_nuggets_for_chunk_validation(
                    current_nuggets=nuggets,
                    extracted_nuggets=extracted_nuggets,
                )
            )

            print(
                f"Preparing validation chunk {chunk_index}/{len(chunks)} "
                f"for: {title}. Preserving {len(preserved_nuggets)} "
                f"previous/unchanged nuggets and validating "
                f"{len(nuggets_to_validate)} new/modified nuggets."
            )

            print(
                f"Starting nugget validation chunk "
                f"{chunk_index}/{len(chunks)} for: {title}"
            )

            validated_nuggets = validate_nuggets_against_chunk(
                article_title=title,
                chunk=chunk,
                nuggets=nuggets_to_validate,
            )

            print(
                f"Finished nugget validation chunk "
                f"{chunk_index}/{len(chunks)} for: {title}. "
                f"Validated {len(validated_nuggets)} nuggets."
            )
            print(
                f"After chunk validation for: {title}, "
                f"chunk {chunk_index}/{len(chunks)}. "
                f"Validated IDs: {nugget_ids(validated_nuggets)}"
            )

            nuggets = merge_validated_nuggets(
                preserved_nuggets=preserved_nuggets,
                validated_nuggets=validated_nuggets,
            )

            print(
                f"Accumulated nuggets after chunk {chunk_index}/{len(chunks)} "
                f"for: {title}: {len(nuggets)}. IDs: {nugget_ids(nuggets)}"
            )

        nuggets = prune_nuggets_by_importance(
            nuggets,
            state.get("max_nuggets_per_article", 20),
        )

        print(
            f"Before storage decision for: {title}. "
            f"Candidate nuggets: {len(nuggets)}. IDs: {nugget_ids(nuggets)}"
        )

        print(f"Starting nugget storage decision for: {title}")

        nuggets = decide_nugget_storage(
            article_title=title,
            candidate_nuggets=nuggets,
            existing_nuggets=[],
        )

        print(
            f"Finished nugget storage decision for: {title}. "
            f"Keeping {len(nuggets)} nuggets."
        )
        print(
            f"After storage decision for: {title}. "
            f"Kept IDs: {nugget_ids(nuggets)}"
        )

        print(f"Starting nugget QA generation for: {title}")
        print(
            f"Before QA generation for: {title}. "
            f"Nuggets available: {len(nuggets)}. IDs: {nugget_ids(nuggets)}"
        )

        qa_pairs = generate_qa_from_nuggets(nuggets)

        print(
            f"Finished nugget QA generation for: {title}. "
            f"Generated {len(qa_pairs)} QA pairs."
        )

        nugget_path.write_text(
            json.dumps(nuggets, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        with nugget_qa_path.open("w", encoding="utf-8") as f:
            for qa in qa_pairs:
                f.write(json.dumps(qa, ensure_ascii=False) + "\n")

        nugget_paths.append(str(nugget_path))
        nugget_qa_paths.append(str(nugget_qa_path))

        print(f"Finished nugget pipeline for: {title}")

    print(
        f"Finished nugget extraction and QA generation. "
        f"Created {len(nugget_paths)} nugget files and "
        f"{len(nugget_qa_paths)} QA files."
    )

    return {
        "nugget_paths": nugget_paths,
        "nugget_qa_paths": nugget_qa_paths,
    }
