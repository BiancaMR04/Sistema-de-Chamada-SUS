"""Tests configuration."""
import pytest
from app import create_app, db
from app.models import Room, Patient, QueueEntry, PriorityType


@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def sample_room(app):
    """Create a sample room."""
    with app.app_context():
        room = Room(name='Sala 1', sector='Clínica Geral')
        db.session.add(room)
        db.session.commit()
        room_id = room.id
    return room_id


@pytest.fixture
def sample_patient(app):
    """Create a sample patient."""
    with app.app_context():
        patient = Patient(
            name='João Silva',
            cpf='12345678901',
            priority_type=PriorityType.NORMAL.value
        )
        db.session.add(patient)
        db.session.commit()
        patient_id = patient.id
    return patient_id
