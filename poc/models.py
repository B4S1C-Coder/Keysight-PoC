from typing import Optional
from pydantic import BaseModel

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
