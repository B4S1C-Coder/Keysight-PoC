from typing import Optional, Union
from pydantic import BaseModel, Field

class Dim(BaseModel):
    nominal: Optional[float] = None
    tolerance: Optional[float] = None
    max_: Optional[float] = None

class Measure(BaseModel):
    inches: Dim
    mm: Dim

class PackageDims(BaseModel):
    package_type: str
    length: Measure
    width: Measure
    height: Measure

class AttrRow(BaseModel):
    attribute: str
    value: Optional[Union[float, str]] = None
    unit: str = ""
    tolerance: str = ""
    note: str = ""
    source: str = ""

class ExtractionResult(BaseModel):
    mpn: str
    manufacturer: str
    source_pdf: str
    set1: list[AttrRow]
    set2: list[AttrRow]
    warnings: list[str] = Field(default_factory=list)