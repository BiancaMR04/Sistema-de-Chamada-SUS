/**
 * Display Panel JavaScript
 */

let audioEnabled = false;
let currentRoomId = null;

/**
 * Initialize the display panel
 */
function initializePanel(roomId) {
    currentRoomId = roomId;
    
    // Join the room for real-time updates
    joinRoom(roomId);
    
    // Load initial data
    loadPanelData();
    
    // Set up real-time listeners
    setupPanelListeners();
    
    // Set up audio button
    setupAudioButton();
    
    // Refresh data periodically as backup
    setInterval(loadPanelData, 5000);
}

/**
 * Load panel data from API
 */
async function loadPanelData() {
    try {
        const data = await apiRequest(`/display/${currentRoomId}`);
        updatePanelDisplay(data);
    } catch (error) {
        console.error('Error loading panel data:', error);
    }
}

/**
 * Update the panel display
 */
function updatePanelDisplay(data) {
    // Update current call
    const ticketEl = document.getElementById('current-ticket');
    const nameEl = document.getElementById('current-name');
    
    if (data.current_call) {
        ticketEl.textContent = data.current_call.ticket_number;
        nameEl.textContent = data.current_call.patient_name || 'Paciente';
    } else {
        ticketEl.textContent = '---';
        nameEl.textContent = 'Aguardando...';
    }
    
    // Update history
    const historyList = document.getElementById('history-list');
    if (data.last_calls && data.last_calls.length > 0) {
        historyList.innerHTML = data.last_calls.map(call => `
            <li class="history-item">
                <div class="ticket">${call.ticket_number}</div>
                <div class="name">${call.patient_display_name}</div>
                <div class="time">${formatTime(call.called_at)}</div>
            </li>
        `).join('');
    } else {
        historyList.innerHTML = '<li class="history-item empty">Nenhuma chamada registrada</li>';
    }
    
    // Update waiting count
    const waitingCount = document.getElementById('waiting-count');
    waitingCount.textContent = data.waiting_count || 0;
    
    // Update next patients preview
    const nextPatients = document.getElementById('next-patients');
    if (data.queue && data.queue.length > 0) {
        nextPatients.innerHTML = data.queue.slice(0, 5).map(entry => `
            <div class="next-patient">
                <span class="priority-indicator ${entry.priority_type}"></span>
                <span class="ticket">${entry.ticket_number}</span>
            </div>
        `).join('');
    } else {
        nextPatients.innerHTML = '<span class="empty">Nenhum paciente na fila</span>';
    }
}

/**
 * Set up real-time update listeners
 */
function setupPanelListeners() {
    if (!socket) return;
    
    // Patient called event
    socket.on('patient_called', function(data) {
        if (data.room_id !== currentRoomId) return;
        
        const ticketEl = document.getElementById('current-ticket');
        const nameEl = document.getElementById('current-name');
        const callSection = document.querySelector('.current-call');
        
        // Update display
        ticketEl.textContent = data.entry.ticket_number;
        nameEl.textContent = data.entry.patient_name || 'Paciente';
        
        // Add animation
        callSection.classList.add('calling');
        setTimeout(() => callSection.classList.remove('calling'), 3000);
        
        // Play audio if enabled
        if (data.play_audio && audioEnabled) {
            playCallSound();
        }
        
        // Reload all data to update history and queue
        setTimeout(loadPanelData, 500);
    });
    
    // Queue update event
    socket.on('queue_update', function(data) {
        if (data.room_id !== currentRoomId) return;
        
        // Reload panel data
        loadPanelData();
    });
}

/**
 * Set up audio button
 */
function setupAudioButton() {
    const audioBtn = document.getElementById('enable-audio');
    
    audioBtn.addEventListener('click', function() {
        audioEnabled = !audioEnabled;
        
        if (audioEnabled) {
            audioBtn.textContent = '🔊 Som Ativado';
            audioBtn.classList.add('enabled');
            
            // Test audio
            playCallSound();
        } else {
            audioBtn.textContent = '🔊 Ativar Som';
            audioBtn.classList.remove('enabled');
        }
    });
}

/**
 * Play call notification sound
 */
function playCallSound() {
    const audio = document.getElementById('call-sound');
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => {
            console.log('Audio play failed:', e);
        });
    }
}
