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

function setText(id, text) {
  const node = document.getElementById(id);
  if (node) node.textContent = text;
}

function clearRoot(elementId) {
  const root = document.getElementById(elementId);
  if (!root) return null;
  root.innerHTML = '';
  return root;
}

function renderEmpty(root, label = 'No items yet') {
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

const PAGE_META = {
  '/': { key: 'dashboard', title: 'Dashboard', sections: ['dashboard-section', 'dashboard-overview-section'] },
  '/activity': { key: 'activity', title: 'Atividade', sections: ['activity-page-section'] },
  '/usage': { key: 'usage', title: 'Usage', sections: ['usage-page-section'] },
  '/agents': { key: 'agents', title: 'Agentes', sections: ['agents-page-section'] },
  '/chat': { key: 'chat', title: 'Conversar', sections: ['chat-page-section'] },
  '/sessions': { key: 'sessions', title: 'Sessões', sections: ['sessions-page-section'] },
  '/tasks': { key: 'tasks', title: 'Tarefas', sections: ['tasks-page-section'] },
  '/cron': { key: 'cron', title: 'Crons', sections: ['cron-page-section'] },
  '/calendar': { key: 'calendar', title: 'Calendario', sections: ['calendar-page-section'] },
  '/integrations': { key: 'integrations', title: 'Integrações', sections: ['integrations-page-section'] },
  '/skill': { key: 'skill', title: 'Skill', sections: ['skill-page-section'] },
  '/memory': { key: 'memory', title: 'Memoria', sections: ['memory-page-section'] },
  '/documents': { key: 'documents', title: 'Documentos', sections: ['documents-page-section'] },
  '/database': { key: 'database', title: 'DataBase', sections: ['database-page-section'] },
  '/apis': { key: 'apis', title: 'API\'s', sections: ['apis-page-section'] },
  '/channels': { key: 'channels', title: 'Canais', sections: ['channels-page-section'] },
  '/hooks': { key: 'hooks', title: 'Segurança Hooks', sections: ['hooks-page-section'] },
  '/preferences': { key: 'preferences', title: 'Preferencias', sections: ['preferences-page-section'] },
  '/doctor': { key: 'doctor', title: 'Doctor', sections: ['doctor-page-section'] },
  '/terminal': { key: 'terminal', title: 'Terminal', sections: ['terminal-policy-section'] },
  '/logs': { key: 'logs', title: 'Logs', sections: ['logs-page-section'] },
  '/tailscale': { key: 'tailscale', title: 'Tailscale', sections: ['tailscale-page-section'] },
  '/config': { key: 'config', title: 'Config', sections: ['config-page-section'] },
  '/skills': { key: 'skill', title: 'Skill', sections: ['skill-page-section'] },
  '/files': { key: 'documents', title: 'Documentos', sections: ['documents-page-section'] },
  '/profiles': { key: 'preferences', title: 'Preferencias', sections: ['preferences-page-section'] },
};

const activePage = PAGE_META[window.location.pathname] || PAGE_META['/'];
const DESIGN_ADVISOR_AGENT_ID = 'HCC-design-advisor';
const SHELL_MARKERS = ['topbar-breadcrumb', 'global-search-shortcut', 'page-theme-pill'];
const DASHBOARD_MARKERS = ['dashboard-stat-grid', 'dashboard-live-activity', 'dashboard-top-agents', 'dashboard-cron-overview'];
const ACTIVITY_MARKERS = ['activity-filter-bar', 'activity-summary-grid'];
const OPS_PAGE_MARKERS = ['cron-quick-actions', 'doctor-summary-grid', 'logs-filter-bar', 'logs-detail'];
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
    renderEmpty(root, 'No transcript messages yet');
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card chat-message';
    const role = document.createElement('div');
    role.className = 'chat-role';
    role.textContent = `${item.message_id}. ${item.role || 'unknown'}`;
    const content = document.createElement('div');
    content.className = 'chat-content';
    content.textContent = item.content || '(empty)';
    li.append(role, content);
    li.addEventListener('click', () => setText('chat-inspector', JSON.stringify(item, null, 2)));
    root.appendChild(li);
  }
  setText('chat-inspector', JSON.stringify(items[0], null, 2));
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

