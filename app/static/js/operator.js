/**
 * Operator Page JavaScript
 */

let currentRoomId = null;
let currentEntry = null;

document.addEventListener('DOMContentLoaded', function() {
    setupRoomSelector();
    setupActionButtons();
});

/**
 * Initialize operator for a specific room
 */
function initializeOperator(roomId) {
    currentRoomId = roomId;
    
    // Join room for real-time updates
    joinRoom(roomId);
    
    // Load initial data
    loadOperatorData();
    
    // Setup real-time listeners
    setupOperatorListeners();
    
    // Show content
    document.getElementById('operator-content').hidden = false;
    
    // Refresh data periodically
    setInterval(loadOperatorData, 5000);
}

/**
 * Setup room selector
 */
function setupRoomSelector() {
    const roomSelect = document.getElementById('operator-room');
    
    roomSelect.addEventListener('change', function() {
        const roomId = this.value;
        
        if (currentRoomId) {
            leaveRoom(currentRoomId);
        }
        
        if (roomId) {
            // Update URL
            const url = new URL(window.location);
            url.searchParams.set('room_id', roomId);
            window.history.pushState({}, '', url);
            
            initializeOperator(parseInt(roomId));
        } else {
            document.getElementById('operator-content').hidden = true;
        }
    });
}

/**
 * Load operator data
 */
async function loadOperatorData() {
    if (!currentRoomId) return;
    
    try {
        const data = await apiRequest(`/display/${currentRoomId}`);
        updateOperatorDisplay(data);
    } catch (error) {
        console.error('Error loading operator data:', error);
    }
}

/**
 * Update operator display
 */
function updateOperatorDisplay(data) {
    // Update current patient
    const ticketEl = document.getElementById('op-current-ticket');
    const nameEl = document.getElementById('op-current-name');
    const priorityEl = document.getElementById('op-current-priority');
    const callCountEl = document.getElementById('op-call-count');
    
    if (data.current_call) {
        currentEntry = data.current_call;
        ticketEl.textContent = data.current_call.ticket_number;
        nameEl.textContent = data.current_call.patient_name || 'Paciente';
        priorityEl.textContent = formatPriority(data.current_call.priority_type);
        callCountEl.textContent = `Chamado ${data.current_call.call_count}x`;
        
        // Enable action buttons
        document.getElementById('btn-recall').disabled = false;
        document.getElementById('btn-attended').disabled = false;
        document.getElementById('btn-absent').disabled = false;
    } else {
        currentEntry = null;
        ticketEl.textContent = '---';
        nameEl.textContent = 'Nenhum paciente chamado';
        priorityEl.textContent = '';
        callCountEl.textContent = '';
        
        // Disable action buttons
        document.getElementById('btn-recall').disabled = true;
        document.getElementById('btn-attended').disabled = true;
        document.getElementById('btn-absent').disabled = true;
    }
    
    // Update queue table
    updateQueueTable(data.queue || []);
    document.getElementById('queue-total').textContent = data.waiting_count || 0;
    
    // Update history
    updateHistory(data.last_calls || []);
}

/**
 * Update queue table
 */
function updateQueueTable(queue) {
    const tbody = document.getElementById('queue-body');
    
    if (queue.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-queue">Nenhum paciente na fila</td></tr>';
        return;
    }
    
    tbody.innerHTML = queue.map(entry => `
        <tr data-entry-id="${entry.id}">
            <td>${entry.position}</td>
            <td><strong>${entry.ticket_number}</strong></td>
            <td>${entry.patient_name || 'Paciente'}</td>
            <td>
                <span class="priority-indicator ${entry.priority_type}"></span>
                ${formatPriority(entry.priority_type)}
            </td>
            <td>${formatTime(entry.created_at)}</td>
            <td>
                <button class="btn btn-small btn-primary btn-call-specific" 
                        data-entry-id="${entry.id}"
                        title="Chamar este paciente">
                    📢 Chamar
                </button>
                <button class="btn btn-small btn-danger btn-cancel" 
                        data-entry-id="${entry.id}"
                        title="Cancelar senha">
                    ✗
                </button>
            </td>
        </tr>
    `).join('');
    
    // Add event listeners
    tbody.querySelectorAll('.btn-call-specific').forEach(btn => {
        btn.addEventListener('click', function() {
            callSpecificPatient(parseInt(this.dataset.entryId));
        });
    });
    
    tbody.querySelectorAll('.btn-cancel').forEach(btn => {
        btn.addEventListener('click', function() {
            cancelEntry(parseInt(this.dataset.entryId));
        });
    });
}

