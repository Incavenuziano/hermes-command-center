async function fetchJson(path, options = {}) {
  const response = await fetch(path, {
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error?.message || 'Request failed');
  }
  return payload;
}

const iconPaths = {
  dashboard: 'M3 3h7v9H3zM14 3h7v5h-7zM14 12h7v9h-7zM3 16h7v5H3z',
  activity: 'M3 12h4l3-9 4 18 3-9h4',
  usage: 'M3 3v18h18M7 14l4-4 4 4 5-7',
  agents: 'M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM4 21a8 8 0 0 1 16 0',
  search: 'M21 21l-4.3-4.3M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0z',
  refresh: 'M23 4v6h-6M1 20v-6h6M3.5 9a9 9 0 0 1 14.8-3.4L23 10M1 14l4.7 4.4A9 9 0 0 0 20.5 15',
  filter: 'M22 3H2l8 9.5V19l4 2v-8.5z',
  download: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3',
  dot: 'M12 13a1 1 0 1 0 0-2 1 1 0 0 0 0 2z'
};

function renderIcon(name, size = 14, stroke = 1.75) {
  const d = iconPaths[name] || iconPaths.dot;
  return `<svg viewBox="0 0 24 24" width="${size}" height="${size}" fill="none" stroke="currentColor" stroke-width="${stroke}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`;
}

function setText(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

function setMarkup(id, markup) {
  const node = document.getElementById(id);
  if (node) node.innerHTML = markup;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatDateTime(value) {
  if (!value) return 'n/a';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toISOString().replace('T', ' ').replace('.000Z', ' UTC').replace('Z', ' UTC');
}

function formatNumber(value) {
  const num = Number(value);
  if (!Number.isFinite(num)) return String(value ?? '0');
  return new Intl.NumberFormat('pt-BR').format(num);
}

function formatCurrency(value) {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'USD' }).format(Number(value || 0));
}

function buildStatusTone(value) {
  const normalized = String(value || 'unknown').toLowerCase();
  if (['ok', 'healthy', 'connected', 'running', 'active', 'enabled', 'passed'].includes(normalized)) return 'accent';
  if (['warning', 'warn'].includes(normalized)) return 'warn';
  if (['failed', 'error', 'offline', 'disconnected', 'blocked', 'denied', 'danger'].includes(normalized)) return 'danger';
  return 'neutral';
}

function buildKeyValueGrid(pairs = []) {
  return `<dl class="detail-kv-grid">${pairs.map(([label, value]) => `<div class="detail-kv-row"><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value ?? 'n/a')}</dd></div>`).join('')}</dl>`;
}

function buildDetailSection(title, body) {
  return `<section class="detail-section"><h3>${escapeHtml(title)}</h3>${body}</section>`;
}

function buildStatusPill(label, value) {
  return `<div class="detail-pill-row"><span class="detail-pill-label">${escapeHtml(label)}</span><span class="memory-scope-pill ${buildStatusTone(value)}">${escapeHtml(value ?? 'n/a')}</span></div>`;
}

function buildMetricBar(label, value, total, meta = '') {
  return `<div class="metric-bar"><div class="metric-bar-head"><span>${escapeHtml(label)}</span><strong>${escapeHtml(meta || formatNumber(value || 0))}</strong></div>${buildProgressBar(value || 0, total || 1, (value || 0) > (total || 0) * 0.5 ? 'warn' : 'ok')}</div>`;
}

function buildMessageCard(item) {
  const role = item.role || 'unknown';
  const toolCalls = Array.isArray(item.tool_calls) ? item.tool_calls : [];
  const toolMarkup = toolCalls.map(tool => `<div class="chat-message-tool"><strong>${escapeHtml(tool.name || 'tool')}</strong><span>${escapeHtml(tool.arguments || '')}</span></div>`).join('');
  return `<article class="chat-inspector-card"><div class="chat-inspector-head"><span class="memory-scope-pill ${buildStatusTone(role === 'assistant' ? 'ok' : role === 'tool' ? 'warning' : 'unknown')}">${escapeHtml(role)}</span><span class="detail-meta-inline">mensagem ${escapeHtml(item.message_id || 'n/a')}</span></div><div class="chat-content">${escapeHtml(item.content || '(empty)')}</div>${toolMarkup}</article>`;
}

function renderDetailCard(id, sections) {
  setMarkup(id, `<div class="detail-card-shell">${sections.join('')}</div>`);
}

function renderDetailError(id, title, message) {
  renderDetailCard(id, [
    buildDetailSection(title, `<p class="detail-body-copy">${escapeHtml(message || 'Falha ao carregar detalhes.')}</p>`),
  ]);
}

function clearRoot(elementId) {
  const root = document.getElementById(elementId);
  if (!root) return null;
  root.innerHTML = '';
  return root;
}

function renderEmpty(root, label = 'Nenhum item ainda') {
  if (!root) return;
  const li = document.createElement('li');
  li.className = 'empty';
  li.textContent = label;
  root.appendChild(li);
}

function actionButton(label, onClick, variant = 'secondary') {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = `action-button ${variant}`;
  button.textContent = label;
  button.addEventListener('click', onClick);
  return button;
}

function decoratePrimaryActions() {
  document.querySelectorAll('#page-export-button, #usage-breaker-submit, #cron-refresh-button').forEach(node => {
    node?.classList.add('primary');
  });
}

const PAGE_META = {
  '/': { key: 'dashboard', title: 'Dashboard', subtitle: 'Visão geral do centro de comando', sections: ['dashboard-section', 'dashboard-overview-section'] },
  '/activity': { key: 'activity', title: 'Atividade', subtitle: 'Timeline de eventos ao vivo', sections: ['activity-page-section'] },
  '/usage': { key: 'usage', title: 'Uso', subtitle: 'Tokens · custo · burn rate', sections: ['usage-page-section'] },
  '/agents': { key: 'agents', title: 'Agentes', subtitle: 'Supervisão multiagente', sections: ['agents-page-section'] },
  '/chat': { key: 'chat', title: 'Conversar', subtitle: 'Transcript ativo do agente', sections: ['chat-page-section'] },
  '/sessions': { key: 'sessions', title: 'Sessões', subtitle: 'Histórico e detalhes da sessão', sections: ['sessions-page-section'] },
  '/tasks': { key: 'tasks', title: 'Tarefas', subtitle: 'Backlog operacional', sections: ['tasks-page-section'] },
  '/cron': { key: 'cron', title: 'Crons', subtitle: 'Jobs agendados e histórico', sections: ['cron-page-section'] },
  '/calendar': { key: 'calendar', title: 'Calendário', subtitle: '', sections: ['calendar-page-section'] },
  '/integrations': { key: 'integrations', title: 'Integrações', subtitle: '', sections: ['integrations-page-section'] },
  '/skill': { key: 'skill', title: 'Skills', subtitle: 'Catálogo de skills do agente', sections: ['skill-page-section'] },
  '/memory': { key: 'memory', title: 'Memória', subtitle: 'Entradas de memória por escopo', sections: ['memory-page-section'] },
  '/documents': { key: 'documents', title: 'Documentos', subtitle: 'Arquivos do workspace', sections: ['documents-page-section'] },
  '/database': { key: 'database', title: 'DataBase', subtitle: '', sections: ['database-page-section'] },
  '/apis': { key: 'apis', title: 'API\'s', subtitle: '', sections: ['apis-page-section'] },
  '/channels': { key: 'channels', title: 'Canais', subtitle: 'Gateway e status dos canais', sections: ['channels-page-section'] },
  '/hooks': { key: 'hooks', title: 'Segurança Hooks', subtitle: 'Security hooks', sections: ['hooks-page-section'] },
  '/preferences': { key: 'preferences', title: 'Preferências', subtitle: 'Profiles and rules', sections: ['preferences-page-section'] },
  '/doctor': { key: 'doctor', title: 'Diagnóstico', subtitle: 'Diagnóstico operacional', sections: ['doctor-page-section'] },
  '/terminal': { key: 'terminal', title: 'Terminal', subtitle: 'Postura de risco · shell interativo', sections: ['terminal-policy-section'] },
  '/logs': { key: 'logs', title: 'Logs', subtitle: 'Fluxo estruturado de eventos', sections: ['logs-page-section'] },
  '/tailscale': { key: 'tailscale', title: 'Tailscale', subtitle: 'Postura de rede', sections: ['tailscale-page-section'] },
  '/config': { key: 'config', title: 'Config', subtitle: '', sections: ['config-page-section'] },
  '/skills': { key: 'skill', title: 'Skills', subtitle: 'Catálogo de skills do agente', sections: ['skill-page-section'] },
  '/files': { key: 'documents', title: 'Documentos', subtitle: 'Workspace files', sections: ['documents-page-section'] },
  '/profiles': { key: 'preferences', title: 'Preferências', subtitle: 'Profiles and rules', sections: ['preferences-page-section'] },
};

