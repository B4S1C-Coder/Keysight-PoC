import os
from google import genai

def llm_client() -> genai.Client:
    if not (api_key := os.getenv("GEMINI_API_KEY")):
        raise RuntimeError("GEMINI_API_KEY is not set.")

    return genai.Client(api_key=api_key)