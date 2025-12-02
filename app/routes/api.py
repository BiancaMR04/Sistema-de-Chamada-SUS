"""
API routes for Sistema de Chamada SUS.
"""
from datetime import datetime
from flask import Blueprint, request, jsonify

from app import db, socketio
from app.models import (
    Patient, Room, QueueEntry, CallHistory, AbsenceRecord,
    PriorityType, CallStatus
)
from app.services import QueueService, ESUSService, ReportService

api_bp = Blueprint('api', __name__)


# ============== Patient Endpoints ==============

@api_bp.route('/patients', methods=['GET'])
def list_patients():
    """List all patients."""
    patients = Patient.query.order_by(Patient.name).all()
    return jsonify([p.to_dict() for p in patients])


@api_bp.route('/patients/<int:patient_id>', methods=['GET'])
def get_patient(patient_id):
    """Get a specific patient."""
    patient = Patient.query.get_or_404(patient_id)
    return jsonify(patient.to_dict())


@api_bp.route('/patients/search', methods=['GET'])
def search_patient():
    """Search for a patient by CPF or name in e-SUS or local database."""
    cpf = request.args.get('cpf')
    name = request.args.get('name')
    
    # First try local database
    if cpf:
        patient = Patient.query.filter_by(cpf=cpf).first()
        if patient:
            return jsonify({
                'found': True,
                'source': 'local',
                'patient': patient.to_dict()
            })
    
    # Try e-SUS API
    esus_data = ESUSService.search_patient(cpf=cpf)
    if esus_data:
        # Sync with local database
        patient = ESUSService.sync_patient(esus_data)
        return jsonify({
            'found': True,
            'source': 'esus',
            'patient': patient.to_dict()
        })
    
    # Search by name in local database
    if name:
        patients = Patient.query.filter(
            Patient.name.ilike(f'%{name}%')
        ).limit(10).all()
        if patients:
            return jsonify({
                'found': True,
                'source': 'local',
                'patients': [p.to_dict() for p in patients]
            })
    
    return jsonify({'found': False})


@api_bp.route('/patients/offline', methods=['POST'])
def create_offline_patient():
    """Create a patient manually (offline mode)."""
    data = request.get_json()
    
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    
    patient = ESUSService.get_or_create_offline_patient(
        name=name,
        cpf=data.get('cpf'),
        priority_type=data.get('priority_type', PriorityType.NORMAL.value),
        birth_date=data.get('birth_date')
    )
    
    return jsonify(patient.to_dict()), 201


@api_bp.route('/patients/<int:patient_id>/priority', methods=['PUT'])
def update_patient_priority(patient_id):
    """Update patient priority."""
    patient = Patient.query.get_or_404(patient_id)
    data = request.get_json()
    
    priority_type = data.get('priority_type')
    if priority_type and priority_type in [p.value for p in PriorityType]:
        patient.priority_type = priority_type
        db.session.commit()
        return jsonify(patient.to_dict())
    
    return jsonify({'error': 'Invalid priority type'}), 400


# ============== Room Endpoints ==============

@api_bp.route('/rooms', methods=['GET'])
def list_rooms():
    """List all rooms."""
    active_only = request.args.get('active', 'true').lower() == 'true'
    query = Room.query
    if active_only:
        query = query.filter_by(is_active=True)
    rooms = query.order_by(Room.sector, Room.name).all()
    return jsonify([r.to_dict() for r in rooms])


@api_bp.route('/rooms/<int:room_id>', methods=['GET'])
def get_room(room_id):
    """Get a specific room."""
    room = Room.query.get_or_404(room_id)
    return jsonify(room.to_dict())


@api_bp.route('/rooms', methods=['POST'])
def create_room():
    """Create a new room."""
    data = request.get_json()
    
    name = data.get('name')
    sector = data.get('sector')
    
    if not name or not sector:
        return jsonify({'error': 'Name and sector are required'}), 400
    
    room = Room(name=name, sector=sector)
    db.session.add(room)
    db.session.commit()
    
    return jsonify(room.to_dict()), 201


