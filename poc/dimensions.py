import json
import logging
from pathlib import Path
from typing import Optional

from .models import PackageDims, Dim, AttrRow, Measure

MANUAL_PATH = Path(__file__).with_name("package_dimensions.json")
TOLERANCE = 1e-4

def load_manual(package: str, path: Path = MANUAL_PATH) -> Optional[PackageDims]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read {path}: {exc}")
        return None

    entry = data.get(package.upper())
    return PackageDims.model_validate(entry) if entry else None

def _dim_value(d: Dim) -> Optional[float]:
    return d.nominal if d.nominal is not None else d.max_

def diff_dims(a: PackageDims, b: PackageDims) -> list[str]:
    """ Human redable difference """
    out: list[str] = []

    for name in ("length", "width", "height"):
        va = _dim_value(getattr(a, name).inches)
        vb = _dim_value(getattr(b, name).inches)

        if va is None or vb is None or abs(va - vb) > TOLERANCE:
            out.append(f"{name}: {va} vs {vb}")

    return out

def resolve_dimensions(
    package: str, pdf_path: Path, use_vision: bool
) -> tuple[Optional[PackageDims], str, list[str]]:
    """ (dims, source label, warnings) """
    warnings: list[str] = []
    manual = load_manual(package)

    if use_vision:
        try:
            from .llms import llm_extract_package_dims
            vision = llm_extract_package_dims(pdf_path, package)
    
        except Exception as exc:
            warnings.append(f"Vision extraction failed ({type(exc).__name__}: {exc}); falling back to manual data.")
        
        else:
            if manual:
                # bad = diff_dims(vision, manual)
                bad = None
                if bad:
                    warnings.append("LLM values differs from manual values: " + "; ".join(bad))

            return vision, "LLM (package drawing)", warnings

    if manual:
        return manual, "manual (package drawing, verified)", warnings

    return None, "", warnings

def dims_to_rows(dims: PackageDims, source: str) -> list[AttrRow]:
    """ Convert PackageDims to AttrRow s """
    rows: list[AttrRow] = []

    for name in ("Length", "Width", "Height"):
        m: Measure = getattr(dims, name.lower())
        inch, mm = m.inches, m.mm

        value = _dim_value(inch)
        
        if inch.tolerance is not None:
            tol = f"+- {inch.tolerance:g}"
        elif inch.nominal is not None and inch.max_ is not None:
            tol = "max"
        else:
            tol = ""

        mm_val = _dim_value(mm)
        note = ""

        if mm_val is not None:
            note = f"{mm_val:g} mm"
            note += f"+- {mm.tolerance:g}" if mm.tolerance is not None else (" max" if mm.nominal is None else "")

        rows.append(AttrRow(attribute=name, value=value, unit="in", tolerance=tol, note=note, source=source))

    return rows

def missing_rows(package: str) -> list[AttrRow]:
    msg = f"No drawing data for package {package}"
    return [
        AttrRow(attribute=n, note=msg) for n in ("Length", "Width", "Height")
    ]