async function loadChatTranscript(sessionId) {
  const payload = await fetchJson(`/ops/chat/transcript?session_id=${encodeURIComponent(sessionId)}`);
  setChatSummary(payload.data.session, payload.data.count || 0);
  const items = payload.data.items || [];
  renderChatTranscript(items);
  renderListInto('sessions-related-transcript', items.slice(0, 4), item => card(`${item.message_id}. ${item.role || 'unknown'}`, item.content || '(empty)'), 'No transcript preview yet');
  setText('chat-stream-status', `Transcript loaded for ${sessionId}`);
}

function openChatStream(sessionId) {
  closeChatStream();
  activeChatStream = new EventSource(`/ops/chat/stream?session_id=${encodeURIComponent(sessionId)}`);
  setText('chat-stream-status', 'Streaming live transcript…');
  activeChatStream.addEventListener('chat.session', event => {
    const payload = JSON.parse(event.data);
    setChatSummary(payload, payload.message_count || 0);
  });
  activeChatStream.addEventListener('chat.message', () => loadChatTranscript(sessionId).catch(error => setText('chat-stream-status', error.message)));
  activeChatStream.onerror = () => {
    setText('chat-stream-status', 'Chat stream disconnected.');
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
  setText('gateway-runtime-button', payload.action_label || 'Start Gateway');
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
  setText('activity-window-summary', `Showing ${items.length} of ${maxItems} retained event(s). Window size ${activityPageLimit}.`);
  const summaryRoot = clearRoot('activity-summary-grid');
  if (summaryRoot) {
    [
      ['Visible Events', String(items.length)],
      ['Retained Max', String(maxItems)],
      ['Approvals', String(items.filter(item => (item.kind || '').startsWith('approval')).length)],
      ['Process Events', String(items.filter(item => (item.kind || '').startsWith('process')).length)],
    ].forEach(([label, value]) => {
      const block = document.createElement('div');
      block.className = 'usage-stat-card';
      block.innerHTML = `<div class="usage-stat-label">${label}</div><div class="usage-stat-value">${value}</div>`;
      summaryRoot.appendChild(block);
    });
  }
  renderListInto('activity-page-list', items, item => card(`${item.at || 'n/a'} · ${item.kind}`, `${item.source || 'unknown'}`, [actionButton('Inspect Event', () => setText('activity-drilldown', JSON.stringify(item, null, 2)))]), 'No activity events yet');
  setText('activity-drilldown', items.length ? JSON.stringify(items[0], null, 2) : 'No activity item selected.');
}

async function loadActivityPage() {
  const suffix = activityKindPrefix ? `&kind_prefix=${encodeURIComponent(activityKindPrefix)}` : '';
  const payload = await fetchJson(`/ops/activity?limit=${encodeURIComponent(activityPageLimit)}${suffix}`);
  renderActivityPage(payload.data.items || [], payload.data.retention || {});
}

function renderApprovals(items) {
  const pendingCount = items.filter(item => item.status === 'pending').length;
  setText('approvals-summary', pendingCount ? `${pendingCount} pending item(s)` : 'No pending approvals.');
  renderListInto('approvals-list', items, item => card(`${item.title} · ${item.status}`, `${item.kind} · ${item.source}`, item.status === 'pending' && Array.isArray(item.choices) ? item.choices.map(choice => actionButton(choice, () => handleApprovalDecision(item.id, choice))) : []), 'No approvals yet');
}

function renderDashboardPremium(overview, cronJobs) {
  const agents = overview.agents || [];
  const cronItems = cronJobs.items || [];
  renderListInto('dashboard-top-agents-list', agents.slice(0, 4), item => card(`${item.agent_id} · ${item.status}`, `${item.role || 'worker'} · last seen ${item.last_seen_at || 'n/a'}`), 'No agents yet');
  renderListInto('dashboard-cron-list', cronItems.slice(0, 4), item => card(`${item.name} · ${item.status}`, `${item.schedule || 'manual'} · next ${item.next_run_at || 'n/a'}`), 'No cron jobs yet');
  setText('dashboard-top-agents-summary', agents.length ? `${agents.length} tracked agent(s)` : 'No agents in overview.');
  setText('dashboard-cron-summary', cronItems.length ? `${cronItems.length} scheduled cron job(s)` : 'No cron jobs available.');
}

function renderEvents(items) {
  renderListInto('events-list', items, item => card(`${item.kind}`, `${item.at || 'n/a'} ← ${item.source}`));
  renderLogsPremium(items);
}

function renderAgentsPage(agents, sessions, processes) {
  const selectedAgent = agents[0] || null;
  renderListInto('agents-page-list', agents, agent => {
    const relatedSession = sessions.find(item => item.status === 'active') || sessions[0];
    const runningProcess = processes.find(item => item.status === 'running');
    const controls = [];
    if (relatedSession) {
      controls.push(actionButton('Open Session', async () => {
        activeSessionId = relatedSession.session_id;
        await loadSessionDetail(relatedSession.session_id);
        await loadChatTranscript(relatedSession.session_id);
        openChatStream(relatedSession.session_id);
      }));
    }
    if (runningProcess) {
      controls.push(actionButton('Kill Process', () => handleProcessKill(runningProcess.process_id), 'danger'));
    }
    controls.push(actionButton('Inspect Agent', () => renderAgentDetail(agent, sessions)));
    return card(`${agent.agent_id} · ${agent.status}`, `${agent.role || 'worker'} · last seen ${agent.last_seen_at || 'n/a'}`, controls);
  }, 'No agents yet');
  renderAgentDetail(selectedAgent, sessions);
}

function renderAgentDetail(agent, sessions) {
  if (!agent) {
    setText('agents-page-detail', 'No agent selected.');
    renderListInto('agents-page-sessions', [], () => null, 'No sessions for this agent.');
    const emptyStats = clearRoot('agents-page-stats');
    if (emptyStats) emptyStats.textContent = 'No stats yet';
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
  setText('agents-page-detail', JSON.stringify(agent, null, 2));
  renderListInto('agents-page-sessions', relatedSessions, item => card(`${item.session_id} · ${item.status}`, `${item.platform || item.source || 'unknown'} · ${item.title || 'Untitled'}`, [actionButton('Open Session', async () => {
    activeSessionId = item.session_id;
    await loadSessionDetail(item.session_id);
    await loadChatTranscript(item.session_id);
    openChatStream(item.session_id);
  })]), 'No sessions for this agent.');
}

async function loadSessionDetail(sessionId) {
  const payload = await fetchJson(`/ops/session?session_id=${encodeURIComponent(sessionId)}`);
  setText('session-detail', JSON.stringify(payload.data.session, null, 2));
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
  renderListInto('sessions-list', items, item => card(`${item.session_id} · ${item.status}`, `${item.platform || item.source || 'unknown'} · ${item.title || 'Untitled'}`, [actionButton('Inspect', async () => {
    activeSessionId = item.session_id;
    await loadSessionDetail(item.session_id);
    await loadChatTranscript(item.session_id);
    openChatStream(item.session_id);
  })]));
  renderListInto('sessions-related-transcript', [], () => null, 'Inspect a session to load transcript preview.');
}

function renderProcessesPage(items) {
  renderListInto('processes-page-list', items, item => {
    const controls = [actionButton('Inspect Process', () => setText('processes-page-detail', JSON.stringify(item, null, 2)))];
    if (item.status === 'running') controls.push(actionButton('Kill Process', () => handleProcessControl(item.process_id, 'kill'), 'danger'));
    return card(`${item.process_id} · ${item.status}`, `${item.command || 'no command'} · pid ${item.pid ?? 'n/a'}`, controls);
  }, 'No processes yet');
  setText('processes-page-summary', items.length ? `${items.length} process(es) in registry.` : 'No processes in registry.');
  setText('processes-page-detail', items.length ? JSON.stringify(items[0], null, 2) : 'No process selected.');
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
    actionButton('Inspect History', async () => {
      const payload = await fetchJson(`/ops/cron/history?job_id=${encodeURIComponent(job.job_id)}`);
      renderCronPage(jobs, payload.data.items || []);
      setText('cron-output-inspection', JSON.stringify({ job, history: payload.data.items || [] }, null, 2));
    }),
    actionButton('Run', () => handleCronAction(job.job_id, 'run')),
    actionButton(job.enabled ? 'Pause' : 'Resume', () => handleCronAction(job.job_id, job.enabled ? 'pause' : 'resume')),
  ]), 'No cron jobs yet');
  renderListInto('cron-run-history', historyItems, item => card(`${item.job_id} · ${item.action}`, `${item.recorded_at || 'n/a'} · ${item.status}`), 'No cron history yet');
}

