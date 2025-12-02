"""Tests for queue service."""
import pytest
from app import db
from app.models import Patient, Room, QueueEntry, PriorityType, CallStatus
from app.services import QueueService


def test_generate_ticket_number(app, sample_room):
    """Test ticket number generation."""
    with app.app_context():
        # Normal priority
        ticket = QueueService.generate_ticket_number(sample_room, is_priority=False)
        assert ticket == 'A001'
        
        # Priority
        ticket_p = QueueService.generate_ticket_number(sample_room, is_priority=True)
        assert ticket_p == 'P001'


def test_add_to_queue(app, sample_room, sample_patient):
    """Test adding patient to queue."""
    with app.app_context():
        entry = QueueService.add_to_queue(sample_patient, sample_room)
        
        assert entry.status == CallStatus.WAITING.value
        assert entry.position == 1
        assert entry.ticket_number.startswith('A')


def test_priority_queue_order(app, sample_room):
    """Test that priority patients come first."""
    with app.app_context():
        # Create normal patient
        patient1 = Patient(name='Normal Patient', priority_type=PriorityType.NORMAL.value)
        db.session.add(patient1)
        
        # Create priority patient
        patient2 = Patient(name='Priority Patient', priority_type=PriorityType.IDOSO_80.value)
        db.session.add(patient2)
        db.session.commit()
        
        # Add normal first
        entry1 = QueueService.add_to_queue(patient1.id, sample_room)
        
        # Add priority second
        entry2 = QueueService.add_to_queue(patient2.id, sample_room)
        
        # Priority should be first
        db.session.refresh(entry1)
        db.session.refresh(entry2)
        
        assert entry2.position < entry1.position


def test_call_next(app, sample_room, sample_patient):
    """Test calling next patient."""
    with app.app_context():
        # Add patient
        QueueService.add_to_queue(sample_patient, sample_room)
        
        # Call next
        entry = QueueService.call_next(sample_room)
        
        assert entry is not None
        assert entry.status == CallStatus.CALLED.value
        assert entry.call_count == 1


def test_recall_patient(app, sample_room, sample_patient):
    """Test recalling patient."""
    with app.app_context():
        # Add and call patient
        QueueService.add_to_queue(sample_patient, sample_room)
        entry = QueueService.call_next(sample_room)
        
        # Recall
        entry = QueueService.recall_patient(entry.id)
        
        assert entry.call_count == 2


def test_mark_attended(app, sample_room, sample_patient):
    """Test marking patient as attended."""
    with app.app_context():
        # Add and call patient
        QueueService.add_to_queue(sample_patient, sample_room)
        entry = QueueService.call_next(sample_room)
        
        # Mark attended
        entry = QueueService.mark_attended(entry.id)
        
        assert entry.status == CallStatus.ATTENDED.value
        assert entry.attended_at is not None


def test_mark_absent(app, sample_room, sample_patient):
    """Test marking patient as absent."""
    with app.app_context():
        # Add and call patient
        QueueService.add_to_queue(sample_patient, sample_room)
        entry = QueueService.call_next(sample_room)
        
        # Mark absent
        absence = QueueService.mark_absent(entry.id, notes='Test absence')
        
        assert absence is not None
        assert absence.notes == 'Test absence'


def test_get_last_calls(app, sample_room, sample_patient):
    """Test getting call history."""
    with app.app_context():
        # Add and call patient
        QueueService.add_to_queue(sample_patient, sample_room)
        QueueService.call_next(sample_room)
        
        # Get history
        history = QueueService.get_last_calls(sample_room, limit=4)
        
        assert len(history) == 1
        assert history[0]['room_id'] == sample_room
