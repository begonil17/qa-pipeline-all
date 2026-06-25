import json
import os
import re
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")

BAD_OUTPUT_DIR = Path("data/debug/llm_bad_outputs")
BAD_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _save_bad_output(text: str):
    debug_path = BAD_OUTPUT_DIR / "bad_json_output.txt"
    debug_path.write_text(text, encoding="utf-8")
    return debug_path


def _extract_json(text: str):
    original_text = text
    text = text.strip()

    match = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\[.*\]|\{.*\})", text, re.DOTALL)
    if match:
        candidate = match.group(1).strip()

        try:
            return json.loads(candidate)
        except json.JSONDecodeError as e:
            debug_path = _save_bad_output(original_text)
            raise ValueError(
                f"LLM returned invalid JSON. Saved raw output to {debug_path}. "
                f"JSON error: {e}"
            ) from e

    debug_path = _save_bad_output(original_text)
    raise ValueError(f"LLM did not return JSON. Saved raw output to {debug_path}.")


def _with_retries(call_fn, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return call_fn()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** attempt
            print(f"LLM call failed: {e}")
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)


def generate_json(prompt: str, model_name: str, schema: dict | None = None):
    if LLM_PROVIDER == "openai":
        from openai import OpenAI

        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=60,
            max_retries=2,
        )

        kwargs = {
            "model": model_name,
            "temperature": 0,
            "messages": [
                {
                    "role": "system",
                    "content": "Return only valid JSON. Do not use markdown.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
        }

        if schema is None:
            kwargs["response_format"] = {"type": "json_object"}

        response = _with_retries(
            lambda: client.chat.completions.create(**kwargs)
        )

        return _extract_json(response.choices[0].message.content)

    elif LLM_PROVIDER == "gemini":
        import google.generativeai as genai

        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

        model = genai.GenerativeModel(model_name)

        generation_config = {
            "temperature": 0,
            "response_mime_type": "application/json",
        }

        if schema is not None:
            generation_config["response_schema"] = schema

        response = _with_retries(
            lambda: model.generate_content(
                prompt,
                generation_config=generation_config,
            )
        )

        try:
            text = response.text
        except ValueError as e:
            raise ValueError(
                f"Gemini returned no text. This may be a safety/copyright block. "
                f"Original error: {e}"
            ) from e

        return _extract_json(text)

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}")