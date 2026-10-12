import re
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

import pdfplumber

from .dimensions import dims_to_rows, missing_rows, resolve_dimensions
from .models import AttrRow

@dataclass
class PdfDocument:
    path: Path
    text: str

class Manufacturer(Enum):
    Unkown = 0
    McMasterCarr = 1
    SemiGen = 2

def load_pdf(path: Path) -> PdfDocument:
    path = Path(path)

    if not path.is_file():
        raise FileNotFoundError(path)

    with pdfplumber.open(path) as pdf:
        text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    if not text.strip():
        raise ValueError(f"No extractable text in {path.name}")

    return PdfDocument(path, text)

def detect_manufacturer(doc: PdfDocument) -> Manufacturer:
    if re.search(r"McMaster-Carr", doc.text, re.I):
        return Manufacturer.McMasterCarr

    if re.search(r"SemiGen", doc.text, re.I):
        return Manufacturer.SemiGen

    return Manufacturer.Unkown

def detect_mpn(doc: PdfDocument) -> str | None:
    # McMaster product-page PDF
    match = re.search(
        r"mcmaster\.com/([0-9]{4,5}[A-Z][0-9]{2,4})",
        doc.text,
        re.I,
    )
    if match:
        return match.group(1).upper()

    # SemiGen family datasheet: several MPNs may be present
    return None

def _row(attr, val=None, unit="", src="PDF") -> AttrRow:
    """ Shortcut for AttrRow creation """
    return AttrRow(
        attribute=attr,
        value=val,
        unit=unit,
        source=src
    )

def _number_or_text(val: str) -> float | str:
    val = val.strip()

    try:
        return float(val)
    except ValueError:
        return val

def _mcmaster_value(text: str, label: str) -> str | None:
    # labels might be slpit across lines
    text = re.sub(r"Head\s*\n\s*Diameter", "Head Diameter", text)

    pattern = rf"(?im)^\s*{re.escape(label)}\s+(.+?)\s*$"
    match_ = re.search(pattern, text)

    return match_.group(1).strip() if match_ else None

def extract_mcmaster(doc: PdfDocument) -> tuple[list[AttrRow], list[AttrRow], list[str]]:
    specs = [
        ("Head Type", "Fastener Head Type", ""),
        ("Material", "Material", ""),
        ("RoHS Compliance", "RoHS Compliance", ""),
        ("Length", "Length", "in"),
        ("Head Diameter", "Head Diameter", "in"),
    ]

    set1: list[AttrRow]
    set2: list[AttrRow]
    warnings: list[str]

    set1, set2, warnings = [], [], []

    for attribute, label, unit in specs:
        raw = _mcmaster_value(doc.text, label)

        if raw is None:
            warnings.append(f"{attribute} not found")
            row = _row(attribute)

        else:
            # preserve fractions like x/y
            val = raw.rstrip('"').strip()
            val = _number_or_text(val)

            if unit == "in" and isinstance(val, str):
                # fractional measurement remains str
                pass

            row = _row(attribute, val, unit, "product page")

        (set2 if attribute in ("Length", "Head Diameter") else set1).append(row)

    return set1, set2, warnings

def extract_semigen(doc: PdfDocument, mpn: str, use_vision=False) -> tuple[list[AttrRow], list[AttrRow], list[str]]:
    # The available-parts table has six whitespace-separated columns.
    row_pattern = re.compile(
        rf"(?m)^\s*{re.escape(mpn)}\s+"
        r"([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+"
        r"([\d.]+)\s+(\S+)\s*$",
        re.I,
    )
    match = row_pattern.search(doc.text)

    if not match:
        raise ValueError(f"MPN {mpn} not found in {doc.path.name}")

    capacitance, voltage, current, _, package = match.groups()

    set1: list[AttrRow] = [
        _row("Capacitance", float(capacitance), "pF", "parts table"),
        _row("Voltage", float(voltage), "V", "parts table"),
        _row("Current", float(current), "uA", "parts table"),
    ]

    dims, source, warnings = resolve_dimensions(
        package, doc.path, use_vision
    )

    if dims:
        set2 = dims_to_rows(dims, source)
    else:
        set2 = missing_rows(package)
        warnings.append(f"No dimensions available for package {package}")

    return set1, set2, warnings

def extract(doc: PdfDocument, mpn=None, use_vision=False):
    manufacturer = detect_manufacturer(doc)

    if manufacturer == Manufacturer.McMasterCarr:
        detected = detect_mpn(doc)

        if mpn and detected and mpn.upper() != detected:
            raise ValueError("An MPN is required for the SemiGen datasheet")

        return extract_mcmaster(doc)

    if manufacturer == Manufacturer.SemiGen:
        if not mpn:
            raise ValueError("An MPN is required for the SemiGen datasheet")

        return extract_semigen(doc, mpn, use_vision)

    raise ValueError(f"Unsupported PDF format: {doc.path.name}")