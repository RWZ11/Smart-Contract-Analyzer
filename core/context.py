from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class AnalysisContext:
    content: str
    filename: str
    lines: List[str]
    ast: Optional[Dict[str, Any]] = None
    ir: Optional[Dict[str, Any]] = None

