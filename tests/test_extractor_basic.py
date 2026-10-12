from pathlib import Path
import pytest

from poc.extractors import load_pdf, extract


@pytest.mark.parametrize(
    ("filename", "mpn"),
    [
        ("Component_Datasheet_1.pdf", "SBC50-4-14-2"),
        ("Component_Datasheet_2.pdf", "91864A002"),
    ],
)

def test_extract_datasheet(filename, mpn):
    pdf_path = Path(__file__).parent.parent / "data" /filename

    doc = load_pdf(pdf_path)
    set1, set2, warnings = extract(doc, mpn, use_vision=False)

    assert set1, "Attribute Set 1 should not be empty"
    assert set2, "Attribute Set 2 should not be empty"

    print("\nSet 1:", [row.model_dump() for row in set1])
    print("Set 2:", [row.model_dump() for row in set2])
    print("Warnings:", warnings)
