import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
_client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(timeout=90000),   # 30 s, in milliseconds
)
MODEL = "gemini-3.5-flash-lite"



def generate(prompt: str, retries: int = 5) -> str:
    """Call the LLM; retry on temporary server errors."""
    for attempt in range(retries):
        try:
            resp = _client.models.generate_content(model=MODEL, contents=prompt)
            return resp.text or ""
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (2 ** attempt))   # 5s, 10s, 20s, 40s

if __name__ == "__main__":
    print(generate("Reply with exactly: LLM connection works"))