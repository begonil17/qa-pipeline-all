import os

from huggingface_hub import InferenceClient
from dotenv import load_dotenv

load_dotenv()

class HFClient:

    def __init__(self):

        self.client = InferenceClient(

            model="https://m63htav5i2ctwik7.us-east4.gcp.endpoints.huggingface.cloud",

            token=os.environ["HF_TOKEN"]

        )

    def generate(self, prompt):

        completion = self.client.chat.completions.create(

            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],

            temperature=0,

            max_tokens=1024,

        )

        return completion.choices[0].message.content.strip()