/**
 * Reception Page JavaScript
 */

let selectedPatient = null;

document.addEventListener('DOMContentLoaded', function() {
    setupSearchForm();
    setupOfflineForm();
    setupQueueForm();
});

/**
 * Setup patient search form
 */
function setupSearchForm() {
    const searchForm = document.getElementById('search-form');
    const cpfInput = document.getElementById('search-cpf');
    const nameInput = document.getElementById('search-name');
    
    // CPF formatting
    cpfInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 11) value = value.slice(0, 11);
        e.target.value = formatCPF(value);
    });
    
    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const cpf = unformatCPF(cpfInput.value);
        const name = nameInput.value.trim();
        
        if (!cpf && name.length < 3) {
            showToast('Digite um CPF ou nome com pelo menos 3 caracteres', 'error');
            return;
        }
        
        try {
            const params = new URLSearchParams();
            if (cpf) params.append('cpf', cpf);
            if (name) params.append('name', name);
            
            const response = await fetch(`/api/patients/search?${params}`);
            const data = await response.json();
            
            displaySearchResults(data);
        } catch (error) {
            console.error('Search error:', error);
            showToast('Erro ao buscar paciente', 'error');
        }
    });
}

/**
 * Display search results
 */
function displaySearchResults(data) {
    const resultsDiv = document.getElementById('search-results');
    
    if (!data.found) {
        resultsDiv.innerHTML = `
            <div class="no-results">
                <p>Paciente não encontrado.</p>
                <p>Use o cadastro manual abaixo para registrar o paciente.</p>
            </div>
        `;
        return;
    }
    
    if (data.patient) {
        // Single patient found
        resultsDiv.innerHTML = `
            <div class="result-item" data-patient='${JSON.stringify(data.patient)}'>
                <strong>${data.patient.name}</strong>
                ${data.patient.cpf ? `<br>CPF: ${formatCPF(data.patient.cpf)}` : ''}
                <br>Prioridade: ${formatPriority(data.patient.priority_type)}
                <br><small>Fonte: ${data.source === 'esus' ? 'e-SUS' : 'Local'}</small>
            </div>
        `;
    } else if (data.patients) {
        // Multiple patients found
        resultsDiv.innerHTML = data.patients.map(patient => `
            <div class="result-item" data-patient='${JSON.stringify(patient)}'>
                <strong>${patient.name}</strong>
                ${patient.cpf ? `<br>CPF: ${formatCPF(patient.cpf)}` : ''}
                <br>Prioridade: ${formatPriority(patient.priority_type)}
            </div>
        `).join('');
    }
    
    // Add click handlers to results
    document.querySelectorAll('.result-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.result-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            
            const patient = JSON.parse(this.dataset.patient);
            selectPatient(patient);
        });
    });
}

/**
 * Select a patient for queue
 */
function selectPatient(patient) {
    selectedPatient = patient;
    
    document.getElementById('selected-patient').value = 
        `${patient.name} ${patient.cpf ? '(CPF: ' + formatCPF(patient.cpf) + ')' : ''}`;
    document.getElementById('patient-id').value = patient.id;
    document.getElementById('add-queue-btn').disabled = false;
    
    // Set priority dropdown to patient's priority
    const prioritySelect = document.getElementById('queue-priority');
    for (let option of prioritySelect.options) {
        if (option.value === patient.priority_type) {
            option.selected = true;
            break;
        }
    }
}

/**
 * Setup offline patient registration form
 */
function setupOfflineForm() {
    const offlineForm = document.getElementById('offline-form');
    const cpfInput = document.getElementById('offline-cpf');
    
    // CPF formatting
    cpfInput.addEventListener('input', function(e) {
        let value = e.target.value.replace(/\D/g, '');
        if (value.length > 11) value = value.slice(0, 11);
        e.target.value = formatCPF(value);
    });
    
    offlineForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = {
            name: document.getElementById('offline-name').value.trim(),
            cpf: unformatCPF(document.getElementById('offline-cpf').value) || null,
            birth_date: document.getElementById('offline-birth').value || null,
            priority_type: document.getElementById('offline-priority').value
        };
        
        if (!formData.name) {
            showToast('Nome é obrigatório', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/patients/offline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to create patient');
            }
            
            const patient = await response.json();
            selectPatient(patient);
            showToast('Paciente cadastrado com sucesso!', 'success');
            
            // Clear form
            offlineForm.reset();
        } catch (error) {
            console.error('Error creating patient:', error);
            showToast('Erro ao cadastrar paciente', 'error');
        }
    });
}

/**
 * Setup queue form
 */
function setupQueueForm() {
    const queueForm = document.getElementById('queue-form');
    
    queueForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const patientId = document.getElementById('patient-id').value;
        const roomId = document.getElementById('room-select').value;
        const priorityType = document.getElementById('queue-priority').value || null;
        
        if (!patientId) {
            showToast('Selecione um paciente', 'error');
            return;
        }
        
        if (!roomId) {
            showToast('Selecione uma sala', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/queue/${roomId}/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    patient_id: parseInt(patientId),
                    priority_type: priorityType
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Failed to add to queue');
            }
            
            const entry = await response.json();
            showTicket(entry);
            
            // Clear selection
            selectedPatient = null;
            document.getElementById('selected-patient').value = '';
            document.getElementById('patient-id').value = '';
            document.getElementById('add-queue-btn').disabled = true;
            document.getElementById('queue-priority').value = '';
            document.getElementById('search-results').innerHTML = '';
        } catch (error) {
            console.error('Error adding to queue:', error);
            showToast(error.message || 'Erro ao adicionar à fila', 'error');
        }
    });
}

/**
 * Show generated ticket
 */
function showTicket(entry) {
    const ticketDisplay = document.getElementById('ticket-display');
    const ticketNumber = document.getElementById('generated-ticket');
    const ticketPosition = document.getElementById('ticket-position');
    
    ticketNumber.textContent = entry.ticket_number;
    ticketPosition.textContent = entry.position;
    ticketDisplay.hidden = false;
    
    showToast('Paciente adicionado à fila com sucesso!', 'success');
    
    // Hide after 10 seconds
    setTimeout(() => {
        ticketDisplay.hidden = true;
    }, 10000);
}
