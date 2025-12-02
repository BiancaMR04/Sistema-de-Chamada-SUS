/**
 * Reports Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('report-date').value = today;
    document.getElementById('absence-start').value = getWeekAgo();
    document.getElementById('absence-end').value = today;
    
    setupReportFilters();
    setupAbsenceReport();
    
    // Load initial reports
    loadDailyReport();
    loadHourlyDistribution();
});

function getWeekAgo() {
    const date = new Date();
    date.setDate(date.getDate() - 7);
    return date.toISOString().split('T')[0];
}

/**
 * Setup report filters
 */
function setupReportFilters() {
    const form = document.getElementById('report-filters');
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        loadDailyReport();
        loadHourlyDistribution();
    });
}

/**
 * Load daily report
 */
async function loadDailyReport() {
    const date = document.getElementById('report-date').value;
    const roomId = document.getElementById('report-room').value;
    
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (roomId) params.append('room_id', roomId);
    
    try {
        const response = await fetch(`/api/reports/daily?${params}`);
        const data = await response.json();
        
        // Update summary cards
        document.getElementById('total-patients').textContent = data.total_patients || 0;
        document.getElementById('attended-count').textContent = data.attended || 0;
        document.getElementById('absent-count').textContent = data.absent || 0;
        document.getElementById('waiting-count').textContent = data.waiting || 0;
        
        // Format wait time
        if (data.average_wait_time_seconds) {
            const minutes = Math.floor(data.average_wait_time_seconds / 60);
            document.getElementById('avg-wait-time').textContent = `${minutes} min`;
        } else {
            document.getElementById('avg-wait-time').textContent = '-';
        }
        
        // Update priority breakdown
        updatePriorityBreakdown(data.priority_breakdown || {});
    } catch (error) {
        console.error('Error loading daily report:', error);
    }
}

/**
 * Update priority breakdown display
 */
function updatePriorityBreakdown(breakdown) {
    const list = document.getElementById('priority-list');
    
    const priorityLabels = {
        'NORMAL': 'Normal',
        'CRIANCA': 'Criança',
        'LACTANTE': 'Lactante',
        'GESTANTE': 'Gestante',
        'IDOSO_60': 'Idoso 60+',
        'DEFICIENTE': 'PcD',
        'AUTISTA': 'TEA',
        'IDOSO_80': 'Idoso 80+'
    };
    
    const entries = Object.entries(breakdown).sort((a, b) => b[1] - a[1]);
    
    if (entries.length === 0) {
        list.innerHTML = '<li>Sem dados</li>';
        return;
    }
    
    list.innerHTML = entries.map(([priority, count]) => `
        <li>
            <span class="priority-indicator ${priority}"></span>
            <span class="label">${priorityLabels[priority] || priority}</span>
            <span class="count">${count}</span>
        </li>
    `).join('');
}

/**
 * Setup absence report
 */
function setupAbsenceReport() {
    document.getElementById('load-absences').addEventListener('click', loadAbsenceReport);
}

/**
 * Load absence report
 */
async function loadAbsenceReport() {
    const startDate = document.getElementById('absence-start').value;
    const endDate = document.getElementById('absence-end').value;
    const roomId = document.getElementById('report-room').value;
    
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    if (roomId) params.append('room_id', roomId);
    
    try {
        const response = await fetch(`/api/reports/absences?${params}`);
        const data = await response.json();
        
        document.getElementById('total-absences').textContent = data.total_absences || 0;
    } catch (error) {
        console.error('Error loading absence report:', error);
    }
}

/**
 * Load hourly distribution
 */
async function loadHourlyDistribution() {
    const date = document.getElementById('report-date').value;
    const roomId = document.getElementById('report-room').value;
    
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (roomId) params.append('room_id', roomId);
    
    try {
        const response = await fetch(`/api/reports/hourly?${params}`);
        const data = await response.json();
        
        displayHourlyChart(data.hourly_distribution || {});
    } catch (error) {
        console.error('Error loading hourly distribution:', error);
    }
}

/**
 * Display simple hourly chart
 */
function displayHourlyChart(distribution) {
    const container = document.getElementById('hourly-chart');
    
    const hours = Object.entries(distribution)
        .filter(([_, count]) => count > 0)
        .sort((a, b) => a[0].localeCompare(b[0]));
    
    if (hours.length === 0) {
        container.innerHTML = '<p>Sem dados para exibir</p>';
        return;
    }
    
    const maxCount = Math.max(...hours.map(([_, count]) => count));
    
    container.innerHTML = `
        <div class="chart-bars">
            ${hours.map(([hour, count]) => `
                <div class="bar-container">
                    <div class="bar" style="height: ${(count / maxCount) * 100}%">
                        <span class="bar-value">${count}</span>
                    </div>
                    <span class="bar-label">${hour}</span>
                </div>
            `).join('')}
        </div>
        <style>
            .chart-bars {
                display: flex;
                align-items: flex-end;
                height: 200px;
                gap: 4px;
                padding: 1rem 0;
            }
            .bar-container {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            .bar {
                width: 100%;
                background: var(--primary-color);
                border-radius: 4px 4px 0 0;
                min-height: 20px;
                display: flex;
                align-items: flex-start;
                justify-content: center;
            }
            .bar-value {
                color: white;
                font-size: 0.75rem;
                padding: 2px;
            }
            .bar-label {
                font-size: 0.75rem;
                color: var(--secondary-color);
                margin-top: 4px;
            }
        </style>
    `;
}