const activePage = PAGE_META[window.location.pathname] || PAGE_META['/'];
const DESIGN_ADVISOR_AGENT_ID = 'HCC-design-advisor';
const SHELL_MARKERS = ['topbar-breadcrumb', 'global-search-shortcut', 'page-theme-pill'];
const DASHBOARD_MARKERS = ['dashboard-stat-grid', 'dashboard-live-activity', 'dashboard-top-agents', 'dashboard-cron-overview', 'dashboard-hero-chart', 'dashboard-kpi-card', 'live-activity-feed'];
const ACTIVITY_MARKERS = ['activity-filter-bar', 'activity-summary-grid'];
const OPS_PAGE_MARKERS = ['cron-quick-actions', 'doctor-summary-grid', 'logs-filter-bar', 'logs-detail', 'usage-main-chart', 'sidebar-collapse-button', 'page-subtitle', 'usage-breaker-card', 'usage-agent-share-bar'];
const NAV_ITEM_MARKERS = ['nav-item-label', 'nav-item-badge', 'topbar-clock'];
const SPLIT_VIEW_MARKERS = ['agent-list-row', 'agent-detail-card', 'agent-session-table', 'session-list-row', 'chat-message-card', 'chat-message-tool'];
const OPS_DEEP_MARKERS = ['cron-split-view', 'cron-job-table', 'cron-output-terminal', 'doctor-diagnostics-table', 'logs-live-stream'];
let activeChatStream = null;
let activeSessionId = null;
let activityPageLimit = 20;
let activityKindPrefix = '';
let designAdvisorCatalog = null;

function renderCurrentPage() {
  document.querySelectorAll('.page-section').forEach(section => section.classList.remove('active'));
  for (const sectionId of activePage.sections) {
    document.getElementById(sectionId)?.classList.add('active');
  }
  setText('page-heading', activePage.title);
  setText('page-subtitle', activePage.subtitle || '');
  setText('breadcrumb-current', activePage.title);
  document.querySelectorAll('[data-nav-item]').forEach(link => {
    link.classList.toggle('active', link.dataset.navItem === activePage.key);
  });
}

function toggleSidebar() {
  const shell = document.getElementById('app-shell');
  shell.classList.toggle('sidebar-collapsed');
  persistShellPreferences();
}

function restoreShellPreferences() {
  try {
    const saved = JSON.parse(window.localStorage.getItem('hcc-shell-preferences') || '{}');
    if (saved.sidebarCollapsed) {
      document.getElementById('app-shell')?.classList.add('sidebar-collapsed');
    }
  } catch (_) {}
}

function persistShellPreferences() {
  const shell = document.getElementById('app-shell');
  const payload = { sidebarCollapsed: shell?.classList.contains('sidebar-collapsed') || false };
  try {
    window.localStorage.setItem('hcc-shell-preferences', JSON.stringify(payload));
  } catch (_) {}
}

function filterSidebar(term) {
  const value = term.trim().toLowerCase();
  document.querySelectorAll('.nav-sector a').forEach(link => {
    link.style.display = !value || link.textContent.toLowerCase().includes(value) ? '' : 'none';
  });
}

function closeChatStream() {
  if (activeChatStream) {
    activeChatStream.close();
    activeChatStream = null;
  }
}

function setChatSummary(session, count) {
  const parts = [session.platform || 'unknown platform', session.model || 'unknown model', `${count} message(s)`];
  setText('chat-session-summary', parts.join(' · '));
}

function renderChatTranscript(items) {
  const root = clearRoot('chat-transcript');
  if (!root) return;
  if (!items.length) {
    renderEmpty(root, 'Nenhuma mensagem no transcript ainda');
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card chat-message chat-message-card';
    const role = document.createElement('div');
    role.className = 'chat-role';
    role.textContent = `${item.message_id}. ${item.role || 'unknown'}`;
    const content = document.createElement('div');
    content.className = 'chat-content';
    content.textContent = item.content || '(empty)';
    li.append(role, content);
    if (Array.isArray(item.tool_calls) && item.tool_calls.length) {
      const tool = document.createElement('div');
      tool.className = 'chat-message-tool';
      tool.textContent = `${item.tool_calls[0].name || 'tool'} · ${item.tool_calls[0].arguments || ''}`;
      li.append(tool);
    }
    li.addEventListener('click', () => renderDetailCard('chat-inspector', [
      buildDetailSection('Mensagem', buildMessageCard(item)),
      buildDetailSection('Metadados', buildKeyValueGrid([
        ['ID', item.message_id || 'n/a'],
        ['Papel', item.role || 'unknown'],
        ['Tool calls', String((item.tool_calls || []).length)],
      ])),
    ]));
    root.appendChild(li);
  }
  renderDetailCard('chat-inspector', items.length ? [
    buildDetailSection('Mensagem', buildMessageCard(items[0])),
    buildDetailSection('Metadados', buildKeyValueGrid([
      ['ID', items[0].message_id || 'n/a'],
      ['Papel', items[0].role || 'unknown'],
      ['Tool calls', String((items[0].tool_calls || []).length)],
    ])),
  ] : [buildDetailSection('Mensagem', '<p class="panel-caption">Nenhuma mensagem selecionada.</p>')]);
}

function renderListInto(rootId, items, formatter, emptyLabel = 'No items yet') {
  const root = clearRoot(rootId);
  if (!root) return;
  if (!items.length) {
    renderEmpty(root, emptyLabel);
    return;
  }
  for (const item of items) {
    root.appendChild(formatter(item));
  }
}

function card(titleText, metaText, controls = []) {
  const li = document.createElement('li');
  li.className = 'item-card';
  const title = document.createElement('div');
  title.className = 'item-title';
  title.textContent = titleText;
  const meta = document.createElement('div');
  meta.className = 'item-meta';
  meta.textContent = metaText;
  li.append(title, meta);
  if (controls.length) {
    const row = document.createElement('div');
    row.className = 'actions-row';
    controls.forEach(control => row.append(control));
    li.append(row);
  }
  return li;
}

function buildSparkline(values = []) {
  return `<svg class="sparkline" viewBox="0 0 120 40" preserveAspectRatio="none"><polyline fill="none" stroke="currentColor" stroke-width="2" points="${values.map((value, index) => `${index * 20},${40 - Math.min(36, value)}`).join(' ')}"></polyline></svg>`;
}

function buildStatCard(label, value, tone = 'neutral') {
  return `<div class="usage-stat-card hc-stat dashboard-kpi-card ${tone}"><div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>${buildSparkline([8, 12, 16, 22, 18, 26])}</div>`;
}

function buildProgressBar(value, max = 100, tone = 'neutral') {
  const pct = Math.max(0, Math.min(100, Math.round((Number(value || 0) / Math.max(1, Number(max || 1))) * 100)));
  return `<div class="usage-agent-share-bar"><div class="usage-agent-share-bar-fill ${tone}" style="width:${pct}%"></div></div>`;
}