@api_bp.route('/rooms/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    """Update a room."""
    room = Room.query.get_or_404(room_id)
    data = request.get_json()
    
    if 'name' in data:
        room.name = data['name']
    if 'sector' in data:
        room.sector = data['sector']
    if 'is_active' in data:
        room.is_active = data['is_active']
    
    db.session.commit()
    return jsonify(room.to_dict())


# ============== Queue Endpoints ==============

@api_bp.route('/queue/<int:room_id>', methods=['GET'])
def get_queue(room_id):
    """Get queue for a room."""
    status = request.args.get('status')
    queue = QueueService.get_queue(room_id, status)
    return jsonify(queue)


@api_bp.route('/queue/<int:room_id>/add', methods=['POST'])
def add_to_queue(room_id):
    """Add a patient to the queue."""
    data = request.get_json()
    patient_id = data.get('patient_id')
    priority_type = data.get('priority_type')
    
    if not patient_id:
        return jsonify({'error': 'patient_id is required'}), 400
    
    try:
        entry = QueueService.add_to_queue(patient_id, room_id, priority_type)
        
        # Emit real-time update
        socketio.emit('queue_update', {
            'room_id': room_id,
            'action': 'added',
            'entry': entry.to_dict()
        }, room=f'room_{room_id}')
        
        return jsonify(entry.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@api_bp.route('/queue/call/next/<int:room_id>', methods=['POST'])
def call_next(room_id):
    """Call the next patient in the queue."""
    entry = QueueService.call_next(room_id)
    
    if not entry:
        return jsonify({'error': 'No patients waiting'}), 404
    
    # Emit real-time update with call notification
    socketio.emit('patient_called', {
        'room_id': room_id,
        'entry': entry.to_dict(),
        'play_audio': True
    }, room=f'room_{room_id}')
    
    # Also emit queue update
    socketio.emit('queue_update', {
        'room_id': room_id,
        'action': 'called',
        'entry': entry.to_dict()
    }, room=f'room_{room_id}')
    
    return jsonify(entry.to_dict())


@api_bp.route('/queue/call/<int:entry_id>', methods=['POST'])
def call_patient(entry_id):
    """Call a specific patient."""
    entry = QueueService.call_patient(entry_id)
    
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    
    # Emit real-time update
    socketio.emit('patient_called', {
        'room_id': entry.room_id,
        'entry': entry.to_dict(),
        'play_audio': True
    }, room=f'room_{entry.room_id}')
    
    socketio.emit('queue_update', {
        'room_id': entry.room_id,
        'action': 'called',
        'entry': entry.to_dict()
    }, room=f'room_{entry.room_id}')
    
    return jsonify(entry.to_dict())


@api_bp.route('/queue/recall/<int:entry_id>', methods=['POST'])
def recall_patient(entry_id):
    """Recall a patient (call again)."""
    entry = QueueService.recall_patient(entry_id)
    
    if not entry:
        return jsonify({'error': 'Entry not found or not in CALLED status'}), 404
    
    # Emit real-time update
    socketio.emit('patient_called', {
        'room_id': entry.room_id,
        'entry': entry.to_dict(),
        'play_audio': True,
        'is_recall': True
    }, room=f'room_{entry.room_id}')
    
    return jsonify(entry.to_dict())


@api_bp.route('/queue/attend/<int:entry_id>', methods=['POST'])
def mark_attended(entry_id):
    """Mark a patient as attended."""
    entry = QueueService.mark_attended(entry_id)
    
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    
    # Emit real-time update
    socketio.emit('queue_update', {
        'room_id': entry.room_id,
        'action': 'attended',
        'entry': entry.to_dict()
    }, room=f'room_{entry.room_id}')
    
    return jsonify(entry.to_dict())


@api_bp.route('/queue/absent/<int:entry_id>', methods=['POST'])
def mark_absent(entry_id):
    """Mark a patient as absent."""
    data = request.get_json() or {}
    notes = data.get('notes')
    
    absence = QueueService.mark_absent(entry_id, notes)
    
    if not absence:
        return jsonify({'error': 'Entry not found'}), 404
    
    # Emit real-time update
    socketio.emit('queue_update', {
        'room_id': absence.room_id,
        'action': 'absent',
        'absence': absence.to_dict()
    }, room=f'room_{absence.room_id}')
    
    return jsonify(absence.to_dict())


@api_bp.route('/queue/cancel/<int:entry_id>', methods=['POST'])
def cancel_entry(entry_id):
    """Cancel a queue entry."""
    entry = QueueService.cancel_entry(entry_id)
    
    if not entry:
        return jsonify({'error': 'Entry not found'}), 404
    
    # Emit real-time update
    socketio.emit('queue_update', {
        'room_id': entry.room_id,
        'action': 'cancelled',
        'entry': entry.to_dict()
    }, room=f'room_{entry.room_id}')
    
    return jsonify(entry.to_dict())


# ============== Display Endpoints ==============

@api_bp.route('/display/<int:room_id>', methods=['GET'])
def get_display_data(room_id):
    """Get data for display panel."""
    current_call = QueueService.get_current_call(room_id)
    last_calls = QueueService.get_last_calls(room_id, limit=4)
    queue = QueueService.get_queue(room_id, CallStatus.WAITING.value)
    
    return jsonify({
        'room_id': room_id,
        'current_call': current_call,
        'last_calls': last_calls,
        'waiting_count': len(queue),
        'queue': queue[:5]  # First 5 waiting
    })


# ============== Report Endpoints ==============

@api_bp.route('/reports/daily', methods=['GET'])
def daily_report():
    """Get daily summary report."""
    date_str = request.args.get('date')
    room_id = request.args.get('room_id', type=int)
    
    report_date = None
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    report = ReportService.get_daily_summary(report_date, room_id)
    return jsonify(report)


@api_bp.route('/reports/absences', methods=['GET'])
def absence_report():
    """Get absence report."""
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    room_id = request.args.get('room_id', type=int)
    
    start_date = None
    end_date = None
    
    if start_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid start_date format'}), 400
    
    if end_str:
        try:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid end_date format'}), 400
    
    report = ReportService.get_absence_report(start_date, end_date, room_id)
    return jsonify(report)


@api_bp.route('/reports/room/<int:room_id>/performance', methods=['GET'])
def room_performance(room_id):
    """Get room performance report."""
    start_str = request.args.get('start_date')
    end_str = request.args.get('end_date')
    
    start_date = None
    end_date = None
    
    if start_str:
        try:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if end_str:
        try:
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    report = ReportService.get_room_performance(room_id, start_date, end_date)
    return jsonify(report)


@api_bp.route('/reports/hourly', methods=['GET'])
def hourly_distribution():
    """Get hourly distribution report."""
    date_str = request.args.get('date')
    room_id = request.args.get('room_id', type=int)
    
    report_date = None
    if date_str:
        try:
            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format'}), 400
    
    report = ReportService.get_hourly_distribution(report_date, room_id)
    return jsonify(report)


# ============== e-SUS Integration Endpoints ==============

@api_bp.route('/esus/status', methods=['GET'])
def esus_status():
    """Check e-SUS connection status."""
    is_connected = ESUSService.check_connection()
    return jsonify({
        'connected': is_connected,
        'mode': 'online' if is_connected else 'offline'
    })


@api_bp.route('/esus/search', methods=['GET'])
def esus_search():
    """Search patient in e-SUS."""
    cpf = request.args.get('cpf')
    cns = request.args.get('cns')
    
    if not cpf and not cns:
        return jsonify({'error': 'CPF or CNS is required'}), 400
    
    result = ESUSService.search_patient(cpf=cpf, cns=cns)
    
    if result:
        return jsonify({
            'found': True,
            'data': result
        })
    
    return jsonify({'found': False})


# ============== Priority Types Endpoint ==============

@api_bp.route('/priorities', methods=['GET'])
def list_priorities():
    """List all priority types."""
    priorities = [
        {'value': PriorityType.NORMAL.value, 'label': 'Normal', 'weight': 0},
        {'value': PriorityType.CRIANCA.value, 'label': 'Criança com Responsável', 'weight': 40},
        {'value': PriorityType.LACTANTE.value, 'label': 'Lactante', 'weight': 50},
        {'value': PriorityType.GESTANTE.value, 'label': 'Gestante', 'weight': 60},
        {'value': PriorityType.IDOSO_60.value, 'label': 'Idoso (60+)', 'weight': 70},
        {'value': PriorityType.DEFICIENTE.value, 'label': 'Pessoa com Deficiência', 'weight': 80},
        {'value': PriorityType.AUTISTA.value, 'label': 'Pessoa com TEA', 'weight': 90},
        {'value': PriorityType.IDOSO_80.value, 'label': 'Idoso (80+)', 'weight': 100},
    ]
    return jsonify(priorities)
