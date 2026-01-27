/**
 * AgriStack MIS - Compact Analytics UI v3.0
 * Smart Response Rendering with Visual KPIs
 */

// ============================================================
// STATE & CONFIG
// ============================================================

let userLGD = localStorage.getItem('userLGD');
let activeCharts = new Map();

// Compact Color Palette
const COLORS = {
    primary: ['#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0'],
    chart: ['#059669', '#0891b2', '#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#84cc16', '#14b8a6'],
    success: '#10b981',
    warning: '#f59e0b',
    error: '#ef4444',
    info: '#3b82f6'
};

// ============================================================
// INITIALIZATION
// ============================================================

document.addEventListener('DOMContentLoaded', initializeApp);

function initializeApp() {
    const elements = {
        loginOverlay: document.getElementById('loginOverlay'),
        loginBtn: document.getElementById('loginBtn'),
        lgdInput: document.getElementById('lgdInput'),
        chatInput: document.getElementById('chatInput'),
        sendBtn: document.getElementById('sendBtn'),
        chatMessages: document.getElementById('chatMessages'),
        lgdDisplay: document.getElementById('lgdDisplay'),
        sidebarLgd: document.getElementById('sidebarLgd'),
        logoutBtn: document.getElementById('logoutBtn'),
        menuToggle: document.getElementById('menuToggle'),
        sidebar: document.getElementById('sidebar'),
        sidebarClose: document.getElementById('sidebarClose'),
        welcomeScreen: document.getElementById('welcomeScreen'),
    };

    if (userLGD) {
        hideLogin(elements);
        updateLGDDisplay(elements, userLGD);
    }

    setupEventListeners(elements);
}

// ============================================================
// EVENT LISTENERS
// ============================================================

function setupEventListeners(elements) {
    const { loginBtn, lgdInput, chatInput, sendBtn, logoutBtn, menuToggle, sidebar, sidebarClose } = elements;

    // Login
    loginBtn?.addEventListener('click', () => handleLogin(elements));
    lgdInput?.addEventListener('keypress', e => { if (e.key === 'Enter') handleLogin(elements); });

    // Chat
    sendBtn?.addEventListener('click', () => handleSendMessage(elements));
    chatInput?.addEventListener('keypress', e => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(elements);
        }
    });

    // Logout
    logoutBtn?.addEventListener('click', handleLogout);

    // Mobile sidebar
    menuToggle?.addEventListener('click', () => {
        sidebar?.classList.add('open');
        showOverlay();
    });

    sidebarClose?.addEventListener('click', () => {
        sidebar?.classList.remove('open');
        hideOverlay();
    });

    // Event delegation
    document.addEventListener('click', e => {
        // Query cards
        const queryCard = e.target.closest('.query-card');
        if (queryCard) {
            const query = queryCard.dataset.query;
            if (query && chatInput) {
                chatInput.value = query;
                handleSendMessage(elements);
            }
        }

        // Metadata toggle
        const metaToggle = e.target.closest('.metadata-toggle');
        if (metaToggle) {
            metaToggle.classList.toggle('active');
            metaToggle.nextElementSibling?.classList.toggle('show');
        }

        // Sidebar overlay
        if (e.target.classList.contains('sidebar-overlay')) {
            sidebar?.classList.remove('open');
            hideOverlay();
        }
    });
}

// ============================================================
// AUTH HANDLERS
// ============================================================

function handleLogin(elements) {
    const code = elements.lgdInput?.value.trim();
    if (code) {
        localStorage.setItem('userLGD', code);
        userLGD = code;
        hideLogin(elements);
        updateLGDDisplay(elements, code);
    } else {
        elements.lgdInput?.classList.add('shake');
        setTimeout(() => elements.lgdInput?.classList.remove('shake'), 400);
    }
}

function handleLogout() {
    localStorage.removeItem('userLGD');
    userLGD = null;
    location.reload();
}

function hideLogin(elements) {
    if (elements.loginOverlay) {
        elements.loginOverlay.style.opacity = '0';
        setTimeout(() => elements.loginOverlay.style.display = 'none', 250);
    }
}

