const API_BASE = 'http://localhost:8000/api/v1/keepcon';

let keepconData = {
    metrics: { total: 0, negatives: 0, positives: 0, x_mentions: 0, fb_mentions: 0, ig_mentions: 0 },
    data: []
};

window.openX = function(url) {
    if(url) window.open(url, '_blank');
};

window.switchPage = function(pageId) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    if (event && event.currentTarget) {
        event.currentTarget.classList.add('active');
    }
    document.querySelectorAll('.page-section').forEach(sec => sec.classList.remove('active'));
    const target = document.getElementById('page-' + pageId);
    if (target) target.classList.add('active');
};

window.manualRefresh = async function() {
    const btn = event ? event.currentTarget : null;
    if (btn) {
        btn.innerHTML = '<span>🔄</span> Sincronizando...';
        btn.style.opacity = '0.6';
    }
    
    try {
        await fetch(`${API_BASE}/refresh`, { method: 'POST' });
        await window.reloadKeepcon();
    } catch(err) {
        console.error("Error refreshing:", err);
    } finally {
        if (btn) {
            btn.innerHTML = '<span>🔄</span> Refrescar Hoy';
            btn.style.opacity = '1';
        }
    }
};

window.reloadKeepcon = async function() {
    const days = document.getElementById('k-days-filter')?.value || 1;
    const sentiment = document.getElementById('k-sentiment-filter')?.value || 'todos';
    const source = document.getElementById('k-source-filter')?.value || 'todas';
    
    const feedContainer = document.getElementById('keepcon-feed');
    if (feedContainer) feedContainer.innerHTML = '<p style="text-align: center; color: #94A3B8; margin-top: 2rem;">Cargando datos históricos...</p>';
    
    try {
        const res = await fetch(`${API_BASE}/data?days=${days}&sentiment=${sentiment}&source=${source}`);
        const result = await res.json();
        
        if (result.status === 'success') {
            keepconData = result;
            updateDashboardDate();
            updateKPIs();
            initCharts();
            renderFeed();
        } else {
            console.error("Error from API:", result.message);
            if (feedContainer) feedContainer.innerHTML = `<p style="text-align: center; color: #F43F5E; margin-top: 2rem;">Error cargando datos: ${result.message}</p>`;
        }
    } catch (err) {
        console.error("Error fetching keepcon data:", err);
        if (feedContainer) feedContainer.innerHTML = '<p style="text-align: center; color: #F43F5E; margin-top: 2rem;">Error de conexión con el servidor.</p>';
    }
};

document.addEventListener('DOMContentLoaded', () => {
    window.reloadKeepcon();
    
    const intervalSeconds = parseInt(import.meta.env.VITE_REFRESH_INTERVAL_SECONDS || 300);
    
    // Update the UI indicator with the actual interval
    const refreshIndicator = document.querySelector('.sidebar p:nth-child(2)');
    if (refreshIndicator) {
        const minutes = Math.floor(intervalSeconds / 60);
        const seconds = intervalSeconds % 60;
        let timeStr = "";
        if (minutes > 0) timeStr += `${minutes}m `;
        if (seconds > 0 || minutes === 0) timeStr += `${seconds}s`;
        refreshIndicator.innerText = `● Actualización Automática: ${timeStr}`;
    }

    // Auto-update based on environment variable
    setInterval(() => {
        window.reloadKeepcon();
    }, intervalSeconds * 1000);
});

function updateDashboardDate() {
    const dateEl = document.getElementById('dashboard-date');
    if (dateEl) {
        const now = new Date();
        dateEl.innerText = `Monitoreo Estratégico Keepcon | Sincronizado: ${now.toLocaleTimeString()}`;
    }
}

function updateKPIs() {
    const setVal = (id, val) => { const el = document.getElementById(id); if (el) el.innerText = val; };
    setVal('kpi-total', keepconData.metrics.total.toLocaleString());
    setVal('kpi-negatives', keepconData.metrics.negatives.toLocaleString());
    setVal('kpi-x', keepconData.metrics.x_mentions.toLocaleString());
    setVal('kpi-fbig', (keepconData.metrics.fb_mentions + keepconData.metrics.ig_mentions).toLocaleString());
}

