/**
 * AgriStack MIS - Premium Analytics UI v5.0
 * Enhanced Charts with Gradients, 3D Effects & Animations
 */

// ============================================================
// STATE & CONFIG
// ============================================================

let userLGD = localStorage.getItem('userLGD');
let activeCharts = new Map();

// AgriStack Green & Gold Color Palette
const COLORS = {
    primary: ['#1B4332', '#2D6A4F', '#40916C', '#52B788', '#74C69D'],
    chart: [
        '#1B4332', '#2D6A4F', '#40916C', '#52B788',
        '#D4A017', '#B8860B', '#74C69D', '#95D5B2',
        '#DAA520', '#2D6A4F', '#40916C', '#1B4332'
    ],
    gradients: [
        ['#1B4332', '#40916C'],
        ['#2D6A4F', '#52B788'],
        ['#B8860B', '#DAA520'],
        ['#40916C', '#74C69D'],
        ['#D4A017', '#F0C040'],
        ['#1B4332', '#2D6A4F'],
        ['#52B788', '#95D5B2'],
        ['#2D6A4F', '#74C69D']
    ],
    success: '#2D6A4F',
    warning: '#DAA520',
    error: '#dc3545',
    info: '#40916C'
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

    // Logout - handle all logout buttons
    document.querySelectorAll('#logoutBtn, .logout-btn').forEach(btn => {
        btn.addEventListener('click', handleLogout);
    });

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

        // Suggested query cards (for off-topic responses)
        const suggestedCard = e.target.closest('.suggested-query-card');
        if (suggestedCard) {
            const query = suggestedCard.dataset.query;
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
        setTimeout(() => elements.lgdInput?.classList.remove('shake'), 500);
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
        elements.loginOverlay.style.transform = 'scale(1.05)';
        setTimeout(() => elements.loginOverlay.style.display = 'none', 300);
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

        case 'off_topic':
            content = renderOffTopic(data);
            break;

        case 'unauthorized_analytics':
            content = renderUnauthorized(data);
            break;

        case 'analytics':
            // Check for multi_kpi (has kpis array) or regular charts (has values array)
            const hasData = chartType === 'multi_kpi'
                ? data.chart_data?.kpis?.length > 0
                : data.chart_data?.values?.length > 0;

            if (chartType === 'message' || !hasData) {
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
    setTimeout(() => initializeCharts(div, data), 100);
}

// ============================================================
// CONVERSATION RENDERER
// ============================================================

function renderConversation(data) {
    const narration = data.narration || 'How can I help you today?';
    const formatted = formatNarration(narration);

    return `
        <div class="msg-conversation">
            <div class="msg-conversation-icon"><i class="fas fa-comments"></i></div>
            <div class="msg-conversation-text">${formatted}</div>
        </div>
    `;
}

// ============================================================
// OFF-TOPIC RENDERER
// ============================================================

function renderOffTopic(data) {
    const suggestedQueries = data.suggested_queries || [];

    let suggestionsHtml = '';
    if (suggestedQueries.length > 0) {
        const queryCards = suggestedQueries.map(query => `
            <div class="suggested-query-card" data-query="${escapeHtml(query)}" style="padding:10px 14px;background:linear-gradient(135deg,#f0f9f0,#e8f5e8);border:1px solid #b7e4c7;border-radius:8px;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:8px">
                <i class="fas fa-arrow-right" style="color:#1B4332;font-size:10px"></i>
                <span style="color:#1B4332;font-size:13px">${escapeHtml(query)}</span>
            </div>
        `).join('');

        suggestionsHtml = `
            <div style="margin-top:16px">
                <div style="font-size:12px;font-weight:600;color:#1B4332;margin-bottom:10px;display:flex;align-items:center;gap:6px">
                    <i class="fas fa-lightbulb"></i>
                    <span>Try asking questions like:</span>
                </div>
                <div style="display:flex;flex-direction:column;gap:8px">
                    ${queryCards}
                </div>
            </div>
        `;
    }

    return `
        <div class="msg-banner info" style="background:linear-gradient(135deg,#fef3c7,#fef9c3);border:1px solid #fcd34d">
            <i class="fas fa-info-circle" style="color:#d97706"></i>
            <div style="flex:1">
                <strong style="color:#92400e">I can only help with Agriculture Data</strong>
                <p style="margin-top:6px;font-size:13px;color:#a16207">${escapeHtml(data.narration)}</p>
                ${suggestionsHtml}
            </div>
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
                <p style="margin-top:4px;font-size:13px;">${escapeHtml(data.narration)}</p>
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
                <p style="margin-top:4px;font-size:13px;">${escapeHtml(data.narration)}</p>
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
        case 'multi_kpi':
            visualContent = renderMultiKPIVisual(data, chartId);
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

    // Display-friendly badge text
    const badgeText = chartType === 'multi_kpi' ? 'SUMMARY' : chartType.toUpperCase();

    return `
        <div class="analytics-card">
            <div class="analytics-header">
                <div class="analytics-title">
                    <div class="analytics-title-icon">
                        <i class="fas ${getChartIcon(chartType)}"></i>
                    </div>
                    <h4>${escapeHtml(data.title)}</h4>
                </div>
                <span class="analytics-badge">${badgeText}</span>
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
// KPI VISUAL - Animated Ring with Gradient
// ============================================================

function renderKPIVisual(data, chartId) {
    const value = data.chart_data.values[0] || 0;
    const unit = data.chart_data.unit || '';
    const formatted = formatNumber(value);
    const fullValue = value.toLocaleString('en-IN');

    // Get icon based on unit type
    const iconMap = {
        'Farmers': 'fa-users',
        'Plots': 'fa-map',
        'Hectares': 'fa-seedling',
        'Surveys': 'fa-clipboard-check',
        'Surveyors': 'fa-user-tie'
    };
    const icon = iconMap[unit] || 'fa-chart-line';

    // Get extra stats from metadata
    const farmersCount = data.farmers_count || data.metadata?.farmers_count;
    const plotsCount = data.plots_count || data.metadata?.plots_count;
    const uniqueCrops = data.unique_crops || data.metadata?.unique_crops;

    // Build mini stats cards
    let miniStats = '';
    if (farmersCount || plotsCount || uniqueCrops) {
        miniStats = `<div class="kpi-mini-stats">`;
        if (farmersCount && unit !== 'Farmers') {
            miniStats += `
                <div class="mini-stat-card">
                    <i class="fas fa-users"></i>
                    <div class="mini-stat-value">${formatNumber(farmersCount)}</div>
                    <div class="mini-stat-label">Farmers</div>
                </div>`;
        }
        if (plotsCount && unit !== 'Plots') {
            miniStats += `
                <div class="mini-stat-card">
                    <i class="fas fa-map"></i>
                    <div class="mini-stat-value">${formatNumber(plotsCount)}</div>
                    <div class="mini-stat-label">Plots</div>
                </div>`;
        }
        if (uniqueCrops) {
            miniStats += `
                <div class="mini-stat-card">
                    <i class="fas fa-leaf"></i>
                    <div class="mini-stat-value">${uniqueCrops}</div>
                    <div class="mini-stat-label">Crops</div>
                </div>`;
        }
        miniStats += `</div>`;
    }

    return `
        <div class="kpi-hero">
            <div class="kpi-hero-left">
                <div class="kpi-icon-wrapper">
                    <div class="kpi-icon-bg"></div>
                    <i class="fas ${icon}"></i>
                </div>
            </div>
            <div class="kpi-hero-right">
                <div class="kpi-hero-value">
                    <span class="kpi-big-number" data-value="${value}">${formatted}</span>
                    <span class="kpi-hero-unit">${escapeHtml(unit)}</span>
                </div>
                <div class="kpi-hero-subtitle">
                    <span class="kpi-exact-value">${fullValue} ${escapeHtml(unit)}</span>
                    <span class="kpi-badge-live"><i class="fas fa-circle"></i> Live Data</span>
                </div>
            </div>
        </div>
        ${miniStats}
    `;
}

// ============================================================
// MULTI-KPI VISUAL - Summary Dashboard with Multiple Cards
// ============================================================

function renderMultiKPIVisual(data, chartId) {
    const kpis = data.chart_data.kpis || [];

    if (kpis.length === 0) {
        return `<div class="msg-banner info">
            <i class="fas fa-info-circle"></i>
            <span>No summary data available</span>
        </div>`;
    }

    // Icon mapping for different indicators
    const iconMap = {
        'surveyed_plots': 'fa-clipboard-check',
        'crop_area': 'fa-seedling',
        'farmers': 'fa-users',
        'total_plots': 'fa-map',
        'irrigated_area': 'fa-tint',
        'fallow_area': 'fa-leaf',
        'harvested_area': 'fa-wheat',
        'surveyed_area': 'fa-ruler-combined'
    };

    // Color gradient mapping
    const colorMap = {
        'surveyed_plots': ['#2D6A4F', '#52B788'],
        'crop_area': ['#1B4332', '#40916C'],
        'farmers': ['#B8860B', '#DAA520'],
        'total_plots': ['#D4A017', '#F0C040'],
        'irrigated_area': ['#40916C', '#74C69D'],
        'fallow_area': ['#52B788', '#95D5B2'],
        'harvested_area': ['#1B4332', '#2D6A4F'],
        'surveyed_area': ['#2D6A4F', '#74C69D']
    };

    let kpiCards = kpis.map((kpi, index) => {
        const icon = iconMap[kpi.indicator] || 'fa-chart-line';
        const colors = colorMap[kpi.indicator] || COLORS.gradients[index % COLORS.gradients.length];
        const formatted = formatNumber(kpi.value);
        const fullValue = kpi.value.toLocaleString('en-IN');

        // Build extra info if available
        let extraInfo = '';
        if (kpi.farmers_count) {
            extraInfo += `<span class="kpi-extra-stat"><i class="fas fa-users"></i> ${formatNumber(kpi.farmers_count)}</span>`;
        }
        if (kpi.plots_count) {
            extraInfo += `<span class="kpi-extra-stat"><i class="fas fa-map"></i> ${formatNumber(kpi.plots_count)}</span>`;
        }
        if (kpi.unique_crops) {
            extraInfo += `<span class="kpi-extra-stat"><i class="fas fa-leaf"></i> ${kpi.unique_crops} crops</span>`;
        }

        return `
            <div class="multi-kpi-card" style="--card-color-1: ${colors[0]}; --card-color-2: ${colors[1]}">
                <div class="multi-kpi-icon">
                    <i class="fas ${icon}"></i>
                </div>
                <div class="multi-kpi-content">
                    <div class="multi-kpi-title">${escapeHtml(kpi.title)}</div>
                    <div class="multi-kpi-value">${formatted}</div>
                    <div class="multi-kpi-unit">${escapeHtml(kpi.unit)}</div>
                    <div class="multi-kpi-exact">${fullValue}</div>
                    ${extraInfo ? `<div class="multi-kpi-extras">${extraInfo}</div>` : ''}
                </div>
            </div>
        `;
    }).join('');

    return `
        <div class="multi-kpi-container">
            <div class="multi-kpi-header">
                <i class="fas fa-layer-group"></i>
                <span>National Summary</span>
            </div>
            <div class="multi-kpi-grid">
                ${kpiCards}
            </div>
        </div>
    `;
}

// ============================================================
// BAR CHART - 3D Style with Gradients
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
                <td style="text-align:right;font-weight:700">${formatNumber(values[i])}</td>
                <td style="text-align:right;color:var(--gray-500)">${pct}%</td>
            </tr>
        `;
    });

    // Total summary section
    const totalFormatted = formatNumber(total);
    const totalFull = total.toLocaleString('en-IN', { maximumFractionDigits: 2 });

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
            <div class="chart-total-summary" style="margin-top:16px;padding:12px 16px;background:linear-gradient(135deg,#f0f9f0,#e8f5e8);border-radius:10px;border:1px solid #b7e4c7;display:flex;align-items:center;justify-content:space-between">
                <div style="display:flex;align-items:center;gap:10px">
                    <div style="width:36px;height:36px;background:#1B4332;border-radius:8px;display:flex;align-items:center;justify-content:center">
                        <i class="fas fa-calculator" style="color:white;font-size:14px"></i>
                    </div>
                    <div>
                        <div style="font-size:11px;font-weight:600;color:#1B4332;text-transform:uppercase;letter-spacing:0.5px">Total</div>
                        <div style="font-size:10px;color:#6b7280">${totalFull} ${escapeHtml(unit)}</div>
                    </div>
                </div>
                <div style="text-align:right">
                    <div style="font-size:22px;font-weight:700;color:#1B4332">${totalFormatted}</div>
                    <div style="font-size:11px;color:#6b7280">${escapeHtml(unit)}</div>
                </div>
            </div>
        </div>
    `;
}

// ============================================================
// PIE CHART - Doughnut with 3D Effect
// ============================================================

function renderPieChart(data, chartId) {
    const labels = data.chart_data.labels || [];
    const values = data.chart_data.values || [];
    const unit = data.chart_data.unit || '';
    const total = values.reduce((a, b) => a + b, 0);

    // Legend items with gradient badges
    let legendItems = '';
    labels.slice(0, 6).forEach((label, i) => {
        const pct = total > 0 ? ((values[i] / total) * 100).toFixed(1) : 0;
        const color = COLORS.chart[i % COLORS.chart.length];
        legendItems += `
            <div style="display:flex;align-items:center;gap:10px;font-size:12px;margin-bottom:8px;padding:6px 10px;background:linear-gradient(135deg,#f9fafb,#ffffff);border-radius:8px;border:1px solid #e5e7eb">
                <span style="width:12px;height:12px;border-radius:4px;background:${color};box-shadow:0 2px 4px rgba(0,0,0,0.1)"></span>
                <span style="color:var(--gray-700);flex:1;font-weight:500">${escapeHtml(String(label))}</span>
                <span style="font-weight:700;color:var(--gray-800)">${pct}%</span>
            </div>
        `;
    });

    // Total summary
    const totalFormatted = formatNumber(total);
    const totalFull = total.toLocaleString('en-IN', { maximumFractionDigits: 2 });

    return `
        <div style="display:flex;gap:24px;align-items:center;flex-wrap:wrap">
            <div class="chart-pie-container" style="flex:1;min-width:180px">
                <canvas id="${chartId}"></canvas>
            </div>
            <div style="flex:1;min-width:180px">
                <div style="font-size:11px;font-weight:700;color:var(--gray-400);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px">Distribution</div>
                ${legendItems}
            </div>
        </div>
        <div class="chart-total-summary" style="margin-top:16px;padding:12px 16px;background:linear-gradient(135deg,#f0f9f0,#e8f5e8);border-radius:10px;border:1px solid #b7e4c7;display:flex;align-items:center;justify-content:space-between">
            <div style="display:flex;align-items:center;gap:10px">
                <div style="width:36px;height:36px;background:#1B4332;border-radius:8px;display:flex;align-items:center;justify-content:center">
                    <i class="fas fa-calculator" style="color:white;font-size:14px"></i>
                </div>
                <div>
                    <div style="font-size:11px;font-weight:600;color:#1B4332;text-transform:uppercase;letter-spacing:0.5px">Total</div>
                    <div style="font-size:10px;color:#6b7280">${totalFull} ${escapeHtml(unit)}</div>
                </div>
            </div>
            <div style="text-align:right">
                <div style="font-size:22px;font-weight:700;color:#1B4332">${totalFormatted}</div>
                <div style="font-size:11px;color:#6b7280">${escapeHtml(unit)}</div>
            </div>
        </div>
    `;
}

// ============================================================
// LINE CHART - Area with Gradient Fill
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

    // Add original query display
    let originalQueryHtml = '';
    if (metadata.original_query) {
        originalQueryHtml = `
            <div class="original-query-section" style="margin-top:12px;padding:10px 12px;background:linear-gradient(135deg,#f0f9f0,#e8f5e8);border-radius:8px;border:1px solid #b7e4c7">
                <div style="font-size:11px;font-weight:700;color:#1B4332;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px">
                    <i class="fas fa-comment-dots" style="margin-right:4px"></i> Your Query
                </div>
                <div style="font-size:13px;color:#1B4332;font-style:italic">"${escapeHtml(metadata.original_query)}"</div>
            </div>
        `;
    }

    // Add parsed query section for verification
    let parsedQueryHtml = '';
    if (metadata.parsed_query) {
        const pq = metadata.parsed_query;
        const queryItems = [];

        if (pq.indicator) queryItems.push({ label: 'Indicator', value: pq.indicator });
        if (pq.dimension) queryItems.push({ label: 'Dimension', value: pq.dimension });
        if (pq.crop_filter) queryItems.push({ label: 'Crop Filter', value: pq.crop_filter });
        if (pq.season_filter) queryItems.push({ label: 'Season Filter', value: pq.season_filter });
        if (pq.year_filter) queryItems.push({ label: 'Year Filter', value: pq.year_filter });
        if (pq.comparison_type) queryItems.push({ label: 'Comparison', value: pq.comparison_type });
        if (pq.top_n) queryItems.push({ label: 'Top N', value: pq.top_n });

        if (queryItems.length > 0) {
            parsedQueryHtml = `
                <div class="parsed-query-section" style="margin-top:12px;padding-top:12px;border-top:1px dashed #e5e7eb">
                    <div style="font-size:11px;font-weight:700;color:#1B4332;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px">
                        <i class="fas fa-code" style="margin-right:4px"></i> Parsed Query
                    </div>
                    ${queryItems.map(item => `
                        <div class="metadata-row">
                            <span class="label">${item.label}</span>
                            <span class="value" style="color:#1B4332;font-weight:600">${item.value}</span>
                        </div>
                    `).join('')}
                </div>
            `;
        }
    }

    // Add data query (SQL-like) section
    let dataQueryHtml = '';
    if (metadata.data_query) {
        const dq = metadata.data_query;
        dataQueryHtml = `
            <div class="data-query-section" style="margin-top:12px;padding-top:12px;border-top:1px dashed #e5e7eb">
                <div style="font-size:11px;font-weight:700;color:#2D6A4F;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px">
                    <i class="fas fa-database" style="margin-right:4px"></i> Data Query
                </div>
                <div class="metadata-row">
                    <span class="label">Table</span>
                    <span class="value" style="color:#2D6A4F;font-weight:600">${dq.table}</span>
                </div>
                <div class="metadata-row">
                    <span class="label">Column</span>
                    <span class="value" style="color:#2D6A4F;font-weight:600">${dq.column}</span>
                </div>
                ${dq.group_by ? `
                <div class="metadata-row">
                    <span class="label">Group By</span>
                    <span class="value" style="color:#2D6A4F;font-weight:600">${dq.group_by}</span>
                </div>
                ` : ''}
                <div style="margin-top:10px;padding:10px;background:#f0f9f0;border-radius:6px;border:1px solid #b7e4c7">
                    <div style="font-size:10px;color:#2D6A4F;font-weight:600;margin-bottom:4px">SQL Preview:</div>
                    <code style="font-size:11px;color:#1B4332;word-break:break-all;display:block">${escapeHtml(dq.sql_preview)}</code>
                </div>
            </div>
        `;
    }

    if (items.length === 0 && !parsedQueryHtml && !originalQueryHtml && !dataQueryHtml) return '';

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
            ${originalQueryHtml}
            ${rows}
            ${parsedQueryHtml}
            ${dataQueryHtml}
        </div>
    `;
}

// ============================================================
// CHART INITIALIZATION - Premium Styling
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
            // Create gradient backgrounds for each bar
            const barGradients = values.map((_, i) => {
                const gradient = ctx.createLinearGradient(0, 0, 400, 0);
                const colorPair = COLORS.gradients[i % COLORS.gradients.length];
                gradient.addColorStop(0, colorPair[0]);
                gradient.addColorStop(1, colorPair[1]);
                return gradient;
            });

            config = {
                type: 'bar',
                data: {
                    labels: labels.map(l => truncateLabel(String(l), 15)),
                    datasets: [{
                        data: values,
                        backgroundColor: barGradients,
                        borderRadius: 8,
                        borderSkipped: false,
                        maxBarThickness: 40,
                        hoverBackgroundColor: COLORS.chart.slice(0, values.length)
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    indexAxis: 'y',
                    animation: {
                        duration: 1200,
                        easing: 'easeOutQuart'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(17, 24, 39, 0.95)',
                            titleFont: { size: 13, weight: '600' },
                            bodyFont: { size: 12 },
                            padding: 14,
                            cornerRadius: 10,
                            displayColors: true,
                            boxPadding: 6,
                            callbacks: {
                                label: ctx => ` ${formatNumber(ctx.raw)} ${unit}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: {
                                color: 'rgba(0,0,0,0.04)',
                                drawBorder: false
                            },
                            ticks: {
                                font: { size: 11, weight: '500' },
                                color: '#6b7280',
                                callback: v => formatNumber(v)
                            }
                        },
                        y: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 11, weight: '500' },
                                color: '#374151'
                            }
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
                        borderWidth: 3,
                        borderColor: '#ffffff',
                        hoverBorderWidth: 4,
                        hoverBorderColor: '#ffffff',
                        hoverOffset: 15,
                        cutout: '60%',
                        spacing: 2
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        animateRotate: true,
                        animateScale: true,
                        duration: 1500,
                        easing: 'easeOutElastic'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(17, 24, 39, 0.95)',
                            titleFont: { size: 13, weight: '600' },
                            bodyFont: { size: 12 },
                            padding: 14,
                            cornerRadius: 10,
                            displayColors: true,
                            boxPadding: 6,
                            callbacks: {
                                label: ctx => {
                                    const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                                    const pct = ((ctx.raw / total) * 100).toFixed(1);
                                    return ` ${formatNumber(ctx.raw)} ${unit} (${pct}%)`;
                                }
                            }
                        }
                    }
                }
            };
            break;

        case 'line':
            // Create gradient fill
            const lineGradient = ctx.createLinearGradient(0, 0, 0, 200);
            lineGradient.addColorStop(0, 'rgba(27, 67, 50, 0.25)');
            lineGradient.addColorStop(0.5, 'rgba(45, 106, 79, 0.12)');
            lineGradient.addColorStop(1, 'rgba(82, 183, 136, 0.02)');

            config = {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        data: values,
                        borderColor: '#1B4332',
                        backgroundColor: lineGradient,
                        fill: true,
                        tension: 0.4,
                        borderWidth: 3,
                        pointRadius: 5,
                        pointBackgroundColor: '#ffffff',
                        pointBorderColor: '#1B4332',
                        pointBorderWidth: 3,
                        pointHoverRadius: 8,
                        pointHoverBackgroundColor: '#1B4332',
                        pointHoverBorderColor: '#ffffff',
                        pointHoverBorderWidth: 3
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(17, 24, 39, 0.95)',
                            titleFont: { size: 13, weight: '600' },
                            bodyFont: { size: 12 },
                            padding: 14,
                            cornerRadius: 10,
                            displayColors: false,
                            callbacks: {
                                label: ctx => `${formatNumber(ctx.raw)} ${unit}`
                            }
                        }
                    },
                    scales: {
                        x: {
                            grid: { display: false },
                            ticks: {
                                font: { size: 11, weight: '500' },
                                color: '#6b7280'
                            }
                        },
                        y: {
                            grid: {
                                color: 'rgba(0,0,0,0.04)',
                                drawBorder: false
                            },
                            ticks: {
                                font: { size: 11, weight: '500' },
                                color: '#6b7280',
                                callback: v => formatNumber(v)
                            },
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
                    <p style="margin-top:4px;font-size:13px;">${escapeHtml(message)}</p>
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
        kpi: 'fa-gauge-high',
        multi_kpi: 'fa-layer-group',
        bar: 'fa-chart-bar',
        pie: 'fa-chart-pie',
        line: 'fa-chart-line'
    };
    return icons[type] || 'fa-chart-simple';
}

function scrollToBottom(container) {
    if (container) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
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
        setTimeout(() => overlay.remove(), 300);
    }
}
