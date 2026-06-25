import json
from openai import OpenAI
from dotenv import load_dotenv
from uuid import uuid4

from src.llm.client import generate_json
from src.config import NUGGET_EXTRACTION_MODEL
from src.schemas import Nugget
from src.llm.schemas import NUGGET_EXTRACTION_SCHEMA

load_dotenv()

def make_nugget_id() -> str:
    return f"ng_{uuid4().hex[:12]}"

def update_nuggets_with_chunk(
    article_title: str,
    chunk: str,
    current_nuggets: list[dict],
    max_nuggets: int = 10,
) -> list[dict]:

    prompt = f"""
You are extracting compact atomic knowledge nuggets from a Wikipedia article.

Article title: {article_title}

Current nugget list:
{json.dumps(current_nuggets, ensure_ascii=False, indent=2)}

New article chunk:
{chunk}

Update the nugget list using the new chunk.

Rules:
- Output Turkish nuggets.
- Each nugget must be atomic: one clear paraphrased fact only.
- Avoid long direct translations or close paraphrases of source sentences.
- Avoid duplicates.
- Merge overlapping facts.
- Keep only important general-purpose knowledge.
- Maximum {max_nuggets} nuggets.
- Order by importance.
- importance must be an integer from 1 to 10.
- Return ONLY valid JSON array.

"""

    raw = generate_json(
        prompt=prompt,
        model_name=NUGGET_EXTRACTION_MODEL,
        schema=NUGGET_EXTRACTION_SCHEMA
        )

    for item in raw:
        if 'nugget_id' not in item or not item['nugget_id']:
            item['nugget_id'] = make_nugget_id()
        
        item['source_article'] = article_title
        

    validated = [Nugget(**item) for item in raw]

    return [item.model_dump() for item in validated]