function initCharts() {
    if (typeof Chart === 'undefined') return;
    
    if (window.sChart) window.sChart.destroy();
    if (window.cChart) window.cChart.destroy();

    // Sentiment Chart
    const ctxS = document.getElementById('sentimentChart')?.getContext('2d');
    if (ctxS) {
        const totalSent = keepconData.data.reduce((acc, curr) => {
            if (curr.sentiment === 'positive') acc.pos++;
            else if (curr.sentiment === 'negative') acc.neg++;
            else if (curr.sentiment === 'neutral') acc.neu++;
            else acc.none++;
            return acc;
        }, { pos: 0, neg: 0, neu: 0, none: 0 });

        window.sChart = new Chart(ctxS, {
            type: 'doughnut',
            data: {
                labels: ['Positivo', 'Negativo', 'Neutral', 'Sin Sentimiento'],
                datasets: [{
                    data: [totalSent.pos, totalSent.neg, totalSent.neu, totalSent.none],
                    backgroundColor: ['#4ADE80', '#F43F5E', '#94A3B8', '#475569'],
                    borderWidth: 0
                }]
            },
            options: { responsive: true, maintainAspectRatio: false, cutout: '75%', plugins: { legend: { position: 'right', labels: { color: '#94A3B8' } } } }
        });
    }

    // Source Chart
    const ctxC = document.getElementById('competitorChart')?.getContext('2d');
    if (ctxC) {
        window.cChart = new Chart(ctxC, {
            type: 'bar',
            data: {
                labels: ['X', 'Facebook', 'Instagram'],
                datasets: [{
                    label: 'Volumen',
                    data: [keepconData.metrics.x_mentions, keepconData.metrics.fb_mentions, keepconData.metrics.ig_mentions],
                    backgroundColor: ['#0F1419', '#1877F2', '#E4405F'],
                    borderRadius: 8
                }]
            },
            options: { 
                responsive: true, maintainAspectRatio: false,
                scales: { y: { display: false }, x: { ticks: { color: '#94A3B8' }, grid: { display: false } } },
                plugins: { legend: { display: false } }
            }
        });
    }
}

function renderFeed() {
    const container = document.getElementById('keepcon-feed');
    const centralFeed = document.getElementById('liveFeed');
    
    if (!container) return;
    
    if (keepconData.data.length === 0) {
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: #94A3B8;">No hay datos para estos filtros.</div>';
        if(centralFeed) centralFeed.innerHTML = container.innerHTML;
        return;
    }

    const htmlContent = keepconData.data.map(item => {
        let sentColor = '#94A3B8';
        if (item.sentiment === 'negative') sentColor = '#F43F5E';
        if (item.sentiment === 'positive') sentColor = '#4ADE80';

        let sourceColor = '#38BDF8';
        let sourceIcon = '💬';
        let sourceName = 'Red';
        if (item.source === 'twitter') { sourceColor = '#0F1419'; sourceIcon = '𝕏'; sourceName = 'X'; }
        if (item.source === 'facebook') { sourceColor = '#1877F2'; sourceIcon = 'f'; sourceName = 'Facebook'; }
        if (item.source === 'instagram') { sourceColor = '#E4405F'; sourceIcon = '📸'; sourceName = 'Instagram'; }

        let typeTag = '';
        if (item.source === 'twitter' && item.content_type) {
            typeTag = `<span style="background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: #94A3B8; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; text-transform: uppercase;">📄 ${item.content_type}</span>`;
        }

        return `
        <div class="feed-item" style="cursor: default; padding: 15px; margin-bottom: 10px; background: rgba(255,255,255,0.03); border-radius: 12px; border-left: 4px solid ${sentColor}; transition: all 0.2s ease;">
            <div class="feed-meta" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="display: flex; gap: 8px; align-items: center;">
                    <span style="background: ${sourceColor}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                        ${sourceIcon} ${sourceName}
                    </span>
                    <span style="font-size: 0.75rem; color: #94A3B8; display: flex; align-items: center; gap: 4px;">
                        🕒 ${item.relative_time}
                    </span>
                    ${typeTag}
                </div>
                <span style="font-size: 0.7rem; padding: 2px 6px; border-radius: 4px; background: rgba(255,255,255,0.1); color: ${sentColor}; text-transform: uppercase;">
                    ${item.sentiment}
                </span>
            </div>
            <div class="feed-text" style="font-size: 0.9rem; line-height: 1.4; color: #E2E8F0;">
                <strong style="color: white;">@${item.username || item.user_name || 'Anónimo'}</strong>: ${item.text}
            </div>
            ${item.url ? `<div style="font-size: 0.75rem; margin-top: 10px; cursor: pointer; color: var(--accent-blue);" onclick="window.openX('${item.url}')">Abrir original ↗</div>` : ''}
        </div>
        `;
    }).join('');

    container.innerHTML = htmlContent;
    
    if (centralFeed) {
        // Only show last 4 on central dashboard
        centralFeed.innerHTML = keepconData.data.slice(0, 4).map(item => {
            let sentColor = '#94A3B8';
            if (item.sentiment === 'negative') sentColor = '#F43F5E';
            if (item.sentiment === 'positive') sentColor = '#4ADE80';
            return `
            <div class="feed-item" style="padding: 10px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                <div class="feed-meta" style="display: flex; justify-content: space-between;">
                    <span style="font-size: 0.7rem; color: ${sentColor}; text-transform: uppercase;">● ${item.sentiment}</span>
                    <span style="font-size: 0.7rem; color: #94A3B8;">${item.relative_time}</span>
                </div>
                <div style="font-size: 0.8rem; margin-top: 5px;"><strong>@${item.username}</strong>: ${item.text.substring(0, 80)}...</div>
            </div>`;
        }).join('');
    }
}
