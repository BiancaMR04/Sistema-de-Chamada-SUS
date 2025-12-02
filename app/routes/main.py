"""
Main routes for display panels.
"""
from flask import Blueprint, render_template, request

from app.models import Room

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page with links to panels."""
    rooms = Room.query.filter_by(is_active=True).all()
    return render_template('index.html', rooms=rooms)


@main_bp.route('/panel/<int:room_id>')
def display_panel(room_id):
    """Display panel for a specific room."""
    room = Room.query.get_or_404(room_id)
    return render_template('panel.html', room=room)


@main_bp.route('/reception')
def reception():
    """Reception interface for adding patients to queue."""
    rooms = Room.query.filter_by(is_active=True).all()
    return render_template('reception.html', rooms=rooms)


@main_bp.route('/operator')
def operator():
    """Operator interface for calling patients."""
    rooms = Room.query.filter_by(is_active=True).all()
    room_id = request.args.get('room_id', type=int)
    selected_room = None
    if room_id:
        selected_room = Room.query.get(room_id)
    return render_template('operator.html', rooms=rooms, selected_room=selected_room)
