from dotenv import load_dotenv
load_dotenv()

import os
from typing import cast
from pathlib import Path

import pytest
from google import genai
from google.genai import types
from poc import PackageDims, llm_client

MODEL = os.getenv("GEMINI_MODEL", "")

PROMPT = (
    "The attached datasheet has a package drawing for style PK14-2. Return the "
    "overall component dimensions: length, width (overall body width of the "
    "component, not the lead width) and height (thickness), each in inches and "
    "mm. Use `max_` only for dimensions labelled MAX, and `tolerance` for +/- "
    "values. Leave unknown fields null."
)

PDF = Path(__file__).parent.parent / "data" / "Component_Datasheet_1.pdf"

def extract_package_dims(pdf_path: Path) -> PackageDims:
    client = llm_client()

    res = client.models.generate_content(
        model=MODEL,
        contents=[
            types.Part.from_bytes(data=pdf_path.read_bytes(), mime_type="application/pdf"),
            PROMPT,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PackageDims,
            temperature=0,
        ),
    )

    if res.parsed is None:
        raise ValueError(f"Response did not match schema. Raw text: {res.text}")

    return cast(PackageDims, res.parsed)

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(
        not os.getenv("GEMINI_API_KEY") or not MODEL,
        reason="GEMINI_API_KEY or GEMINI_MODEL not set."
    ),
]

@pytest.fixture(scope="module")
def dims() -> PackageDims:
    assert PDF.exists(), f"PDF not found: {PDF}"
    return extract_package_dims(PDF)

def test_schema_is_valid(dims):
    assert isinstance(dims, PackageDims)
    assert "PK14-2" in dims.package_type.upper()

def test_values_match_ground_truth(dims):
    assert dims.length.inches.nominal == pytest.approx(0.035, abs=1e-4)
    assert dims.length.inches.tolerance == pytest.approx(0.005, abs=1e-4)
    assert dims.width.inches.max_ == pytest.approx(0.012, abs=1e-4)
    assert dims.height.inches.nominal == pytest.approx(0.004, abs=1e-4)
