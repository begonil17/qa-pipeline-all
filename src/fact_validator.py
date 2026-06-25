import json

from src.config import NUGGET_EXTRACTION_MODEL
from src.llm.client import generate_json
from src.schemas import FactValidation
from src.llm.schemas import FACT_VALIDATION_SCHEMA


def validate_nuggets_against_chunk(
    article_title: str,
    chunk: str,
    nuggets: list[dict],
) -> list[dict]:
    if not nuggets:
        return []

    prompt = f"""
You are validating extracted Turkish atomic knowledge nuggets against their original Wikipedia article chunk.

Article title:
{article_title}

Original article chunk:
{chunk}

Extracted nuggets:
{json.dumps(nuggets, ensure_ascii=False, indent=2)}

For each nugget, decide whether it is supported by the original chunk.

Verdicts:
- supported: the nugget is clearly supported by the chunk
- partially_supported: the nugget is mostly correct but needs rewriting to be fully supported
- unsupported: the nugget is not supported by the chunk

Rules:
- Do not use external knowledge.
- corrected_text must be Turkish.
- corrected_text must contain only the supported version of the fact.
- If unsupported, corrected_text should be an empty string.
- Return ONLY valid JSON array.

"""

    raw = generate_json(
        prompt=prompt,
        model_name=NUGGET_EXTRACTION_MODEL,
        schema=FACT_VALIDATION_SCHEMA
    )

    validations = [FactValidation(**item) for item in raw]

    validated_nuggets = []

    for validation in validations:
        original = next(
            (n for n in nuggets if n["nugget_id"] == validation.nugget_id),
            None,
        )

        if original is None:
            continue

        if validation.verdict == "unsupported":
            continue

        updated = dict(original)
        updated["text"] = validation.corrected_text
        updated["validation_verdict"] = validation.verdict
        updated["validation_reason"] = validation.reason

        validated_nuggets.append(updated)

    return validated_nuggets