function updateLGDDisplay(elements, code) {
    if (elements.lgdDisplay) elements.lgdDisplay.textContent = code;
    if (elements.sidebarLgd) elements.sidebarLgd.textContent = code;
}

// ============================================================
// CHAT HANDLER
// ============================================================

async function handleSendMessage(elements) {
    const query = elements.chatInput?.value.trim();
    if (!query) return;

    // Hide welcome
    if (elements.welcomeScreen) elements.welcomeScreen.style.display = 'none';

    // Add user message
    addUserMessage(elements.chatMessages, query);
    elements.chatInput.value = '';

    // Typing indicator
    const typingId = addTypingIndicator(elements.chatMessages);

    try {
        const response = await fetch('http://localhost:8001/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query, user_lgd_code: userLGD || '27' })
        });

        if (!response.ok) throw new Error('Server error');

        const data = await response.json();
        removeTypingIndicator(typingId);
        renderSmartResponse(elements.chatMessages, data);

    } catch (error) {
        removeTypingIndicator(typingId);
        renderErrorMessage(elements.chatMessages, error.message);
    }
}

// ============================================================
// USER MESSAGE
// ============================================================

function addUserMessage(container, text) {
    const div = document.createElement('div');
    div.className = 'message message-user';
    div.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
    container.appendChild(div);
    scrollToBottom(container);
}

// ============================================================
// TYPING INDICATOR
// ============================================================

