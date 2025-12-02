"""
Database models for Sistema de Chamada SUS.
"""
from datetime import datetime
from enum import Enum

from app import db


class PriorityType(str, Enum):
    """Priority types based on Brazilian law (Lei 10.048/2000)."""
    NORMAL = 'NORMAL'
    IDOSO_60 = 'IDOSO_60'  # Elderly 60+
    IDOSO_80 = 'IDOSO_80'  # Elderly 80+ (super priority)
    GESTANTE = 'GESTANTE'  # Pregnant
    LACTANTE = 'LACTANTE'  # Breastfeeding
    DEFICIENTE = 'DEFICIENTE'  # Person with disability
    CRIANCA = 'CRIANCA'  # Child with caregiver
    AUTISTA = 'AUTISTA'  # Person with autism


class CallStatus(str, Enum):
    """Call status types."""
    WAITING = 'WAITING'
    CALLED = 'CALLED'
    ATTENDED = 'ATTENDED'
    ABSENT = 'ABSENT'
    CANCELLED = 'CANCELLED'


class Room(db.Model):
    """Room/Sector model for organizing queues."""
    __tablename__ = 'rooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    queue_entries = db.relationship('QueueEntry', backref='room', lazy='dynamic')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'sector': self.sector,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Patient(db.Model):
    """Patient model with e-SUS integration support."""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    esus_id = db.Column(db.String(50), unique=True, nullable=True)  # e-SUS integration ID
    name = db.Column(db.String(200), nullable=False)
    cpf = db.Column(db.String(11), unique=True, nullable=True)
    birth_date = db.Column(db.Date, nullable=True)
    priority_type = db.Column(db.String(20), default=PriorityType.NORMAL.value)
    is_offline = db.Column(db.Boolean, default=False)  # Manual registration (offline mode)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    queue_entries = db.relationship('QueueEntry', backref='patient', lazy='dynamic')
    
    def get_initials(self):
        """Get patient initials for privacy display."""
        parts = self.name.split()
        if len(parts) >= 2:
            return f"{parts[0][0]}.{parts[-1][0]}."
        elif parts:
            return f"{parts[0][0]}."
        return ""
    
    def get_display_name(self):
        """Get display name with privacy (first name + last initial)."""
        parts = self.name.split()
        if len(parts) >= 2:
            return f"{parts[0]} {parts[-1][0]}."
        return self.name
    
    def get_priority_weight(self):
        """Get priority weight for sorting (higher = more priority)."""
        weights = {
            PriorityType.IDOSO_80.value: 100,  # Super priority
            PriorityType.AUTISTA.value: 90,
            PriorityType.DEFICIENTE.value: 80,
            PriorityType.IDOSO_60.value: 70,
            PriorityType.GESTANTE.value: 60,
            PriorityType.LACTANTE.value: 50,
            PriorityType.CRIANCA.value: 40,
            PriorityType.NORMAL.value: 0
        }
        return weights.get(self.priority_type, 0)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'esus_id': self.esus_id,
            'name': self.name,
            'display_name': self.get_display_name(),
            'initials': self.get_initials(),
            'cpf': self.cpf,
            'birth_date': self.birth_date.isoformat() if self.birth_date else None,
            'priority_type': self.priority_type,
            'is_offline': self.is_offline,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class QueueEntry(db.Model):
    """Queue entry model for managing patient calls."""
    __tablename__ = 'queue_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    ticket_number = db.Column(db.String(20), nullable=False)  # e.g., "A001", "P015"
    position = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default=CallStatus.WAITING.value)
    priority_type = db.Column(db.String(20), nullable=False)
    call_count = db.Column(db.Integer, default=0)  # Number of times called
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    called_at = db.Column(db.DateTime, nullable=True)
    attended_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.get_display_name() if self.patient else None,
            'patient_initials': self.patient.get_initials() if self.patient else None,
            'room_id': self.room_id,
            'room_name': self.room.name if self.room else None,
            'sector': self.room.sector if self.room else None,
            'ticket_number': self.ticket_number,
            'position': self.position,
            'status': self.status,
            'priority_type': self.priority_type,
            'call_count': self.call_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'called_at': self.called_at.isoformat() if self.called_at else None,
            'attended_at': self.attended_at.isoformat() if self.attended_at else None,
            'notes': self.notes
        }


class CallHistory(db.Model):
    """Call history for tracking and displaying last calls."""
    __tablename__ = 'call_history'
    
    id = db.Column(db.Integer, primary_key=True)
    queue_entry_id = db.Column(db.Integer, db.ForeignKey('queue_entries.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    ticket_number = db.Column(db.String(20), nullable=False)
    patient_display_name = db.Column(db.String(200), nullable=False)
    called_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    queue_entry = db.relationship('QueueEntry', backref='history_entries')
    room = db.relationship('Room', backref='call_history')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'queue_entry_id': self.queue_entry_id,
            'room_id': self.room_id,
            'room_name': self.room.name if self.room else None,
            'ticket_number': self.ticket_number,
            'patient_display_name': self.patient_display_name,
            'called_at': self.called_at.isoformat() if self.called_at else None
        }


class AbsenceRecord(db.Model):
    """Absence tracking for reporting."""
    __tablename__ = 'absence_records'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    queue_entry_id = db.Column(db.Integer, db.ForeignKey('queue_entries.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    call_count = db.Column(db.Integer, default=1)  # How many times called before marked absent
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    patient = db.relationship('Patient', backref='absence_records')
    queue_entry = db.relationship('QueueEntry', backref='absence_record')
    room = db.relationship('Room', backref='absence_records')
    
    def to_dict(self):
        """Convert to dictionary."""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'patient_name': self.patient.get_display_name() if self.patient else None,
            'queue_entry_id': self.queue_entry_id,
            'room_id': self.room_id,
            'room_name': self.room.name if self.room else None,
            'recorded_at': self.recorded_at.isoformat() if self.recorded_at else None,
            'call_count': self.call_count,
            'notes': self.notes
        }
