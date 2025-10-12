from __future__ import annotations
from typing import Protocol, Dict, Any, List, Tuple
from models.events import UnifiedEventResult
from datetime import datetime

class DSLBuilder(Protocol):
    def __call__(
        self,
        question: str,
        companies: List[str],
        event_result: UnifiedEventResult,
        date_range: Tuple[datetime, datetime],
    ) -> Dict[str, Any]: ...