function renderTerminalPolicyPage(policy) {
  renderListInto('terminal-policy-list', [
    ['Mode', policy.mode || 'unknown'],
    ['Interactive Terminal', policy.interactive_terminal_enabled ? 'enabled' : 'disabled'],
    ['Risk Posture', policy.risk_posture || 'unknown'],
    ['Revisit', policy.revisit_in_milestone || 'unspecified'],
  ], ([label, value]) => card(label, value));
  setText('terminal-policy-summary', `${policy.mode || 'unknown'} · ${policy.risk_posture || 'unknown'}`);
  setText('terminal-policy-detail', JSON.stringify(policy, null, 2));
}

function renderMemoryPage(payload) {
  const items = payload.items || [];
  renderListInto('memory-page-list', items, item => card(`${item.scope}`, item.preview || item.text, [actionButton('Inspect', () => setText('memory-page-detail', JSON.stringify(item, null, 2)))]), 'No memory entries yet');
  const counts = payload.counts || {};
  setText('memory-page-summary', `${counts.memory || 0} memory / ${counts.user || 0} user entries`);
  setText('memory-page-detail', items.length ? JSON.stringify(items[0], null, 2) : 'No memory entry selected.');
}

function renderSkillsPage(payload) {
  const items = payload.items || [];
  renderListInto('skills-page-list', items, item => card(item.skill_id, item.preview || item.title, [actionButton('Inspect', () => setText('skills-page-detail', JSON.stringify(item, null, 2)))]), 'No skills yet');
  setText('skills-page-summary', `${payload.count || items.length} skill(s)`);
  setText('skills-page-detail', items.length ? JSON.stringify(items[0], null, 2) : 'No skill selected.');
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
  renderListInto('usage-list', [
    ['Total Tokens', String(totals.total_tokens || 0)],
    ['Actual Cost USD', String(totals.actual_cost_usd || 0)],
    ['Estimated Cost USD', String(totals.estimated_cost_usd || 0)],
    ['Circuit Breaker', breaker.tripped ? `tripped (${(breaker.reasons || []).join(', ')})` : 'healthy'],
    ['Route Count', String(performance.snapshot?.route_count || 0)],
    ['Load Smoke Failures', String(loadSmoke.failures || 0)],
  ], ([label, value]) => card(label, value));
  renderListInto('usage-agent-breakdown', agentBreakdown, item => card(`${item.agent_id} · ${item.session_count} session(s)`, `${item.total_tokens} tokens · $${item.actual_cost_usd || 0}`, [actionButton('Inspect Agent', () => setText('usage-detail', JSON.stringify({ agent: item, top_sessions: topSessions }, null, 2)))]), 'No agent usage yet');
  renderListInto('usage-top-sessions', topSessions, item => card(`${item.session_id} · ${item.title || 'Untitled'}`, `${item.total_tokens || (Number(item.input_tokens || 0) + Number(item.output_tokens || 0) + Number(item.reasoning_tokens || 0))} tokens · $${item.actual_cost_usd || 0}`, [actionButton('Inspect Session', () => setText('usage-detail', JSON.stringify(item, null, 2)))]), 'No sessions yet');
  const statGrid = clearRoot('usage-stat-grid');
  if (statGrid) {
    if (!summaryCards.length) {
      statGrid.textContent = 'No summary cards yet';
    } else {
      summaryCards.forEach(cardItem => {
        const block = document.createElement('div');
        block.className = `usage-stat-card ${(cardItem.tone || 'neutral')}`;
        block.innerHTML = `<div class="usage-stat-label">${cardItem.label}</div><div class="usage-stat-value">${cardItem.value}</div>`;
        statGrid.appendChild(block);
      });
    }
  }
  const perf = document.getElementById('usage-performance-summary');
  if (perf) {
    perf.textContent = `Performance routes ${performance.snapshot?.route_count || 0} · retained window ${performance.budgets?.max_default_list_window || 0} · load smoke failures ${loadSmoke.failures || 0}`;
  }
  setText('usage-summary', `${totals.total_tokens || 0} tokens · $${totals.actual_cost_usd || 0} actual · breaker ${breaker.tripped ? 'tripped' : 'healthy'}`);
  setText('usage-detail', JSON.stringify({ totals, circuit_breaker: breaker, performance, load_smoke: loadSmoke, top_sessions: topSessions }, null, 2));
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
  renderListInto('files-page-list', items, item => card(item.path, item.preview, [actionButton('Inspect', () => setText('files-page-detail', JSON.stringify(item, null, 2)))]), 'No files yet');
  setText('files-page-summary', `${payload.count || items.length} file(s)`);
  setText('files-page-detail', items.length ? JSON.stringify(items[0], null, 2) : 'No file selected.');
}

