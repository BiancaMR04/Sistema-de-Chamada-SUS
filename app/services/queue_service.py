"""
Queue management service for Sistema de Chamada SUS.
"""
from datetime import datetime, date
from typing import Optional

from sqlalchemy import func

from app import db
from app.models import (
    Patient, Room, QueueEntry, CallHistory, 
    AbsenceRecord, CallStatus, PriorityType
)


class QueueService:
    """Service for managing patient queues."""
    
    @staticmethod
    def generate_ticket_number(room_id: int, is_priority: bool = False) -> str:
        """Generate a new ticket number for the day."""
        today = date.today()
        prefix = 'P' if is_priority else 'A'
        
        # Get the last ticket number for today in this room
        last_entry = QueueEntry.query.filter(
            QueueEntry.room_id == room_id,
            QueueEntry.ticket_number.startswith(prefix),
            func.date(QueueEntry.created_at) == today
        ).order_by(QueueEntry.id.desc()).first()
        
        if last_entry:
            # Extract the number and increment
            try:
                last_num = int(last_entry.ticket_number[1:])
                new_num = last_num + 1
            except ValueError:
                new_num = 1
        else:
            new_num = 1
        
        return f"{prefix}{new_num:03d}"
    
    @staticmethod
    def calculate_position(room_id: int, priority_type: str) -> int:
        """Calculate position in queue considering priorities."""
        # Get priority weight
        priority_weights = {
            PriorityType.IDOSO_80.value: 100,
            PriorityType.AUTISTA.value: 90,
            PriorityType.DEFICIENTE.value: 80,
            PriorityType.IDOSO_60.value: 70,
            PriorityType.GESTANTE.value: 60,
            PriorityType.LACTANTE.value: 50,
            PriorityType.CRIANCA.value: 40,
            PriorityType.NORMAL.value: 0
        }
        
        weight = priority_weights.get(priority_type, 0)
        
        # Count entries with higher or equal priority that are waiting
        waiting_entries = QueueEntry.query.filter(
            QueueEntry.room_id == room_id,
            QueueEntry.status == CallStatus.WAITING.value
        ).all()
        
        # Calculate position based on priority
        position = 1
        for entry in waiting_entries:
            entry_weight = priority_weights.get(entry.priority_type, 0)
            if entry_weight >= weight:
                position += 1
        
        return position
    
    @staticmethod
    def add_to_queue(patient_id: int, room_id: int, priority_type: Optional[str] = None) -> QueueEntry:
        """Add a patient to the queue."""
        patient = Patient.query.get(patient_id)
        if not patient:
            raise ValueError("Patient not found")
        
        room = Room.query.get(room_id)
        if not room:
            raise ValueError("Room not found")
        
        # Use patient's priority if not specified
        if not priority_type:
            priority_type = patient.priority_type
        
        is_priority = priority_type != PriorityType.NORMAL.value
        ticket_number = QueueService.generate_ticket_number(room_id, is_priority)
        position = QueueService.calculate_position(room_id, priority_type)
        
        entry = QueueEntry(
            patient_id=patient_id,
            room_id=room_id,
            ticket_number=ticket_number,
            position=position,
            priority_type=priority_type,
            status=CallStatus.WAITING.value
        )
        
        db.session.add(entry)
        db.session.commit()
        
        # Recalculate positions for all waiting entries
        QueueService.recalculate_positions(room_id)
        
        return entry
    
    @staticmethod
    def recalculate_positions(room_id: int):
        """Recalculate positions for all waiting entries in a room."""
        priority_weights = {
            PriorityType.IDOSO_80.value: 100,
            PriorityType.AUTISTA.value: 90,
            PriorityType.DEFICIENTE.value: 80,
            PriorityType.IDOSO_60.value: 70,
            PriorityType.GESTANTE.value: 60,
            PriorityType.LACTANTE.value: 50,
            PriorityType.CRIANCA.value: 40,
            PriorityType.NORMAL.value: 0
        }
        
        waiting_entries = QueueEntry.query.filter(
            QueueEntry.room_id == room_id,
            QueueEntry.status == CallStatus.WAITING.value
        ).all()
        
        # Sort by priority (desc) and then by creation time (asc)
        waiting_entries.sort(
            key=lambda x: (
                -priority_weights.get(x.priority_type, 0),
                x.created_at
            )
        )
        
        for i, entry in enumerate(waiting_entries, 1):
            entry.position = i
        
        db.session.commit()
    
    @staticmethod
    def call_next(room_id: int) -> Optional[QueueEntry]:
        """Call the next patient in the queue."""
        priority_weights = {
            PriorityType.IDOSO_80.value: 100,
            PriorityType.AUTISTA.value: 90,
            PriorityType.DEFICIENTE.value: 80,
            PriorityType.IDOSO_60.value: 70,
            PriorityType.GESTANTE.value: 60,
            PriorityType.LACTANTE.value: 50,
            PriorityType.CRIANCA.value: 40,
            PriorityType.NORMAL.value: 0
        }
        
        # Get all waiting entries
        waiting_entries = QueueEntry.query.filter(
            QueueEntry.room_id == room_id,
            QueueEntry.status == CallStatus.WAITING.value
        ).all()
        
        if not waiting_entries:
            return None
        
        # Sort and get the first one
        waiting_entries.sort(
            key=lambda x: (
                -priority_weights.get(x.priority_type, 0),
                x.created_at
            )
        )
        
        entry = waiting_entries[0]
        return QueueService.call_patient(entry.id)
    
    @staticmethod
    def call_patient(queue_entry_id: int) -> Optional[QueueEntry]:
        """Call a specific patient."""
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry:
            return None
        
        entry.status = CallStatus.CALLED.value
        entry.called_at = datetime.utcnow()
        entry.call_count += 1
        
        # Create call history entry
        history = CallHistory(
            queue_entry_id=entry.id,
            room_id=entry.room_id,
            ticket_number=entry.ticket_number,
            patient_display_name=entry.patient.get_display_name(),
            called_at=datetime.utcnow()
        )
        db.session.add(history)
        db.session.commit()
        
        # Recalculate positions
        QueueService.recalculate_positions(entry.room_id)
        
        return entry
    
    @staticmethod
    def recall_patient(queue_entry_id: int) -> Optional[QueueEntry]:
        """Recall a patient (call again)."""
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry or entry.status != CallStatus.CALLED.value:
            return None
        
        entry.call_count += 1
        entry.called_at = datetime.utcnow()
        
        # Create another history entry
        history = CallHistory(
            queue_entry_id=entry.id,
            room_id=entry.room_id,
            ticket_number=entry.ticket_number,
            patient_display_name=entry.patient.get_display_name(),
            called_at=datetime.utcnow()
        )
        db.session.add(history)
        db.session.commit()
        
        return entry
    
    @staticmethod
    def mark_attended(queue_entry_id: int) -> Optional[QueueEntry]:
        """Mark a patient as attended."""
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry:
            return None
        
        entry.status = CallStatus.ATTENDED.value
        entry.attended_at = datetime.utcnow()
        db.session.commit()
        
        return entry
    
    @staticmethod
    def mark_absent(queue_entry_id: int, notes: Optional[str] = None) -> Optional[AbsenceRecord]:
        """Mark a patient as absent and create absence record."""
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry:
            return None
        
        entry.status = CallStatus.ABSENT.value
        entry.notes = notes
        
        # Create absence record
        absence = AbsenceRecord(
            patient_id=entry.patient_id,
            queue_entry_id=entry.id,
            room_id=entry.room_id,
            call_count=entry.call_count,
            notes=notes
        )
        db.session.add(absence)
        db.session.commit()
        
        # Recalculate positions
        QueueService.recalculate_positions(entry.room_id)
        
        return absence
    
    @staticmethod
    def cancel_entry(queue_entry_id: int) -> Optional[QueueEntry]:
        """Cancel a queue entry."""
        entry = QueueEntry.query.get(queue_entry_id)
        if not entry:
            return None
        
        entry.status = CallStatus.CANCELLED.value
        db.session.commit()
        
        # Recalculate positions
        QueueService.recalculate_positions(entry.room_id)
        
        return entry
    
    @staticmethod
    def get_queue(room_id: int, status: Optional[str] = None) -> list:
        """Get queue entries for a room."""
        query = QueueEntry.query.filter(QueueEntry.room_id == room_id)
        
        if status:
            query = query.filter(QueueEntry.status == status)
        else:
            # By default, show waiting and called
            query = query.filter(
                QueueEntry.status.in_([
                    CallStatus.WAITING.value,
                    CallStatus.CALLED.value
                ])
            )
        
        entries = query.order_by(QueueEntry.position).all()
        return [entry.to_dict() for entry in entries]
    
    @staticmethod
    def get_last_calls(room_id: int, limit: int = 4) -> list:
        """Get the last N calls for a room (for display panel)."""
        history = CallHistory.query.filter(
            CallHistory.room_id == room_id
        ).order_by(CallHistory.called_at.desc()).limit(limit).all()
        
        return [h.to_dict() for h in history]
    
    @staticmethod
    def get_current_call(room_id: int) -> Optional[dict]:
        """Get the currently called patient for a room."""
        entry = QueueEntry.query.filter(
            QueueEntry.room_id == room_id,
            QueueEntry.status == CallStatus.CALLED.value
        ).order_by(QueueEntry.called_at.desc()).first()
        
        return entry.to_dict() if entry else None
