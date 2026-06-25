import re

def clean_article(text: str) -> str:
    text = re.sub(r"\[\d+\]", "", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()