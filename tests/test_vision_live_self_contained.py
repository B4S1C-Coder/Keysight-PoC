from dotenv import load_dotenv
load_dotenv()

import os
from pathlib import Path

import pytest
from poc import PackageDims, llm_extract_package_dims

MODEL = os.getenv("GEMINI_MODEL", "")

PDF = Path(__file__).parent.parent / "data" / "Component_Datasheet_1.pdf"

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
    return llm_extract_package_dims(PDF, "PK14-2")

def test_schema_is_valid(dims):
    assert isinstance(dims, PackageDims)
    assert "PK14-2" in dims.package_type.upper()

def test_values_match_ground_truth(dims):
    assert dims.length.inches.nominal == pytest.approx(0.035, abs=1e-4)
    assert dims.length.inches.tolerance == pytest.approx(0.005, abs=1e-4)
    assert dims.width.inches.max_ == pytest.approx(0.012, abs=1e-4)
    assert dims.height.inches.nominal == pytest.approx(0.004, abs=1e-4)
