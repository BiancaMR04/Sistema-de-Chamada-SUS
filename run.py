"""
Entry point for Sistema de Chamada SUS.
"""
import os
from app import create_app, socketio

# Determine configuration
# In development, we use 'testing' config for threading mode compatibility
# In production, set FLASK_ENV=production for gevent async mode
config_name = os.environ.get('FLASK_ENV', 'development')
if config_name == 'development':
    # Use threading mode for local development (gevent has compatibility issues)
    config_name = 'testing'

app = create_app(config_name)


@socketio.on('join')
def on_join(data):
    """Handle client joining a room."""
    from flask_socketio import join_room
    room = data.get('room')
    if room:
        join_room(room)


@socketio.on('leave')
def on_leave(data):
    """Handle client leaving a room."""
    from flask_socketio import leave_room
    room = data.get('room')
    if room:
        leave_room(room)


if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