function renderProfilesPage(payload) {
  const items = payload.items || [];
  renderListInto('profiles-page-list', items, item => card(item.label || item.id, `${item.sensitivity} · reauth ${item.requires_reauth ? 'yes' : 'no'}`, [actionButton('Inspect', () => setText('profiles-page-detail', JSON.stringify(item, null, 2)))]), 'No profiles yet');
  setText('profiles-page-summary', `active ${payload.active_profile_id || 'none'} · ${payload.count || items.length} profile(s)`);
  setText('profiles-page-detail', items.length ? JSON.stringify(items[0], null, 2) : 'No profile selected.');
}

function renderChannelsPage(payload) {
  const items = payload.channels || [];
  renderListInto('channels-page-list', items, item => card(item.label || item.id, `${item.platform || 'unknown'} · ${item.delivery_state || 'unknown'}`, [actionButton('Inspect', () => setText('channels-page-detail', JSON.stringify({ gateway: payload.gateway, channel: item }, null, 2)))]), 'No channels yet');
  setText('channels-page-summary', `${payload.gateway?.status || 'unknown'} gateway · ${payload.count || items.length} channel(s)`);
  setText('channels-page-detail', JSON.stringify(items.length ? { gateway: payload.gateway, channel: items[0] } : payload.gateway || {}, null, 2));
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
  setText('doctor-detail', JSON.stringify({ health: health.data, securityAudit: securityAudit.data, performance: performance.data, loadSmoke: loadSmoke.data }, null, 2));
}

