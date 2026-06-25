import os
from dotenv import load_dotenv

load_dotenv()

TOPIC_SELECTION_MODEL = os.getenv("TOPIC_SELECTION_MODEL", "gpt-5.1")
RAW_QA_MODEL = os.getenv("RAW_QA_MODEL", "gpt-5.1")
NUGGET_EXTRACTION_MODEL = os.getenv("NUGGET_EXTRACTION_MODEL", "gpt-5.1")
NUGGET_QA_MODEL = os.getenv("NUGGET_QA_MODEL", "gpt-5.1")