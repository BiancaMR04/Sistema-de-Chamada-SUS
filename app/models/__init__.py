"""Models package."""
from app.models.models import (
    PriorityType,
    CallStatus,
    Room,
    Patient,
    QueueEntry,
    CallHistory,
    AbsenceRecord
)

__all__ = [
    'PriorityType',
    'CallStatus',
    'Room',
    'Patient',
    'QueueEntry',
    'CallHistory',
    'AbsenceRecord'
]
