"""Tests for API endpoints."""
import json
import pytest


def test_index_route(client):
    """Test home page loads."""
    response = client.get('/')
    assert response.status_code == 200


def test_list_rooms_empty(client):
    """Test listing rooms when empty."""
    response = client.get('/api/rooms')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)


def test_create_room(client):
    """Test creating a room."""
    response = client.post('/api/rooms', 
        data=json.dumps({'name': 'Sala 1', 'sector': 'Triagem'}),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Sala 1'
    assert data['sector'] == 'Triagem'


def test_create_room_missing_fields(client):
    """Test creating room with missing fields."""
    response = client.post('/api/rooms',
        data=json.dumps({'name': 'Sala 1'}),
        content_type='application/json'
    )
    assert response.status_code == 400


def test_list_priorities(client):
    """Test listing priority types."""
    response = client.get('/api/priorities')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert len(data) == 8  # 8 priority types


def test_create_offline_patient(client):
    """Test creating an offline patient."""
    response = client.post('/api/patients/offline',
        data=json.dumps({
            'name': 'Maria Santos',
            'cpf': '98765432101',
            'priority_type': 'GESTANTE'
        }),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['name'] == 'Maria Santos'
    assert data['priority_type'] == 'GESTANTE'
    assert data['is_offline'] is True


def test_create_offline_patient_missing_name(client):
    """Test creating offline patient without name."""
    response = client.post('/api/patients/offline',
        data=json.dumps({'cpf': '12345678901'}),
        content_type='application/json'
    )
    assert response.status_code == 400


def test_add_to_queue(client, sample_room, sample_patient):
    """Test adding patient to queue."""
    response = client.post(f'/api/queue/{sample_room}/add',
        data=json.dumps({'patient_id': sample_patient}),
        content_type='application/json'
    )
    assert response.status_code == 201
    data = json.loads(response.data)
    assert data['room_id'] == sample_room
    assert data['patient_id'] == sample_patient
    assert data['status'] == 'WAITING'
    assert data['position'] == 1


def test_add_to_queue_invalid_patient(client, sample_room):
    """Test adding invalid patient to queue."""
    response = client.post(f'/api/queue/{sample_room}/add',
        data=json.dumps({'patient_id': 9999}),
        content_type='application/json'
    )
    assert response.status_code == 400


def test_call_next_empty_queue(client, sample_room):
    """Test calling next when queue is empty."""
    response = client.post(f'/api/queue/call/next/{sample_room}')
    assert response.status_code == 404


def test_call_next(client, sample_room, sample_patient):
    """Test calling next patient."""
    # Add patient to queue
    client.post(f'/api/queue/{sample_room}/add',
        data=json.dumps({'patient_id': sample_patient}),
        content_type='application/json'
    )
    
    # Call next
    response = client.post(f'/api/queue/call/next/{sample_room}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'CALLED'


def test_mark_attended(client, sample_room, sample_patient):
    """Test marking patient as attended."""
    # Add patient to queue
    add_response = client.post(f'/api/queue/{sample_room}/add',
        data=json.dumps({'patient_id': sample_patient}),
        content_type='application/json'
    )
    entry_id = json.loads(add_response.data)['id']
    
    # Call patient
    client.post(f'/api/queue/call/{entry_id}')
    
    # Mark attended
    response = client.post(f'/api/queue/attend/{entry_id}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'ATTENDED'


def test_mark_absent(client, sample_room, sample_patient):
    """Test marking patient as absent."""
    # Add patient to queue
    add_response = client.post(f'/api/queue/{sample_room}/add',
        data=json.dumps({'patient_id': sample_patient}),
        content_type='application/json'
    )
    entry_id = json.loads(add_response.data)['id']
    
    # Call patient
    client.post(f'/api/queue/call/{entry_id}')
    
    # Mark absent
    response = client.post(f'/api/queue/absent/{entry_id}',
        data=json.dumps({'notes': 'Paciente não compareceu'}),
        content_type='application/json'
    )
    assert response.status_code == 200


def test_display_data(client, sample_room):
    """Test getting display data."""
    response = client.get(f'/api/display/{sample_room}')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'current_call' in data
    assert 'last_calls' in data
    assert 'waiting_count' in data


def test_daily_report(client):
    """Test daily report."""
    response = client.get('/api/reports/daily')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'total_patients' in data
    assert 'attended' in data
    assert 'absent' in data


def test_esus_status(client):
    """Test e-SUS status endpoint."""
    response = client.get('/api/esus/status')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'connected' in data
    assert 'mode' in data