/**
 * Update history list
 */
function updateHistory(history) {
    const historyList = document.getElementById('op-history');
    
    if (history.length === 0) {
        historyList.innerHTML = '<li class="empty">Nenhuma chamada registrada</li>';
        return;
    }
    
    historyList.innerHTML = history.map(call => `
        <li class="history-item">
            <span><strong>${call.ticket_number}</strong> - ${call.patient_display_name}</span>
            <span>${formatTime(call.called_at)}</span>
        </li>
    `).join('');
}

/**
 * Setup action buttons
 */
function setupActionButtons() {
    // Call next button
    document.getElementById('btn-call-next').addEventListener('click', callNext);
    
    // Recall button
    document.getElementById('btn-recall').addEventListener('click', recallPatient);
    
    // Attended button
    document.getElementById('btn-attended').addEventListener('click', markAttended);
    
    // Absent button
    document.getElementById('btn-absent').addEventListener('click', markAbsent);
}

/**
 * Call next patient
 */
async function callNext() {
    if (!currentRoomId) return;
    
    try {
        const entry = await apiRequest(`/queue/call/next/${currentRoomId}`, {
            method: 'POST'
        });
        
        currentEntry = entry;
        loadOperatorData();
        playCallSound();
        showToast(`Chamando: ${entry.ticket_number}`, 'success');
    } catch (error) {
        console.error('Error calling next:', error);
        showToast('Nenhum paciente na fila', 'info');
    }
}

/**
 * Call specific patient
 */
async function callSpecificPatient(entryId) {
    try {
        const entry = await apiRequest(`/queue/call/${entryId}`, {
            method: 'POST'
        });
        
        currentEntry = entry;
        loadOperatorData();
        playCallSound();
        showToast(`Chamando: ${entry.ticket_number}`, 'success');
    } catch (error) {
        console.error('Error calling patient:', error);
        showToast('Erro ao chamar paciente', 'error');
    }
}

/**
 * Recall current patient
 */
async function recallPatient() {
    if (!currentEntry) return;
    
    try {
        await apiRequest(`/queue/recall/${currentEntry.id}`, {
            method: 'POST'
        });
        
        loadOperatorData();
        playCallSound();
        showToast(`Chamando novamente: ${currentEntry.ticket_number}`, 'success');
    } catch (error) {
        console.error('Error recalling patient:', error);
        showToast('Erro ao chamar novamente', 'error');
    }
}

/**
 * Mark current patient as attended
 */
async function markAttended() {
    if (!currentEntry) return;
    
    try {
        await apiRequest(`/queue/attend/${currentEntry.id}`, {
            method: 'POST'
        });
        
        showToast('Paciente atendido', 'success');
        currentEntry = null;
        loadOperatorData();
    } catch (error) {
        console.error('Error marking attended:', error);
        showToast('Erro ao marcar atendido', 'error');
    }
}

/**
 * Mark current patient as absent
 */
async function markAbsent() {
    if (!currentEntry) return;
    
    const notes = prompt('Observações sobre a ausência (opcional):');
    
    try {
        await apiRequest(`/queue/absent/${currentEntry.id}`, {
            method: 'POST',
            body: JSON.stringify({ notes })
        });
        
        showToast('Paciente marcado como ausente', 'warning');
        currentEntry = null;
        loadOperatorData();
    } catch (error) {
        console.error('Error marking absent:', error);
        showToast('Erro ao marcar ausente', 'error');
    }
}

/**
 * Cancel queue entry
 */
async function cancelEntry(entryId) {
    if (!confirm('Cancelar esta senha?')) return;
    
    try {
        await apiRequest(`/queue/cancel/${entryId}`, {
            method: 'POST'
        });
        
        showToast('Senha cancelada', 'info');
        loadOperatorData();
    } catch (error) {
        console.error('Error cancelling entry:', error);
        showToast('Erro ao cancelar', 'error');
    }
}

/**
 * Setup real-time listeners
 */
function setupOperatorListeners() {
    if (!socket) return;
    
    socket.on('queue_update', function(data) {
        if (data.room_id !== currentRoomId) return;
        loadOperatorData();
    });
    
    socket.on('patient_called', function(data) {
        if (data.room_id !== currentRoomId) return;
        loadOperatorData();
    });
}

/**
 * Play call sound
 */
function playCallSound() {
    const audio = document.getElementById('call-sound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log('Audio play failed:', e));
    }
}
