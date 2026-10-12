import os
from pathlib import Path
from typing import cast
from google import genai
from google.genai import types

from .models import PackageDims
from .prompts import get_extraction_prompt

def model_name() -> str:
    if not (name := os.getenv("GEMINI_MODEL")):
        raise RuntimeError("GEMINI_MODEL is not set.")

    return name

def llm_client() -> genai.Client:
    if not (api_key := os.getenv("GEMINI_API_KEY")):
        raise RuntimeError("GEMINI_API_KEY is not set.")

    return genai.Client(api_key=api_key)

def llm_extract_package_dims(pdf_path: Path, package: str) -> PackageDims:
    client = llm_client()

    res = client.models.generate_content(
        model = model_name(),
        contents = [
            types.Part.from_bytes(data=Path(pdf_path).read_bytes(), mime_type="application/pdf"),
            get_extraction_prompt().format(package=package)
        ],
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PackageDims,
            temperature=0,
        ),
    )

    if res.parsed is None:
        raise ValueError(f"Response did not match schema. Raw text: {res.text}")

    return cast(PackageDims, res.parsed)