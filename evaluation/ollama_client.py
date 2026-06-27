import requests
import json

ANSWER_SCHEMA = {
    "type": "object",
    "properties": {
        "original": {
            "type": "string"
        },
        "direct": {
            "type": "string"
        },
        "conversational": {
            "type": "string"
        },
        "indirect": {
            "type": "string"
        }
    },
    "required": [
        "original",
        "direct",
        "conversational",
        "indirect"
    ]
}


class OllamaClient:

    def __init__(
        self,
        model="gemma-rag",
        host="http://localhost:11434",
    ):

        self.model = model
        self.host = host

    def generate(
        self,
        prompt,
        retries=3,
    ):

        for attempt in range(retries):

            try:

                response = requests.post(

                    f"{self.host}/api/chat",

                    json={
                        "model": self.model,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt,
                            }
                        ],
                        "stream": False,
                        "options": {
                            "temperature": 0,
                        }
                    },

                    timeout=600,

                )

                response.raise_for_status()

                return response.json()["message"]["content"].strip()

            except Exception as e:

                print(
                    f"Retry {attempt+1}/{retries}: {e}"
                )

        raise RuntimeError(
            "Gemma failed after retries."
        )