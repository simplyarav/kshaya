from pydantic import BaseModel
from abc import ABC, abstractmethod

class CarvedCandidate(BaseModel):
    format_name: str
    offset: int
    length: int
    signature_confidence: float
    structure_pass: bool
    structure_details: str
    is_executable_risk: bool = False

class BaseCarver(ABC):
    @abstractmethod
    def carve(self, data: bytes, offset: int) -> CarvedCandidate:
        pass