function renderLogsPremium(items) {
  renderListInto('logs-list', items, item => card(item.kind || 'event', `${item.at || 'n/a'} ← ${item.source || 'unknown'}`, [actionButton('Inspect Log', () => setText('logs-detail', JSON.stringify(item, null, 2)))]), 'No logs/events yet');
  setText('logs-detail', items.length ? JSON.stringify(items[0], null, 2) : 'No log selected.');
}

function renderTailscalePage(systemInfo, gatewayPayload) {
  const items = [
    ['Bind', systemInfo.data?.bind || 'unknown'],
    ['Auth', systemInfo.data?.auth_mode || 'unknown'],
    ['Gateway', gatewayPayload.data?.gateway?.status || 'unknown'],
  ];
  renderListInto('tailscale-list', items, ([label, value]) => card(label, value));
  setText('tailscale-detail', JSON.stringify({ system: systemInfo.data, gateway: gatewayPayload.data }, null, 2));
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
    setText('session-detail', 'No session selected.');
    setText('chat-stream-status', 'No session selected.');
    setText('chat-session-summary', 'Select a session to load transcript.');
    renderListInto('chat-transcript', [], () => null, 'No transcript messages yet');
  }
}

window.addEventListener('DOMContentLoaded', () => {
  restoreShellPreferences();
  renderCurrentPage();
  document.getElementById('sidebar-toggle').addEventListener('click', toggleSidebar);
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
  document.getElementById('cron-refresh-button')?.addEventListener('click', () => fetchOverview().catch(error => setText('cron-output-inspection', error.message)));
  document.getElementById('logs-filter-all')?.addEventListener('click', () => {
    renderLogsPremium([]);
    fetchOverview().catch(error => setText('logs-detail', error.message));
  });
  document.getElementById('logs-filter-approval')?.addEventListener('click', () => {
    fetchJson('/ops/activity?limit=20&kind_prefix=approval').then(payload => renderLogsPremium(payload.data.items || [])).catch(error => setText('logs-detail', error.message));
  });
  document.getElementById('logs-filter-process')?.addEventListener('click', () => {
    fetchJson('/ops/activity?limit=20&kind_prefix=process').then(payload => renderLogsPremium(payload.data.items || [])).catch(error => setText('logs-detail', error.message));
  });
  document.getElementById('design-advisor-run')?.addEventListener('click', () => requestDesignAdvisorRecommendation().catch(error => setText('design-advisor-result', error.message)));
  document.getElementById('usage-breaker-form')?.addEventListener('submit', event => {
    event.preventDefault();
    requestUsageCircuitBreakerUpdate().catch(error => setText('usage-detail', error.message));
  });
  document.getElementById('refresh-button').addEventListener('click', () => fetchOverview().catch(error => setText('generated-at', error.message)));
  fetchOverview().catch(error => setText('generated-at', error.message));
  window.addEventListener('beforeunload', closeChatStream);
});