function buildUsageAreaChart(values = []) {
  const safe = values.length ? values : [12, 18, 16, 24, 22, 28, 26, 32, 30, 34, 31, 36];
  const width = 800;
  const height = 180;
  const pad = 16;
  const max = Math.max(...safe, 1);
  const step = (width - pad * 2) / Math.max(1, safe.length - 1);
  const pts = safe.map((v, i) => [pad + i * step, height - pad - (v / max) * (height - pad * 2)]);
  const line = pts.map((p, i) => `${i ? 'L' : 'M'}${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(' ');
  const area = `${line} L${width - pad},${height - pad} L${pad},${height - pad} Z`;
  const circles = pts.filter((_, i) => i % 4 === 0).map(p => `<circle cx="${p[0]}" cy="${p[1]}" r="2"></circle>`).join('');
  return `<svg class="usage-area-chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none"><defs><linearGradient id="usage-area-gradient" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--accent)" stop-opacity="0.35"></stop><stop offset="100%" stop-color="var(--accent)" stop-opacity="0"></stop></linearGradient></defs><path d="${area}" fill="url(#usage-area-gradient)"></path><path d="${line}" fill="none" stroke="var(--accent)" stroke-width="1.75"></path>${circles}</svg>`;
}

function buildTimelineItem(item) {
  const li = document.createElement('li');
  li.className = 'item-card hc-feed-item';
  li.innerHTML = `<div class="item-title">${item.kind || 'event'}</div><div class="item-meta">${item.at || 'n/a'} ← ${item.source || 'unknown'}</div>`;
  return li;
}

function buildScopePill(text, tone = 'neutral', className = 'memory-scope-pill') {
  return `<span class="${className} ${tone}">${text}</span>`;
}

async function loadChatTranscript(sessionId) {
  const payload = await fetchJson(`/ops/chat/transcript?session_id=${encodeURIComponent(sessionId)}`);
  setChatSummary(payload.data.session, payload.data.count || 0);
  const items = payload.data.items || [];
  renderChatTranscript(items);
  renderListInto('sessions-related-transcript', items.slice(0, 4), item => card(`${item.message_id}. ${item.role || 'unknown'}`, item.content || '(empty)'), 'No transcript preview yet');
  setText('chat-stream-status', `Transcript carregado para ${sessionId}`);
}

function openChatStream(sessionId) {
  closeChatStream();
  activeChatStream = new EventSource(`/ops/chat/stream?session_id=${encodeURIComponent(sessionId)}`);
  setText('chat-stream-status', 'Transmitindo transcript ao vivo…');
  activeChatStream.addEventListener('chat.session', event => {
    const payload = JSON.parse(event.data);
    setChatSummary(payload, payload.message_count || 0);
  });
  activeChatStream.addEventListener('chat.message', () => loadChatTranscript(sessionId).catch(error => setText('chat-stream-status', error.message)));
  activeChatStream.onerror = () => {
    setText('chat-stream-status', 'Stream do chat desconectado.');
    closeChatStream();
  };
}

async function handleProcessKill(processId) {
  await fetchJson('/ops/processes/kill', { method: 'POST', body: JSON.stringify({ process_id: processId }) });
  await fetchOverview();
}

async function handleProcessControl(processId, action) {
  await fetchJson('/ops/processes/control', { method: 'POST', body: JSON.stringify({ process_id: processId, action }) });
  await fetchOverview();
}

async function handleCronAction(jobId, action) {
  await fetchJson('/ops/cron/control', { method: 'POST', body: JSON.stringify({ job_id: jobId, action }) });
  await fetchOverview();
}

async function handleApprovalDecision(itemId, decision) {
  await fetchJson('/ops/approvals/resolve', { method: 'POST', body: JSON.stringify({ item_id: itemId, decision }) });
  await fetchOverview();
}

async function handleGatewayRuntimeAction() {
  const current = await fetchJson('/ops/gateway-runtime');
  const action = current.data.status === 'online' ? 'kill' : 'start';
  const payload = await fetchJson('/ops/gateway-runtime', { method: 'POST', body: JSON.stringify({ action }) });
  renderGatewayRuntime(payload.data);
}

function renderGatewayRuntime(payload) {
  const statusNode = document.getElementById('gateway-runtime-status');
  if (statusNode) {
    statusNode.textContent = payload.status || 'offline';
    statusNode.classList.toggle('online', payload.status === 'online');
    statusNode.classList.toggle('offline', payload.status !== 'online');
  }
  setText('gateway-runtime-button', payload.action_label || 'Iniciar gateway');
}

function renderSystemHealth(systemInfo, health) {
  renderListInto('system-health', [
    ['Service', systemInfo.service || 'unknown'],
    ['Bind', systemInfo.bind || 'unknown'],
    ['Auth', systemInfo.auth_mode || 'unknown'],
    ['Overall', health.overall_status || 'unknown'],
    ['Runtime', health.runtime?.status || 'unknown'],
    ['Event Bus', health.event_bus?.status || 'unknown'],
  ], ([label, value]) => card(label, value));
  setText('system-summary', `${systemInfo.environment || 'unknown'} · ${health.overall_status || 'unknown'}`);
}

function renderActivityPage(items, retention) {
  const maxItems = retention && typeof retention.max_items === 'number' ? retention.max_items : items.length;
  setText('activity-window-summary', `Exibindo ${items.length} de ${maxItems} evento(s) retidos. Janela operacional ${activityPageLimit}.`);
  const summaryRoot = clearRoot('activity-summary-grid');
  if (summaryRoot) {
    [
      ['Visible Events', String(items.length)],
      ['Retained Max', String(maxItems)],
      ['Approvals', String(items.filter(item => (item.kind || '').startsWith('approval')).length)],
      ['Process Events', String(items.filter(item => (item.kind || '').startsWith('process')).length)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card activity-summary-stat';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('activity-page-list', items, item => {
    const node = buildTimelineItem(item);
    node.classList.add('activity-feed-card');
    node.insertAdjacentHTML('afterbegin', `<div class="activity-feed-meta">${buildScopePill(item.kind || 'event', 'neutral', 'activity-kind-pill')}</div>`);
    const actions = document.createElement('div');
    actions.className = 'actions-row';
    actions.appendChild(actionButton('Inspecionar evento', () => renderDetailCard('activity-drilldown', [
      buildDetailSection('Evento', `${buildStatusPill('Tipo', item.kind || 'event')}<p class="detail-body-copy">${escapeHtml(item.title || 'Sem título')}</p><p class="panel-caption">${escapeHtml(item.detail || 'Sem detalhe adicional.')}</p>`),
      buildDetailSection('Metadados', buildKeyValueGrid([
        ['Origem', item.source || 'unknown'],
        ['Registrado em', formatDateTime(item.at)],
        ['Status', item.status || 'n/a'],
      ])),
    ])));
    node.appendChild(actions);
    return node;
  }, 'Nenhum evento de atividade ainda');
  const drilldown = document.getElementById('activity-drilldown');
  drilldown?.classList.add('activity-detail-card');
  renderDetailCard('activity-drilldown', items.length ? [
    buildDetailSection('Evento', `${buildStatusPill('Tipo', items[0].kind || 'event')}<p class="detail-body-copy">${escapeHtml(items[0].title || 'Sem título')}</p><p class="panel-caption">${escapeHtml(items[0].detail || 'Sem detalhe adicional.')}</p>`),
    buildDetailSection('Metadados', buildKeyValueGrid([
      ['Origem', items[0].source || 'unknown'],
      ['Registrado em', formatDateTime(items[0].at)],
      ['Status', items[0].status || 'n/a'],
    ])),
  ] : [buildDetailSection('Evento', '<p class="panel-caption">Nenhum evento selecionado.</p>')]);
}

async function loadActivityPage() {
  const suffix = activityKindPrefix ? `&kind_prefix=${encodeURIComponent(activityKindPrefix)}` : '';
  const payload = await fetchJson(`/ops/activity?limit=${encodeURIComponent(activityPageLimit)}${suffix}`);
  renderActivityPage(payload.data.items || [], payload.data.retention || {});
}

function renderApprovals(items) {
  const pendingCount = items.filter(item => item.status === 'pending').length;
  setText('approvals-summary', pendingCount ? `${pendingCount} item(ns) pendente(s)` : 'Nenhuma aprovação pendente.');
  renderListInto('approvals-list', items, item => card(`${item.title} · ${item.status}`, `${item.kind} · ${item.source}`, item.status === 'pending' && Array.isArray(item.choices) ? item.choices.map(choice => actionButton(choice, () => handleApprovalDecision(item.id, choice))) : []), 'Nenhuma aprovação ainda');
}

function renderDashboardPremium(overview, cronJobs) {
  const agents = overview.agents || [];
  const cronItems = cronJobs.items || [];
  renderListInto('dashboard-top-agents-list', agents.slice(0, 4), item => {
    const node = card(`${item.agent_id} · ${item.status}`, `${item.role || 'worker'} · última atividade ${item.last_seen_at || 'n/a'}`, []);
    node.insertAdjacentHTML('afterbegin', `<div class="profile-card-head">${buildScopePill(item.status || 'unknown', buildStatusTone(item.status || 'unknown'), 'profile-sensitivity-pill')}</div>`);
    return node;
  }, 'Nenhum agente ainda');
  renderListInto('dashboard-cron-list', cronItems.slice(0, 4), item => {
    const node = card(`${item.name} · ${item.status}`, `${item.schedule || 'manual'} · próxima execução ${item.next_run_at || 'n/a'}`);
    node.insertAdjacentHTML('afterbegin', `<div class="channel-card-head">${buildScopePill(item.status || 'unknown', buildStatusTone(item.status || 'unknown'), 'channel-platform-pill')}</div>`);
    return node;
  }, 'Nenhum cron ainda');
  setText('dashboard-top-agents-summary', agents.length ? `${agents.length} agente(s) monitorado(s)` : 'Nenhum agente na visão geral.');
  setText('dashboard-cron-summary', cronItems.length ? `${cronItems.length} cron(s) agendado(s)` : 'Nenhum cron disponível.');
  const hero = document.getElementById('dashboard-hero-chart');
  if (hero) {
    const chart = hero.querySelector('.dashboard-hero-chart');
    if (chart) chart.innerHTML = buildUsageAreaChart((overview.sessions || []).map((_, index) => 12 + index * 4).concat([20, 28, 24, 32, 30, 38]));
  }
}

function renderEvents(items) {
  renderListInto('events-list', items, item => {
    const node = buildTimelineItem(item);
    node.insertAdjacentHTML('beforeend', `<div class="detail-meta-inline">${escapeHtml(item.detail || 'Sem detalhe adicional.')}</div>`);
    return node;
  });
  renderLogsPremium(items);
}

function renderAgentsPage(agents, sessions, processes) {
  const selectedAgent = agents[0] || null;
  renderListInto('agents-page-list', agents, agent => {
    const relatedSession = sessions.find(item => item.status === 'active') || sessions[0];
    const runningProcess = processes.find(item => item.status === 'running');
    const controls = [];
    if (relatedSession) {
      controls.push(actionButton('Abrir sessão', async () => {
        activeSessionId = relatedSession.session_id;
        await loadSessionDetail(relatedSession.session_id);
        await loadChatTranscript(relatedSession.session_id);
        openChatStream(relatedSession.session_id);
      }));
    }
    if (runningProcess) {
      controls.push(actionButton('Encerrar processo', () => handleProcessKill(runningProcess.process_id), 'danger'));
    }
    controls.push(actionButton('Inspecionar agente', () => renderAgentDetail(agent, sessions)));
    const cardNode = card(`${agent.agent_id} · ${agent.status}`, `${agent.role || 'worker'} · last seen ${agent.last_seen_at || 'n/a'}`, controls);
    cardNode.classList.add('agent-list-row');
    return cardNode;
  }, 'No agents yet');
  renderAgentDetail(selectedAgent, sessions);
}

function renderAgentDetail(agent, sessions) {
  if (!agent) {
    setText('agents-page-detail', 'Nenhum agente selecionado.');
    renderListInto('agents-page-sessions', [], () => null, 'No sessions for this agent.');
    const emptyStats = clearRoot('agents-page-stats');
    if (emptyStats) emptyStats.textContent = 'Nenhuma métrica ainda';
    return;
  }
  const relatedSessions = (sessions || []).filter(item => item.agent_id === agent.agent_id || item.agent_id === 'agent-main').slice(0, 4);
  const statsRoot = clearRoot('agents-page-stats');
  if (statsRoot) {
    [
      ['Agent', agent.agent_id],
      ['Status', agent.status || 'unknown'],
      ['Role', agent.role || 'worker'],
      ['Last Seen', agent.last_seen_at || 'n/a'],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      statsRoot.appendChild(block);
    });
  }
  renderDetailCard('agents-page-detail', [
    buildDetailSection('Resumo do agente', `${buildStatusPill('Status', agent.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(agent.agent_id)}</strong><span>${escapeHtml(agent.role || 'worker')}</span></div>`),
    buildDetailSection('Metadados', buildKeyValueGrid([
      ['Agent ID', agent.agent_id],
      ['Role', agent.role || 'worker'],
      ['Status', agent.status || 'unknown'],
      ['Última atividade', formatDateTime(agent.last_seen_at)],
    ])),
    buildDetailSection('Atividade recente', buildMetricBar('Sessões recentes', relatedSessions.length, Math.max(relatedSessions.length, 1), `${relatedSessions.length} sessões`)),
  ]);
  document.getElementById('agents-page-detail')?.classList.add('agent-detail-card');
  renderListInto('agents-page-sessions', relatedSessions, item => {
    const node = card(`${item.session_id} · ${item.status}`, `${item.platform || item.source || 'unknown'} · ${item.title || 'Untitled'}`, [actionButton('Abrir sessão', async () => {
      activeSessionId = item.session_id;
      await loadSessionDetail(item.session_id);
      await loadChatTranscript(item.session_id);
      openChatStream(item.session_id);
    })]);
    node.classList.add('agent-session-table');
    return node;
  }, 'No sessions for this agent.');
}

async function loadSessionDetail(sessionId) {
  const payload = await fetchJson(`/ops/session?session_id=${encodeURIComponent(sessionId)}`);
  const session = payload.data.session || {};
  renderDetailCard('session-detail', [
    buildDetailSection('Resumo da sessão', `${buildStatusPill('Status', session.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(session.title || session.session_id || 'Untitled')}</strong><span>${escapeHtml(session.platform || session.source || 'unknown')}</span></div>`),
    buildDetailSection('Metadados', buildKeyValueGrid([
      ['Session ID', session.session_id || 'n/a'],
      ['Modelo', session.model || 'unknown'],
      ['Usuário', session.display_name || session.user_id || 'n/a'],
      ['Início', formatDateTime(session.started_at)],
      ['Atualizado', formatDateTime(session.updated_at)],
    ])),
    buildDetailSection('Uso', buildKeyValueGrid([
      ['Input tokens', formatNumber(session.input_tokens || 0)],
      ['Output tokens', formatNumber(session.output_tokens || 0)],
      ['Reasoning tokens', formatNumber(session.reasoning_tokens || 0)],
      ['Custo real', formatCurrency(session.actual_cost_usd || 0)],
    ])),
  ]);
}

function renderSessions(items) {
  renderSessionsPremium(items);
}

function renderSessionsPremium(items) {
  const statsRoot = clearRoot('sessions-stats');
  if (statsRoot) {
    [
      ['Sessions', String(items.length)],
      ['Active', String(items.filter(item => item.status === 'active').length)],
      ['Platforms', String(new Set(items.map(item => item.platform || item.source || 'unknown')).size)],
      ['Models', String(new Set(items.map(item => item.model || 'unknown')).size)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      statsRoot.appendChild(block);
    });
  }
  renderListInto('sessions-list', items, item => {
    const node = card(`${item.session_id} · ${item.status}`, `${item.platform || item.source || 'unknown'} · ${item.title || 'Untitled'}`, [actionButton('Inspecionar', async () => {
      activeSessionId = item.session_id;
      await loadSessionDetail(item.session_id);
      await loadChatTranscript(item.session_id);
      openChatStream(item.session_id);
    })]);
    node.classList.add('session-list-row');
    return node;
  });
  renderListInto('sessions-related-transcript', [], () => null, 'Inspect a session to load transcript preview.');
}

function renderProcessesPage(items) {
  renderListInto('processes-page-list', items, item => {
    const controls = [actionButton('Inspecionar processo', () => renderDetailCard('processes-page-detail', [
      buildDetailSection('Processo', `${buildStatusPill('Status', item.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(item.process_id || 'process')}</strong><span>${escapeHtml(item.command || 'no command')}</span></div>`),
      buildDetailSection('Metadados', buildKeyValueGrid([
        ['PID', item.pid ?? 'n/a'],
        ['Started', formatDateTime(item.started_at)],
        ['Exit code', item.exit_code ?? 'n/a'],
      ])),
    ]))];
    if (item.status === 'running') controls.push(actionButton('Encerrar processo', () => handleProcessControl(item.process_id, 'kill'), 'danger'));
    return card(`${item.process_id} · ${item.status}`, `${item.command || 'no command'} · pid ${item.pid ?? 'n/a'}`, controls);
  }, 'Nenhum processo ainda');
  setText('processes-page-summary', items.length ? `${items.length} processo(s) no registro.` : 'Nenhum processo no registro.');
  if (items.length) {
    const first = items[0];
    renderDetailCard('processes-page-detail', [
      buildDetailSection('Processo', `${buildStatusPill('Status', first.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(first.process_id || 'process')}</strong><span>${escapeHtml(first.command || 'no command')}</span></div>`),
      buildDetailSection('Metadados', buildKeyValueGrid([
        ['PID', first.pid ?? 'n/a'],
        ['Started', formatDateTime(first.started_at)],
        ['Exit code', first.exit_code ?? 'n/a'],
      ])),
    ]);
  } else {
    setText('processes-page-detail', 'Nenhum processo selecionado.');
  }
}

function renderProcesses(items) {
  renderProcessesPage(items);
}

function renderCronPage(jobs, historyItems) {
  const summaryRoot = clearRoot('cron-summary-grid');
  if (summaryRoot) {
    [
      ['Cron Jobs', String(jobs.length)],
      ['Enabled', String(jobs.filter(item => item.enabled).length)],
      ['Run Requested', String(jobs.filter(item => item.status === 'run_requested').length)],
      ['History Items', String(historyItems.length)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('cron-page-list', jobs, job => card(`${job.name} · ${job.status}`, `${job.schedule || 'manual'} · next ${job.next_run_at || 'n/a'}`, [
    actionButton('Inspecionar histórico', async () => {
      const payload = await fetchJson(`/ops/cron/history?job_id=${encodeURIComponent(job.job_id)}`);
      renderCronPage(jobs, payload.data.items || []);
      renderDetailCard('cron-output-inspection', [
        buildDetailSection('Job', `${buildStatusPill('Status', job.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(job.name || job.job_id)}</strong><span>${escapeHtml(job.schedule || 'manual')}</span></div>`),
        buildDetailSection('Histórico', buildKeyValueGrid((payload.data.items || []).slice(0, 4).map(item => [formatDateTime(item.recorded_at), `${item.action || 'run'} · ${item.status || 'unknown'}`]))),
      ]);
    }),
    actionButton('Executar', () => handleCronAction(job.job_id, 'run')),
    actionButton(job.enabled ? 'Pausar' : 'Retomar', () => handleCronAction(job.job_id, job.enabled ? 'pause' : 'resume')),
  ]), 'Nenhum cron ainda');
  renderListInto('cron-run-history', historyItems, item => card(`${item.job_id} · ${item.action}`, `${item.recorded_at || 'n/a'} · ${item.status}`), 'No cron history yet');
  if (jobs.length && !historyItems.length) {
    const first = jobs[0];
    renderDetailCard('cron-output-inspection', [
      buildDetailSection('Job', `${buildStatusPill('Status', first.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(first.name || first.job_id)}</strong><span>${escapeHtml(first.schedule || 'manual')}</span></div>`),
      buildDetailSection('Próxima execução', buildKeyValueGrid([
        ['Next run', formatDateTime(first.next_run_at)],
        ['Enabled', first.enabled ? 'yes' : 'no'],
      ])),
    ]);
  }
}

function renderTerminalPolicyPage(policy) {
  const summaryRoot = clearRoot('terminal-summary-grid');
  if (summaryRoot) {
    [
      ['Mode', policy.mode || 'unknown'],
      ['Interactive', policy.interactive_terminal_enabled ? 'enabled' : 'disabled'],
      ['Risk', policy.risk_posture || 'unknown'],
      ['Revisit', policy.revisit_in_milestone || 'unspecified'],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card terminal-summary-stat';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('terminal-policy-list', [
    ['Mode', policy.mode || 'unknown'],
    ['Interactive Terminal', policy.interactive_terminal_enabled ? 'enabled' : 'disabled'],
    ['Risk Posture', policy.risk_posture || 'unknown'],
    ['Revisit', policy.revisit_in_milestone || 'unspecified'],
  ], ([label, value]) => {
    const node = card(label, value);
    node.insertAdjacentHTML('afterbegin', `<div class="terminal-card-head">${buildScopePill(label, 'neutral', 'terminal-mode-pill')}</div>`);
    return node;
  });
  setText('terminal-policy-summary', `${policy.mode || 'unknown'} · ${policy.risk_posture || 'unknown'}`);
  document.getElementById('terminal-policy-detail')?.classList.add('terminal-policy-card');
  renderDetailCard('terminal-policy-detail', [
    buildDetailSection('Postura operacional', `${buildStatusPill('Modo', policy.mode || 'unknown')}${buildStatusPill('Risco', policy.risk_posture || 'unknown')}`),
    buildDetailSection('Política', buildKeyValueGrid([
      ['Terminal interativo', policy.interactive_terminal_enabled ? 'enabled' : 'disabled'],
      ['Milestone revisit', policy.revisit_in_milestone || 'unspecified'],
      ['Reason', policy.reason || 'n/a'],
    ])),
  ]);
}

function renderMemoryPage(payload) {
  const items = payload.items || [];
  const counts = payload.counts || {};
  const summaryRoot = clearRoot('memory-summary-grid');
  if (summaryRoot) {
    [
      ['Memory', String(counts.memory || 0)],
      ['User', String(counts.user || 0)],
      ['Visible', String(items.length)],
      ['Freshest', items[0]?.updated_at || 'n/a'],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card memory-summary-stat';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('memory-page-list', items, item => {
    const node = card(`${item.scope}`, item.preview || item.text, [actionButton('Inspecionar', () => renderDetailCard('memory-page-detail', [
      buildDetailSection('Entrada', `${buildStatusPill('Escopo', item.scope || 'memory')}<p class="detail-body-copy">${escapeHtml(item.text || item.preview || '(empty)')}</p>`),
      buildDetailSection('Metadados', buildKeyValueGrid([
        ['Updated', formatDateTime(item.updated_at)],
        ['Kind', item.kind || 'note'],
        ['Preview', item.preview || 'n/a'],
      ])),
    ]))]);
    node.insertAdjacentHTML('afterbegin', `<div class="memory-item-head">${buildScopePill(item.scope || 'memory', item.scope === 'user' ? 'accent' : 'neutral')}</div>`);
    return node;
  }, 'Nenhuma entrada de memória ainda');
  setText('memory-page-summary', `${counts.memory || 0} memória / ${counts.user || 0} entrada(s) de usuário`);
  const detailNode = document.getElementById('memory-page-detail');
  detailNode?.classList.add('memory-detail-card');
  if (items.length) {
    const first = items[0];
    renderDetailCard('memory-page-detail', [
      buildDetailSection('Entrada', `${buildStatusPill('Escopo', first.scope || 'memory')}<p class="detail-body-copy">${escapeHtml(first.text || first.preview || '(empty)')}</p>`),
      buildDetailSection('Metadados', buildKeyValueGrid([
        ['Updated', formatDateTime(first.updated_at)],
        ['Kind', first.kind || 'note'],
        ['Preview', first.preview || 'n/a'],
      ])),
    ]);
  } else {
    setText('memory-page-detail', 'Nenhuma entrada de memória selecionada.');
  }
}

function renderSkillsPage(payload) {
  const items = payload.items || [];
  renderListInto('skills-page-list', items, item => card(item.skill_id, item.preview || item.title, [actionButton('Inspecionar', () => renderDetailCard('skills-page-detail', [
    buildDetailSection('Skill', `${buildStatusPill('ID', item.skill_id || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(item.title || item.skill_id || 'Untitled')}</strong><span>${escapeHtml(item.path || 'skills')}</span></div>`),
    buildDetailSection('Preview', `<p class="detail-body-copy">${escapeHtml(item.preview || 'No preview available.')}</p>`),
  ]))]), 'No skills yet');
  setText('skills-page-summary', `${payload.count || items.length} skill(s)`);
  if (items.length) {
    const first = items[0];
    renderDetailCard('skills-page-detail', [
      buildDetailSection('Skill', `${buildStatusPill('ID', first.skill_id || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(first.title || first.skill_id || 'Untitled')}</strong><span>${escapeHtml(first.path || 'skills')}</span></div>`),
      buildDetailSection('Preview', `<p class="detail-body-copy">${escapeHtml(first.preview || 'No preview available.')}</p>`),
    ]);
  } else {
    setText('skills-page-detail', 'Nenhuma skill selecionada.');
  }
}

function applyDesignAdvisorPromptSuggestion(prompt) {
  const input = document.getElementById('design-advisor-prompt');
  if (input) input.value = prompt;
}

function renderDesignAdvisorCatalog(payload) {
  designAdvisorCatalog = payload;
  const preset = payload.surface_presets?.[activePage.key] || payload.surface_presets?.skills || null;
  const suggestions = preset?.prompt_suggestions || payload.prompt_starters || [];
  const buttons = suggestions.map(prompt => `[${prompt}]`).join(' ');
  const lines = [
    `Catalog Agent: ${payload.agent?.id || DESIGN_ADVISOR_AGENT_ID}`,
    `Supported Surfaces: ${(payload.supported_page_types || []).join(', ')}`,
    '',
    'Prompt Suggestions:',
    ...suggestions.map(item => `- ${item}`),
  ];
  setText('design-advisor-catalog', lines.join('\n'));
  setText('design-advisor-prompt-suggestions', buttons || 'No prompt suggestions available.');
}

function renderDesignAdvisor(payload) {
  const recommendation = payload.recommendation || {};
  const lines = [
    `Agent: ${payload.agent?.id || DESIGN_ADVISOR_AGENT_ID}`,
    `Page Type: ${recommendation.page_type || 'unknown'}`,
    `Visual Profile: ${recommendation.visual_profile || 'unknown'}`,
    `Best-Fit Style: ${recommendation.best_fit_style || 'unknown'}`,
    `Layout: ${recommendation.layout_pattern || 'unknown'}`,
    '',
    'Color Direction:',
    ...((recommendation.color_direction || []).map(item => `- ${item}`)),
    '',
    'Typography Direction:',
    ...((recommendation.typography_direction || []).map(item => `- ${item}`)),
    '',
    'Interaction Cues:',
    ...((recommendation.interaction_cues || []).map(item => `- ${item}`)),
    '',
    'Avoid:',
    ...((recommendation.avoid || []).map(item => `- ${item}`)),
    '',
    'Implementation Notes:',
    ...((recommendation.implementation_notes || []).map(item => `- ${item}`)),
    '',
    'Recommended Components:',
    ...((recommendation.recommended_components || []).map(item => `- ${item}`)),
    '',
    'Next Actions:',
    ...((recommendation.next_actions || []).map(item => `- ${item}`)),
  ];
  setText('design-advisor-result', lines.join('\n'));
}

async function requestDesignAdvisorRecommendation() {
  const prompt = document.getElementById('design-advisor-prompt')?.value || 'Refine the current operator surface.';
  const payload = await fetchJson('/ops/design-advisor/recommend', {
    method: 'POST',
    body: JSON.stringify({
      page_type: activePage.key || 'dashboard',
      intent: prompt,
      visual_profile: 'premium-dark-ops',
    }),
  });
  renderDesignAdvisor(payload.data || {});
}

async function loadDesignAdvisorCatalog() {
  const payload = await fetchJson('/ops/design-advisor/catalog');
  renderDesignAdvisorCatalog(payload.data || {});
}

function renderUsagePage(payload) {
  const totals = payload.totals || {};
  const breaker = payload.circuit_breaker || {};
  const topSessions = payload.top_sessions || [];
  const agentBreakdown = payload.agent_breakdown || [];
  const performance = payload.performance || {};
  const loadSmoke = payload.load_smoke || {};
  const summaryCards = payload.summary_cards || [];
  const usageChart = document.getElementById('usage-main-chart');
  if (usageChart) {
    usageChart.innerHTML = buildUsageAreaChart(agentBreakdown.map((item, index) => Number(item.total_tokens || 0) / 1000 || (index + 1) * 6));
  }
  renderListInto('usage-list', [
    ['Total Tokens', String(totals.total_tokens || 0)],
    ['Actual Cost USD', String(totals.actual_cost_usd || 0)],
    ['Estimated Cost USD', String(totals.estimated_cost_usd || 0)],
    ['Circuit Breaker', breaker.tripped ? `tripped (${(breaker.reasons || []).join(', ')})` : 'healthy'],
    ['Route Count', String(performance.snapshot?.route_count || 0)],
    ['Load Smoke Failures', String(loadSmoke.failures || 0)],
  ], ([label, value]) => card(label, value));
  renderListInto('usage-agent-breakdown', agentBreakdown, item => {
    const share = Number(item.total_tokens || 0);
    const total = Number(totals.total_tokens || 0);
    const wrap = document.createElement('li');
    wrap.className = 'item-card';
    wrap.innerHTML = `<div class="item-title">${item.agent_id} · ${item.session_count} session(s)</div><div class="item-meta">${item.total_tokens} tokens · $${item.actual_cost_usd || 0}</div>${buildProgressBar(share, total || 1, share > total * 0.5 ? 'warn' : 'ok')}`;
    const row = document.createElement('div');
    row.className = 'actions-row';
    row.appendChild(actionButton('Inspecionar agente', () => renderDetailCard('usage-detail', [buildDetailSection('Agente', `${buildStatusPill('Agent', item.agent_id || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(item.agent_id || 'agent')}</strong><span>${escapeHtml(formatNumber(item.total_tokens || 0))} tokens</span></div>`), buildDetailSection('Metadados', buildKeyValueGrid([['Sessions', item.session_count || 0], ['Actual cost', formatCurrency(item.actual_cost_usd || 0)], ['Top sessions', topSessions.length]]))])));
    wrap.appendChild(row);
    return wrap;
  }, 'Nenhum uso por agente ainda');
  const shareRoot = clearRoot('usage-agent-share-bar');
  if (shareRoot) {
    agentBreakdown.slice(0, 4).forEach(item => {
      const lane = document.createElement('div');
      lane.className = 'usage-agent-share-lane';
      lane.innerHTML = `<span class="usage-agent-share-label">${item.agent_id}</span>${buildProgressBar(item.total_tokens || 0, totals.total_tokens || 1, (item.total_tokens || 0) > (totals.total_tokens || 0) * 0.5 ? 'warn' : 'ok')}`;
      shareRoot.appendChild(lane);
    });
  }
  renderListInto('usage-top-sessions', topSessions, item => card(`${item.session_id} · ${item.title || 'Untitled'}`, `${item.total_tokens || (Number(item.input_tokens || 0) + Number(item.output_tokens || 0) + Number(item.reasoning_tokens || 0))} tokens · $${item.actual_cost_usd || 0}`, [actionButton('Inspecionar sessão', () => renderDetailCard('usage-detail', [buildDetailSection('Sessão de uso', `${buildStatusPill('Session', item.session_id || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(item.title || item.session_id || 'Untitled')}</strong><span>${escapeHtml(formatCurrency(item.actual_cost_usd || 0))}</span></div>`), buildDetailSection('Metadados', buildKeyValueGrid([['Tokens', formatNumber(item.total_tokens || (Number(item.input_tokens || 0) + Number(item.output_tokens || 0) + Number(item.reasoning_tokens || 0)))], ['Input', formatNumber(item.input_tokens || 0)], ['Output', formatNumber(item.output_tokens || 0)], ['Reasoning', formatNumber(item.reasoning_tokens || 0)]]))]))]), 'No sessions yet');
  const statGrid = clearRoot('usage-stat-grid');
  if (statGrid) {
    if (!summaryCards.length) {
      statGrid.textContent = 'Nenhum card de resumo ainda';
    } else {
      summaryCards.forEach(cardItem => {
        statGrid.insertAdjacentHTML('beforeend', buildStatCard(cardItem.label, cardItem.value, cardItem.tone || 'neutral'));
      });
    }
  }
  const perf = document.getElementById('usage-performance-summary');
  if (perf) {
    perf.textContent = `Performance routes ${performance.snapshot?.route_count || 0} · retained window ${performance.budgets?.max_default_list_window || 0} · load smoke failures ${loadSmoke.failures || 0}`;
  }
  setText('usage-summary', `${totals.total_tokens || 0} tokens · $${totals.actual_cost_usd || 0} real · breaker ${breaker.tripped ? 'acionado' : 'saudável'}`);
  renderDetailCard('usage-detail', [buildDetailSection('Resumo de uso', `${buildStatusPill('Breaker', breaker.tripped ? 'tripped' : 'healthy')}<div class="detail-hero-line"><strong>${escapeHtml(formatNumber(totals.total_tokens || 0))} tokens</strong><span>${escapeHtml(formatCurrency(totals.actual_cost_usd || 0))}</span></div>`), buildDetailSection('Metadados', buildKeyValueGrid([['Estimated cost', formatCurrency(totals.estimated_cost_usd || 0)], ['Load smoke failures', loadSmoke.failures || 0], ['Routes', performance.snapshot?.route_count || 0], ['Top sessions', topSessions.length]]))]);
  const costInput = document.getElementById('usage-max-cost');
  const tokenInput = document.getElementById('usage-max-tokens');
  if (costInput && typeof breaker.max_actual_cost_usd !== 'undefined' && breaker.max_actual_cost_usd !== null) costInput.value = breaker.max_actual_cost_usd;
  if (tokenInput && typeof breaker.max_total_tokens !== 'undefined' && breaker.max_total_tokens !== null) tokenInput.value = breaker.max_total_tokens;
}

async function requestUsageCircuitBreakerUpdate() {
  const maxCostRaw = document.getElementById('usage-max-cost')?.value || '';
  const maxTokensRaw = document.getElementById('usage-max-tokens')?.value || '';
  await fetchJson('/ops/costs/circuit-breaker', {
    method: 'POST',
    body: JSON.stringify({
      max_actual_cost_usd: maxCostRaw ? Number(maxCostRaw) : null,
      max_total_tokens: maxTokensRaw ? Number(maxTokensRaw) : null,
    }),
  });
  const usagePayload = await fetchJson('/ops/usage');
  renderUsagePage(usagePayload.data || {});
}

function renderFilesPage(payload) {
  const items = payload.items || [];
  const summaryRoot = clearRoot('documents-summary-grid');
  if (summaryRoot) {
    [
      ['Files', String(payload.count || items.length)],
      ['Workspace', payload.root || 'n/a'],
      ['Largest', items.length ? `${Math.max(...items.map(item => Number(item.size_bytes || 0)))} B` : '0 B'],
      ['First Path', items[0]?.path || 'n/a'],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card documents-summary-stat';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('files-page-list', items, item => {
    const node = card(item.path, item.preview, [actionButton('Inspecionar', () => renderDetailCard('files-page-detail', [buildDetailSection('Arquivo', `${buildStatusPill('Path', item.path || 'file')}<p class="detail-body-copy">${escapeHtml(item.preview || 'Sem preview')}</p>`), buildDetailSection('Metadados', buildKeyValueGrid([['Size', formatNumber(item.size_bytes || 0)], ['Root', payload.root || 'n/a'], ['Path', item.path || 'n/a']]))]))]);
    node.insertAdjacentHTML('afterbegin', `<div class="document-card-head">${buildScopePill(item.path || 'file', 'neutral', 'document-path-chip')}</div>`);
    return node;
  }, 'Nenhum arquivo ainda');
  setText('files-page-summary', `${payload.count || items.length} arquivo(s)`);
  const fileDetailNode = document.getElementById('files-page-detail');
  fileDetailNode?.classList.add('files-detail-card');
  if (items.length) { const first = items[0]; renderDetailCard('files-page-detail', [buildDetailSection('Arquivo', `${buildStatusPill('Path', first.path || 'file')}<p class="detail-body-copy">${escapeHtml(first.preview || 'Sem preview')}</p>`), buildDetailSection('Metadados', buildKeyValueGrid([['Size', formatNumber(first.size_bytes || 0)], ['Root', payload.root || 'n/a'], ['Path', first.path || 'n/a']]))]); } else { setText('files-page-detail', 'Nenhum arquivo selecionado.'); }
}

function renderProfilesPage(payload) {
  const items = payload.items || [];
  const summaryRoot = clearRoot('profiles-summary-grid');
  if (summaryRoot) {
    [
      ['Profiles', String(payload.count || items.length)],
      ['Active', payload.active_profile_id || 'none'],
      ['High Sensitivity', String(items.filter(item => item.sensitivity === 'high').length)],
      ['Reauth', String(items.filter(item => item.requires_reauth).length)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card profiles-summary-stat';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('profiles-page-list', items, item => {
    const node = card(item.label || item.id, `${item.sensitivity} · reauth ${item.requires_reauth ? 'yes' : 'no'}`, [actionButton('Inspecionar', () => renderDetailCard('profiles-page-detail', [buildDetailSection('Perfil', `${buildStatusPill('Sensibilidade', item.sensitivity || 'standard')}<div class="detail-hero-line"><strong>${escapeHtml(item.label || item.id || 'profile')}</strong><span>${escapeHtml(item.requires_reauth ? 'reauth required' : 'trusted local')}</span></div>`), buildDetailSection('Metadados', buildKeyValueGrid([['ID', item.id || 'n/a'], ['Requires reauth', item.requires_reauth ? 'yes' : 'no'], ['Sensitivity', item.sensitivity || 'standard']]))]))]);
    node.insertAdjacentHTML('afterbegin', `<div class="profile-card-head">${buildScopePill(item.sensitivity || 'standard', item.sensitivity === 'high' ? 'accent' : 'neutral', 'profile-sensitivity-pill')}</div>`);
    return node;
  }, 'Nenhum perfil ainda');
  setText('profiles-page-summary', `ativo ${payload.active_profile_id || 'nenhum'} · ${payload.count || items.length} perfil(is)`);
  document.getElementById('profiles-page-detail')?.classList.add('profiles-detail-card');
  if (items.length) { const first = items[0]; renderDetailCard('profiles-page-detail', [buildDetailSection('Perfil', `${buildStatusPill('Sensibilidade', first.sensitivity || 'standard')}<div class="detail-hero-line"><strong>${escapeHtml(first.label || first.id || 'profile')}</strong><span>${escapeHtml(first.requires_reauth ? 'reauth required' : 'trusted local')}</span></div>`), buildDetailSection('Metadados', buildKeyValueGrid([['ID', first.id || 'n/a'], ['Active', payload.active_profile_id === first.id ? 'yes' : 'no'], ['Requires reauth', first.requires_reauth ? 'yes' : 'no']]))]); } else { setText('profiles-page-detail', 'No profile selected.'); }
}

function renderChannelsPage(payload) {
  const items = payload.channels || [];
  const summaryRoot = clearRoot('channels-summary-grid');
  if (summaryRoot) {
    [
      ['Channels', String(payload.count || items.length)],
      ['Gateway', payload.gateway?.status || 'unknown'],
      ['Platforms', String(new Set(items.map(item => item.platform || 'unknown')).size)],
      ['Connected', String(items.filter(item => item.delivery_state === 'connected').length)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card channels-summary-stat';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('channels-page-list', items, item => {
    const node = card(item.label || item.id, `${item.platform || 'unknown'} · ${item.delivery_state || 'unknown'}`, [actionButton('Inspecionar', () => renderDetailCard('channels-page-detail', [buildDetailSection('Canal', `${buildStatusPill('Entrega', item.delivery_state || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(item.label || item.id || 'channel')}</strong><span>${escapeHtml(item.platform || 'unknown')}</span></div>`), buildDetailSection('Gateway', buildKeyValueGrid([['Gateway status', payload.gateway?.status || 'unknown'], ['Platform', item.platform || 'unknown'], ['Channel ID', item.id || 'n/a']]))]))]);
    node.insertAdjacentHTML('afterbegin', `<div class="channel-card-head">${buildScopePill(item.platform || 'unknown', item.delivery_state === 'connected' ? 'accent' : 'neutral', 'channel-platform-pill')}</div>`);
    return node;
  }, 'Nenhum canal ainda');
  setText('channels-page-summary', `${payload.gateway?.status || 'unknown'} gateway · ${payload.count || items.length} canal(is)`);
  document.getElementById('channels-page-detail')?.classList.add('channels-detail-card');
  if (items.length) { const first = items[0]; renderDetailCard('channels-page-detail', [buildDetailSection('Canal', `${buildStatusPill('Entrega', first.delivery_state || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(first.label || first.id || 'channel')}</strong><span>${escapeHtml(first.platform || 'unknown')}</span></div>`), buildDetailSection('Gateway', buildKeyValueGrid([['Gateway status', payload.gateway?.status || 'unknown'], ['Platform', first.platform || 'unknown'], ['Channel ID', first.id || 'n/a']]))]); } else { setText('channels-page-detail', 'No channel selected.'); }
}

function renderDoctorPremium(health, securityAudit, performance, loadSmoke) {
  const summaryRoot = clearRoot('doctor-summary-grid');
  if (summaryRoot) {
    [
      ['Health', health.data?.overall_status || 'unknown'],
      ['Security', securityAudit.data?.overall_status || 'unknown'],
      ['Routes', String(performance.data?.snapshot?.route_count || 0)],
      ['Load Smoke', String(loadSmoke.data?.failures || 0)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
}

function renderDoctorPage({ health, securityAudit, performance, loadSmoke }) {
  const items = [
    ['Health', health.data?.overall_status || 'unknown'],
    ['Security Audit', securityAudit.data?.overall_status || 'unknown'],
    ['Performance Routes', String(performance.data?.snapshot?.route_count || 0)],
    ['Load Smoke Failures', String(loadSmoke.data?.failures || 0)],
  ];
  renderDoctorPremium(health, securityAudit, performance, loadSmoke);
  renderListInto('doctor-list', items, ([label, value]) => card(label, value));
  renderDetailCard('doctor-detail', [buildDetailSection('Saúde geral', `${buildStatusPill('Health', health.data?.overall_status || 'unknown')}${buildStatusPill('Security', securityAudit.data?.overall_status || 'unknown')}`), buildDetailSection('Diagnóstico', buildKeyValueGrid([['Route count', performance.data?.snapshot?.route_count || 0], ['Load smoke failures', loadSmoke.data?.failures || 0], ['Environment', health.data?.details?.environment || 'development'], ['Mode', health.data?.details?.mode || 'unknown']]))]);
}

function renderLogsPremium(items) {
  renderListInto('logs-list', items, item => card(item.kind || 'event', `${item.at || 'n/a'} ← ${item.source || 'unknown'}`, [actionButton('Inspecionar log', () => renderDetailCard('logs-detail', [buildDetailSection('Log event', `${buildStatusPill('Tipo', item.kind || 'event')}<p class=\"detail-body-copy\">${escapeHtml(item.title || item.kind || 'Event')}</p><p class=\"panel-caption\">${escapeHtml(item.detail || 'No extra detail.')}</p>`), buildDetailSection('Metadados', buildKeyValueGrid([['Source', item.source || 'unknown'], ['Recorded at', formatDateTime(item.at)], ['Status', item.status || 'n/a']]))]))]), 'No logs/events yet');
  if (items.length) { const first = items[0]; renderDetailCard('logs-detail', [buildDetailSection('Log event', `${buildStatusPill('Tipo', first.kind || 'event')}<p class=\"detail-body-copy\">${escapeHtml(first.title || first.kind || 'Event')}</p><p class=\"panel-caption\">${escapeHtml(first.detail || 'No extra detail.')}</p>`), buildDetailSection('Metadados', buildKeyValueGrid([['Source', first.source || 'unknown'], ['Recorded at', formatDateTime(first.at)], ['Status', first.status || 'n/a']]))]); } else { setText('logs-detail', 'Nenhum log selecionado.'); }
}

function renderTailscalePage(systemInfo, gatewayPayload) {
  const items = [
    ['Bind', systemInfo.data?.bind || 'unknown'],
    ['Auth', systemInfo.data?.auth_mode || 'unknown'],
    ['Gateway', gatewayPayload.data?.gateway?.status || 'unknown'],
  ];
  renderListInto('tailscale-list', items, ([label, value]) => card(label, value));
  renderDetailCard('tailscale-detail', [buildDetailSection('Rede', `${buildStatusPill('Gateway', gatewayPayload.data?.gateway?.status || 'unknown')}<div class="detail-hero-line"><strong>${escapeHtml(systemInfo.data?.bind || 'unknown')}</strong><span>${escapeHtml(systemInfo.data?.auth_mode || 'unknown')}</span></div>`), buildDetailSection('Metadados', buildKeyValueGrid([['Environment', systemInfo.data?.environment || 'development'], ['Bind', systemInfo.data?.bind || 'unknown'], ['Auth mode', systemInfo.data?.auth_mode || 'unknown']]))]);
}

async function fetchOverview() {
  const session = await fetchJson('/auth/session');
  setText('generated-at', `Mode: ${session.data.auth_mode}`);
  const gatewayRuntime = await fetchJson('/ops/gateway-runtime');
  renderGatewayRuntime(gatewayRuntime.data);

  const overview = await fetchJson('/ops/overview');
  const approvals = await fetchJson('/ops/approvals');
  const systemInfo = await fetchJson('/system/info');
  const health = await fetchJson('/health');
  const cronJobs = await fetchJson('/ops/cron/jobs');
  const cronHistory = await fetchJson('/ops/cron/history');
  const processesRegistry = await fetchJson('/ops/processes');
  const terminalPolicy = await fetchJson('/ops/terminal-policy');
  const memoryPayload = await fetchJson('/ops/memory');
  const skillsPayload = await fetchJson('/ops/skills');
  const usagePayload = await fetchJson('/ops/usage');
  const filesPayload = await fetchJson('/ops/files');
  const profilesPayload = await fetchJson('/ops/profiles');
  const gatewayPayload = await fetchJson('/ops/gateway');
  const securityAudit = await fetchJson('/ops/security-audit');
  const performance = await fetchJson('/ops/performance');
  const loadSmoke = await fetchJson('/ops/load-smoke');
  await loadActivityPage();

  setText('count-agents', String(overview.data.counts.agents));
  setText('count-sessions', String(overview.data.counts.sessions));
  setText('count-processes', String(overview.data.counts.processes));
  setText('count-cron', String(overview.data.counts.cron_jobs));

  renderApprovals(approvals.data.items || []);
  renderDashboardPremium(overview.data || {}, cronJobs.data || {});
  renderEvents(overview.data.events || []);
  renderSystemHealth(systemInfo.data, health.data);
  renderAgentsPage(overview.data.agents || [], overview.data.sessions || [], overview.data.processes || []);
  renderSessions(overview.data.sessions || []);
  renderProcesses(processesRegistry.data.items || []);
  renderCronPage(cronJobs.data.items || [], cronHistory.data.items || []);
  renderTerminalPolicyPage(terminalPolicy.data || {});
  renderMemoryPage(memoryPayload.data || {});
  renderSkillsPage(skillsPayload.data || {});
  renderUsagePage(usagePayload.data || {});
  await loadDesignAdvisorCatalog();
  await requestDesignAdvisorRecommendation();
  renderFilesPage(filesPayload.data || {});
  renderProfilesPage(profilesPayload.data || {});
  renderChannelsPage(gatewayPayload.data || {});
  renderDoctorPage({ health, securityAudit, performance, loadSmoke });
  renderTailscalePage(systemInfo, gatewayPayload);

  if ((overview.data.sessions || []).length) {
    activeSessionId = overview.data.sessions[0].session_id;
    await loadSessionDetail(activeSessionId);
    await loadChatTranscript(activeSessionId);
    openChatStream(activeSessionId);
  } else {
    closeChatStream();
    setText('session-detail', 'Nenhuma sessão selecionada.');
    setText('chat-stream-status', 'Nenhuma sessão selecionada.');
    setText('chat-session-summary', 'Selecione uma sessão para carregar o transcript.');
    renderListInto('chat-transcript', [], () => null, 'Nenhuma mensagem no transcript ainda');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.documentElement.setAttribute('data-theme', 'premium');
  restoreShellPreferences();
  renderCurrentPage();
  decoratePrimaryActions();
  const updateClock = () => {
    const now = new Date();
    setText('topbar-clock', `${String(now.getUTCHours()).padStart(2, '0')}:${String(now.getUTCMinutes()).padStart(2, '0')}:${String(now.getUTCSeconds()).padStart(2, '0')} UTC`);
  };
  updateClock();
  window.setInterval(updateClock, 1000);
  document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);
  document.getElementById('sidebar-collapse-button')?.addEventListener('click', toggleSidebar);
  document.getElementById('global-search').addEventListener('input', event => filterSidebar(event.target.value));
  document.getElementById('gateway-runtime-button').addEventListener('click', () => handleGatewayRuntimeAction().catch(error => setText('gateway-runtime-status', error.message)));
  document.getElementById('activity-load-more').addEventListener('click', () => {
    activityPageLimit += 20;
    loadActivityPage().catch(error => setText('activity-window-summary', error.message));
  });
  document.getElementById('activity-filter-all')?.addEventListener('click', () => {
    activityKindPrefix = '';
    loadActivityPage().catch(error => setText('activity-window-summary', error.message));
  });
  document.getElementById('activity-filter-approvals')?.addEventListener('click', () => {
    activityKindPrefix = 'approval';
    loadActivityPage().catch(error => setText('activity-window-summary', error.message));
  });
  document.getElementById('activity-filter-process')?.addEventListener('click', () => {
    activityKindPrefix = 'process';
    loadActivityPage().catch(error => setText('activity-window-summary', error.message));
  });
  document.getElementById('cron-refresh-button')?.addEventListener('click', () => fetchOverview().catch(error => renderDetailError('cron-output-inspection', 'Erro de cron', error.message)));
  document.getElementById('logs-filter-all')?.addEventListener('click', () => {
    renderLogsPremium([]);
    fetchOverview().catch(error => renderDetailError('logs-detail', 'Erro de logs', error.message));
  });
  document.getElementById('logs-filter-approval')?.addEventListener('click', () => {
    fetchJson('/ops/activity?limit=20&kind_prefix=approval').then(payload => renderLogsPremium(payload.data.items || [])).catch(error => renderDetailError('logs-detail', 'Erro de logs', error.message));
  });
  document.getElementById('logs-filter-process')?.addEventListener('click', () => {
    fetchJson('/ops/activity?limit=20&kind_prefix=process').then(payload => renderLogsPremium(payload.data.items || [])).catch(error => renderDetailError('logs-detail', 'Erro de logs', error.message));
  });
  document.getElementById('design-advisor-run')?.addEventListener('click', () => requestDesignAdvisorRecommendation().catch(error => setText('design-advisor-result', error.message)));
  document.getElementById('usage-breaker-form')?.addEventListener('submit', event => {
    event.preventDefault();
    requestUsageCircuitBreakerUpdate().catch(error => renderDetailError('usage-detail', 'Erro de uso', error.message));
  });
  document.getElementById('refresh-button').addEventListener('click', () => fetchOverview().catch(error => setText('generated-at', error.message)));
  fetchOverview().catch(error => setText('generated-at', error.message));
  window.addEventListener('beforeunload', closeChatStream);
});