function addTypingIndicator(container) {
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.className = 'message message-bot';
    div.id = id;
    div.innerHTML = `
        <div class="bot-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <div class="message-bubble">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom(container);
    return id;
}

function removeTypingIndicator(id) {
    document.getElementById(id)?.remove();
}

// ============================================================
// SMART RESPONSE RENDERER
// ============================================================

function renderSmartResponse(container, data) {
    const intentType = data.metadata?.intent_type || 'conversation';
    const chartType = data.chart_data?.type || 'message';

    const div = document.createElement('div');
    div.className = 'message message-bot';

    let content = '';

    // Route to appropriate renderer
    switch (intentType) {
        case 'conversation':
            content = renderConversation(data);
            break;

        case 'unauthorized_analytics':
            content = renderUnauthorized(data);
            break;

        case 'analytics':
            if (chartType === 'message' || !data.chart_data?.values?.length) {
                content = renderNoData(data);
            } else {
                content = renderAnalytics(data);
            }
            break;

        default:
            content = renderConversation(data);
    }

    div.innerHTML = `
        <div class="bot-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">${content}</div>
    `;

    container.appendChild(div);
    scrollToBottom(container);

    // Initialize charts after DOM render
    setTimeout(() => initializeCharts(div, data), 50);
}

// ============================================================
// CONVERSATION RENDERER
// ============================================================

function renderConversation(data) {
    const narration = data.narration || 'How can I help you today?';

    // Convert markdown-like formatting
    const formatted = formatNarration(narration);

    return `
        <div class="msg-conversation">
            <div class="msg-conversation-icon"><i class="fas fa-comments"></i></div>
            <div class="msg-conversation-text">${formatted}</div>
        </div>
    `;
}

// ============================================================
// UNAUTHORIZED RENDERER
// ============================================================

function renderUnauthorized(data) {
    return `
        <div class="msg-banner warning">
            <i class="fas fa-shield-halved"></i>
            <div>
                <strong>Access Restricted</strong>
                <p style="margin-top:4px;font-size:12px;">${escapeHtml(data.narration)}</p>
            </div>
        </div>
    `;
}

// ============================================================
// NO DATA RENDERER
// ============================================================

function renderNoData(data) {
    return `
        <div class="msg-banner info">
            <i class="fas fa-database"></i>
            <div>
                <strong>${escapeHtml(data.title)}</strong>
                <p style="margin-top:4px;font-size:12px;">${escapeHtml(data.narration)}</p>
            </div>
        </div>
    `;
}

// ============================================================
// ANALYTICS RENDERER
// ============================================================

function renderAnalytics(data) {
    const chartType = data.chart_data.type;
    const chartId = 'chart-' + Date.now();

    let visualContent = '';

    switch (chartType) {
        case 'kpi':
            visualContent = renderKPIVisual(data, chartId);
            break;
        case 'bar':
            visualContent = renderBarChart(data, chartId);
            break;
        case 'pie':
            visualContent = renderPieChart(data, chartId);
            break;
        case 'line':
            visualContent = renderLineChart(data, chartId);
            break;
        default:
            visualContent = renderKPIVisual(data, chartId);
    }

    return `
        <div class="analytics-card">
            <div class="analytics-header">
                <div class="analytics-title">
                    <div class="analytics-title-icon">
                        <i class="fas ${getChartIcon(chartType)}"></i>
                    </div>
                    <h4>${escapeHtml(data.title)}</h4>
                </div>
                <span class="analytics-badge">${chartType}</span>
            </div>
            <div class="analytics-body">
                ${visualContent}
                <div class="analytics-narration">
                    <p>${escapeHtml(data.narration)}</p>
                </div>
                ${renderMetadata(data.metadata)}
            </div>
        </div>
    `;
}

// ============================================================
// KPI VISUAL - Progress Ring + Mini Bar
// ============================================================

function renderKPIVisual(data, chartId) {
    const value = data.chart_data.values[0] || 0;
    const unit = data.chart_data.unit || '';
    const formatted = formatNumber(value);

    // Calculate progress percentage (assume 100% baseline for demo)
    const percentage = Math.min(100, Math.max(0, (value / (value * 1.2)) * 100));
    const circumference = 2 * Math.PI * 22;
    const strokeDasharray = `${(percentage / 100) * circumference} ${circumference}`;

    return `
        <div class="kpi-compact">
            <div class="kpi-ring">
                <svg viewBox="0 0 56 56">
                    <circle class="ring-bg" cx="28" cy="28" r="22"></circle>
                    <circle class="ring-progress" cx="28" cy="28" r="22"
                            stroke-dasharray="${strokeDasharray}"></circle>
                </svg>
                <div class="kpi-ring-value">${Math.round(percentage)}%</div>
            </div>
            <div class="kpi-info">
                <div class="kpi-value-row">
                    <span class="kpi-number">${formatted}</span>
                    <span class="kpi-unit">${escapeHtml(unit)}</span>
                </div>
                <div class="kpi-label">Current Period Total</div>
                <div class="kpi-progress-bar">
                    <div class="progress-track">
                        <div class="progress-fill" style="width:${percentage}%"></div>
                    </div>
                    <div class="progress-labels">
                        <span>0</span>
                        <span>Target</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// ============================================================
// BAR CHART VISUAL
// ============================================================

function renderBarChart(data, chartId) {
    const labels = data.chart_data.labels || [];
    const values = data.chart_data.values || [];
    const unit = data.chart_data.unit || '';

    // Mini table for top 5
    let tableRows = '';
    const top5 = labels.slice(0, 5);
    const total = values.reduce((a, b) => a + b, 0);

    top5.forEach((label, i) => {
        const pct = total > 0 ? ((values[i] / total) * 100).toFixed(1) : 0;
        tableRows += `
            <tr>
                <td><span class="table-rank ${i === 0 ? 'top' : ''}">${i + 1}</span></td>
                <td>${escapeHtml(String(label))}</td>
                <td style="text-align:right;font-weight:600">${formatNumber(values[i])}</td>
                <td style="text-align:right;color:var(--gray-500)">${pct}%</td>
            </tr>
        `;
    });

    return `
        <div class="chart-wrapper">
            <div class="chart-bar-container">
                <canvas id="${chartId}"></canvas>
            </div>
            <table class="data-table-mini">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Name</th>
                        <th style="text-align:right">${unit}</th>
                        <th style="text-align:right">Share</th>
                    </tr>
                </thead>
                <tbody>${tableRows}</tbody>
            </table>
        </div>
    `;
}

// ============================================================
// PIE CHART VISUAL
// ============================================================

function renderPieChart(data, chartId) {
    const labels = data.chart_data.labels || [];
    const values = data.chart_data.values || [];
    const total = values.reduce((a, b) => a + b, 0);

    // Legend items
    let legendItems = '';
    labels.slice(0, 6).forEach((label, i) => {
        const pct = total > 0 ? ((values[i] / total) * 100).toFixed(1) : 0;
        legendItems += `
            <div style="display:flex;align-items:center;gap:6px;font-size:11px;margin-bottom:4px">
                <span style="width:8px;height:8px;border-radius:50%;background:${COLORS.chart[i % COLORS.chart.length]}"></span>
                <span style="color:var(--gray-600);flex:1">${escapeHtml(String(label))}</span>
                <span style="font-weight:600">${pct}%</span>
            </div>
        `;
    });

    return `
        <div style="display:flex;gap:16px;align-items:center;flex-wrap:wrap">
            <div class="chart-pie-container" style="flex:1;min-width:140px">
                <canvas id="${chartId}"></canvas>
            </div>
            <div style="flex:1;min-width:140px">
                ${legendItems}
            </div>
        </div>
    `;
}

// ============================================================
// LINE CHART VISUAL
// ============================================================

function renderLineChart(data, chartId) {
    const labels = data.chart_data.labels || [];
    const values = data.chart_data.values || [];
    const unit = data.chart_data.unit || '';

    // Calculate trend
    let trendHtml = '';
    if (values.length >= 2) {
        const first = values[0];
        const last = values[values.length - 1];
        const change = last - first;
        const pctChange = first > 0 ? ((change / first) * 100).toFixed(1) : 0;
        const isPositive = change >= 0;

        trendHtml = `
            <div class="sparkline-container">
                <div class="sparkline-info">
                    <span class="sparkline-value">${formatNumber(last)}</span>
                    <span class="sparkline-change ${isPositive ? 'positive' : 'negative'}">
                        <i class="fas fa-arrow-${isPositive ? 'up' : 'down'}"></i>
                        ${Math.abs(pctChange)}%
                    </span>
                    <div class="sparkline-label">vs first period (${formatNumber(first)} ${unit})</div>
                </div>
            </div>
        `;
    }

    return `
        <div class="chart-wrapper">
            ${trendHtml}
            <div class="chart-line-container">
                <canvas id="${chartId}"></canvas>
            </div>
        </div>
    `;
}

// ============================================================
// METADATA RENDERER
// ============================================================

function renderMetadata(metadata) {
    if (!metadata) return '';

    const items = [];
    if (metadata.state) items.push({ label: 'State', value: metadata.state });
    if (metadata.lgd_scope) items.push({ label: 'LGD Code', value: metadata.lgd_scope });
    if (metadata.chart_type) items.push({ label: 'Visualization', value: metadata.chart_type });
    if (metadata.record_count) items.push({ label: 'Records', value: metadata.record_count });

    if (items.length === 0) return '';

    const rows = items.map(item => `
        <div class="metadata-row">
            <span class="label">${item.label}</span>
            <span class="value">${item.value}</span>
        </div>
    `).join('');

    return `
        <button class="metadata-toggle">
            <i class="fas fa-chevron-down"></i>
            <span>Details</span>
        </button>
        <div class="metadata-content">
            ${rows}
        </div>
    `;
}

// ============================================================
// CHART INITIALIZATION
// ============================================================

function initializeCharts(container, data) {
    const canvas = container.querySelector('canvas');
    if (!canvas || !data.chart_data) return;

    const chartType = data.chart_data.type;
    if (chartType === 'kpi' || chartType === 'message') return;

    const ctx = canvas.getContext('2d');
    const labels = data.chart_data.labels || [];
    const values = data.chart_data.values || [];
    const unit = data.chart_data.unit || '';

    // Destroy existing
    if (activeCharts.has(canvas.id)) {
        activeCharts.get(canvas.id).destroy();
    }

    let config;

    switch (chartType) {
        case 'bar':
            config = {
                type: 'bar',
                data: {
                    labels: labels.map(l => truncateLabel(String(l), 12)),
                    datasets: [{
                        data: values,
                        backgroundColor: COLORS.chart.slice(0, values.length),
                        borderRadius: 4,
                        maxBarThickness: 32
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(17,24,39,0.9)',
                            titleFont: { size: 11 },
                            bodyFont: { size: 11 },
                            padding: 8,
                            cornerRadius: 4,
                            callbacks: {
                                label: ctx => `${formatNumber(ctx.raw)} ${unit}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { color: 'rgba(0,0,0,0.04)' },
                            ticks: { font: { size: 10 }, callback: v => formatNumber(v) }
                        },
                        y: {
                            grid: { display: false },
                            ticks: { font: { size: 10 } }
                        }
                    }
                }
            };
            break;

        case 'pie':
            config = {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        backgroundColor: COLORS.chart.slice(0, values.length),
                        borderWidth: 0,
                        cutout: '65%'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(17,24,39,0.9)',
                            titleFont: { size: 11 },
                            bodyFont: { size: 11 },
                            padding: 8,
                            cornerRadius: 4,
                            callbacks: {
                                label: ctx => {
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = ((ctx.raw / total) * 100).toFixed(1);
                                    return `${formatNumber(ctx.raw)} ${unit} (${pct}%)`;
                                }
                            }
                        }
                    }
                }
            };
            break;

        case 'line':
            config = {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        borderColor: COLORS.primary[0],
                        backgroundColor: 'rgba(5,150,105,0.1)',
                        fill: true,
                        tension: 0.3,
                        borderWidth: 2,
                        pointRadius: 3,
                        pointBackgroundColor: COLORS.primary[0],
                        pointBorderColor: '#fff',
                        pointBorderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(17,24,39,0.9)',
                            titleFont: { size: 11 },
                            bodyFont: { size: 11 },
                            padding: 8,
                            cornerRadius: 4,
                            callbacks: {
                                label: ctx => `${formatNumber(ctx.raw)} ${unit}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: { font: { size: 10 } }
                        },
                        y: {
                            grid: { color: 'rgba(0,0,0,0.04)' },
                            ticks: { font: { size: 10 }, callback: v => formatNumber(v) },
                            beginAtZero: true
                        }
                    }
                }
            };
            break;
    }

    if (config) {
        const chart = new Chart(ctx, config);
        activeCharts.set(canvas.id, chart);
    }
}

// ============================================================
// ERROR RENDERER
// ============================================================

function renderErrorMessage(container, message) {
    const div = document.createElement('div');
    div.className = 'message message-bot';
    div.innerHTML = `
        <div class="bot-avatar"><i class="fas fa-robot"></i></div>
        <div class="message-content">
            <div class="msg-banner error">
                <i class="fas fa-exclamation-triangle"></i>
                <div>
                    <strong>Connection Error</strong>
                    <p style="margin-top:4px;font-size:12px;">${escapeHtml(message)}</p>
                </div>
            </div>
        </div>
    `;
    container.appendChild(div);
    scrollToBottom(container);
}

// ============================================================
// UTILITY FUNCTIONS
// ============================================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    const n = parseFloat(num);
    if (isNaN(n)) return '0';

    if (Math.abs(n) >= 10000000) return (n / 10000000).toFixed(2) + ' Cr';
    if (Math.abs(n) >= 100000) return (n / 100000).toFixed(2) + ' L';
    if (Math.abs(n) >= 1000) return (n / 1000).toFixed(1) + 'K';
    return n.toLocaleString('en-IN', { maximumFractionDigits: 2 });
}

function formatNarration(text) {
    // Convert **bold** and bullet points
    return text
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/• /g, '<br>• ')
        .replace(/\n/g, '<br>');
}

function truncateLabel(label, maxLen) {
    if (label.length <= maxLen) return label;
    return label.substring(0, maxLen - 2) + '..';
}

function getChartIcon(type) {
    const icons = {
        kpi: 'fa-gauge',
        bar: 'fa-chart-bar',
        pie: 'fa-chart-pie',
        line: 'fa-chart-line'
    };
    return icons[type] || 'fa-chart-simple';
}

function scrollToBottom(container) {
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
}

function showOverlay() {
    let overlay = document.querySelector('.sidebar-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'sidebar-overlay';
        document.body.appendChild(overlay);
    }
    setTimeout(() => overlay.classList.add('show'), 10);
}

function hideOverlay() {
    const overlay = document.querySelector('.sidebar-overlay');
    if (overlay) {
        overlay.classList.remove('show');
        setTimeout(() => overlay.remove(), 250);
    }
}
