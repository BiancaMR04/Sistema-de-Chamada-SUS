"""Tests for models."""
import pytest
from datetime import date
from app import db
from app.models import Patient, Room, QueueEntry, PriorityType, CallStatus


def test_patient_initials(app):
    """Test patient initials generation."""
    with app.app_context():
        patient = Patient(name='João da Silva Santos')
        assert patient.get_initials() == 'J.S.'
        
        patient2 = Patient(name='Maria')
        assert patient2.get_initials() == 'M.'


def test_patient_display_name(app):
    """Test patient display name generation."""
    with app.app_context():
        patient = Patient(name='João da Silva Santos')
        assert patient.get_display_name() == 'João S.'
        
        patient2 = Patient(name='Maria')
        assert patient2.get_display_name() == 'Maria'


def test_patient_priority_weight(app):
    """Test priority weight calculation."""
    with app.app_context():
        # Normal priority
        patient1 = Patient(name='Test', priority_type=PriorityType.NORMAL.value)
        assert patient1.get_priority_weight() == 0
        
        # Elderly 80+ (highest)
        patient2 = Patient(name='Test', priority_type=PriorityType.IDOSO_80.value)
        assert patient2.get_priority_weight() == 100
        
        # Pregnant
        patient3 = Patient(name='Test', priority_type=PriorityType.GESTANTE.value)
        assert patient3.get_priority_weight() == 60


def test_room_to_dict(app):
    """Test room serialization."""
    with app.app_context():
        room = Room(name='Sala 1', sector='Triagem')
        db.session.add(room)
        db.session.commit()
        
        data = room.to_dict()
        assert data['name'] == 'Sala 1'
        assert data['sector'] == 'Triagem'
        assert data['is_active'] is True


def test_queue_entry_to_dict(app, sample_room, sample_patient):
    """Test queue entry serialization."""
    with app.app_context():
        room = Room.query.get(sample_room)
        patient = Patient.query.get(sample_patient)
        
        entry = QueueEntry(
            patient_id=sample_patient,
            room_id=sample_room,
            ticket_number='A001',
            position=1,
            priority_type=patient.priority_type,
            status=CallStatus.WAITING.value
        )
        db.session.add(entry)
        db.session.commit()
        
        data = entry.to_dict()
        assert data['ticket_number'] == 'A001'
        assert data['position'] == 1
        assert data['status'] == 'WAITING'
        assert data['room_name'] == room.name
