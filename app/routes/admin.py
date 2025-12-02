"""
Admin routes for Sistema de Chamada SUS.
"""
from flask import Blueprint, render_template

from app.models import Room, Patient

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
def index():
    """Admin dashboard."""
    rooms = Room.query.all()
    patients_count = Patient.query.count()
    return render_template('admin/index.html', rooms=rooms, patients_count=patients_count)


@admin_bp.route('/rooms')
def rooms():
    """Manage rooms."""
    rooms = Room.query.order_by(Room.sector, Room.name).all()
    return render_template('admin/rooms.html', rooms=rooms)


@admin_bp.route('/reports')
def reports():
    """View reports."""
    rooms = Room.query.filter_by(is_active=True).all()
    return render_template('admin/reports.html', rooms=rooms)
