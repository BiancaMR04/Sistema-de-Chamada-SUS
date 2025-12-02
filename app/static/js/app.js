/**
 * Sistema de Chamada SUS - Main Application JavaScript
 */

// API Base URL
const API_BASE = '/api';

// Socket.IO connection
let socket = null;

/**
 * Initialize Socket.IO connection
 */
function initSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Socket connected');
        updateConnectionStatus(true);
    });
    
    socket.on('disconnect', function() {
        console.log('Socket disconnected');
        updateConnectionStatus(false);
    });
    
    socket.on('error', function(error) {
        console.error('Socket error:', error);
    });
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(isOnline) {
    const indicator = document.querySelector('.status-indicator');
    const text = document.getElementById('status-text');
    
    if (indicator) {
        indicator.classList.toggle('online', isOnline);
        indicator.classList.toggle('offline', !isOnline);
    }
    
    if (text) {
        text.textContent = isOnline ? 'Conectado' : 'Desconectado';
    }
}

/**
 * Check e-SUS connection status
 */
async function checkESUSStatus() {
    try {
        const response = await fetch(`${API_BASE}/esus/status`);
        const data = await response.json();
        
        const statusEl = document.getElementById('esus-status');
        if (statusEl) {
            statusEl.textContent = data.connected ? 'e-SUS: Online' : 'e-SUS: Offline';
            statusEl.className = data.connected ? 'online' : 'offline';
        }
        
        return data.connected;
    } catch (error) {
        console.error('Error checking e-SUS status:', error);
        return false;
    }
}

/**
 * Join a room for real-time updates
 */
function joinRoom(roomId) {
    if (socket) {
        socket.emit('join', { room: `room_${roomId}` });
    }
}

/**
 * Leave a room
 */
function leaveRoom(roomId) {
    if (socket) {
        socket.emit('leave', { room: `room_${roomId}` });
    }
}

/**
 * Format timestamp to local time
 */
function formatTime(isoString) {
    if (!isoString) return '';
    const date = new Date(isoString);
    return date.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}

/**
 * Format priority type to display text
 */
function formatPriority(priorityType) {
    const priorities = {
        'NORMAL': 'Normal',
        'CRIANCA': 'Criança',
        'LACTANTE': 'Lactante',
        'GESTANTE': 'Gestante',
        'IDOSO_60': 'Idoso 60+',
        'DEFICIENTE': 'PcD',
        'AUTISTA': 'TEA',
        'IDOSO_80': 'Idoso 80+'
    };
    return priorities[priorityType] || priorityType;
}

/**
 * Format CPF with mask
 */
function formatCPF(cpf) {
    if (!cpf) return '';
    const digits = cpf.replace(/\D/g, '');
    if (digits.length !== 11) return cpf;
    return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

/**
 * Remove CPF mask
 */
function unformatCPF(cpf) {
    return cpf.replace(/\D/g, '');
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position: fixed; top: 1rem; right: 1rem; z-index: 1000;';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    toast.style.cssText = `
        background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#2563eb'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease;
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * API request helper
 */
async function apiRequest(endpoint, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    const config = { ...defaultOptions, ...options };
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, config);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initSocket();
    checkESUSStatus();
    
    // Add toast animation styles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOut {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
});
