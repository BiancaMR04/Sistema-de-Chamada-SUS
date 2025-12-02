/**
 * Admin Pages JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    setupRoomForm();
    setupToggleButtons();
});

/**
 * Setup room creation form
 */
function setupRoomForm() {
    const form = document.getElementById('room-form');
    if (!form) return;
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const name = document.getElementById('room-name').value.trim();
        const sector = document.getElementById('room-sector').value.trim();
        
        if (!name || !sector) {
            showToast('Nome e setor são obrigatórios', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/rooms', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, sector })
            });
            
            if (!response.ok) {
                throw new Error('Failed to create room');
            }
            
            showToast('Sala criada com sucesso!', 'success');
            
            // Reload page to show new room
            setTimeout(() => window.location.reload(), 1000);
        } catch (error) {
            console.error('Error creating room:', error);
            showToast('Erro ao criar sala', 'error');
        }
    });
}

/**
 * Setup toggle buttons for room activation
 */
function setupToggleButtons() {
    document.querySelectorAll('.btn-toggle').forEach(btn => {
        btn.addEventListener('click', async function() {
            const roomId = this.dataset.roomId;
            const action = this.dataset.action;
            const isActive = action === 'activate';
            
            try {
                const response = await fetch(`/api/rooms/${roomId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ is_active: isActive })
                });
                
                if (!response.ok) {
                    throw new Error('Failed to update room');
                }
                
                showToast(`Sala ${isActive ? 'ativada' : 'desativada'}`, 'success');
                
                // Reload page
                setTimeout(() => window.location.reload(), 1000);
            } catch (error) {
                console.error('Error updating room:', error);
                showToast('Erro ao atualizar sala', 'error');
            }
        });
    });
}

// Toast function (in case app.js is not loaded)
if (typeof showToast === 'undefined') {
    function showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.style.cssText = 'position: fixed; top: 1rem; right: 1rem; z-index: 1000;';
            document.body.appendChild(container);
        }
        
        const toast = document.createElement('div');
        toast.textContent = message;
        toast.style.cssText = `
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#22c55e' : '#2563eb'};
            color: white;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            margin-bottom: 0.5rem;
        `;
        
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}
