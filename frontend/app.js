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
  document.getElementById(id).textContent = text;
}

function clearRoot(elementId) {
  const root = document.getElementById(elementId);
  root.innerHTML = '';
  return root;
}

function renderEmpty(root, label = 'No items yet') {
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

let activeChatStream = null;
let activeSessionId = null;

async function loadSessionDetail(sessionId) {
  const payload = await fetchJson(`/ops/session?session_id=${encodeURIComponent(sessionId)}`);
  setText('session-detail', JSON.stringify(payload.data.session, null, 2));
}

function renderSystemHealth(systemInfo, health) {
  const root = clearRoot('system-health');
  const items = [
    { label: 'Service', value: systemInfo.service || 'unknown' },
    { label: 'Bind', value: systemInfo.bind || 'unknown' },
    { label: 'Auth', value: systemInfo.auth_mode || 'unknown' },
    { label: 'Overall', value: health.overall_status || 'unknown' },
    { label: 'Runtime', value: health.runtime?.status || 'unknown' },
    { label: 'Event Bus', value: health.event_bus?.status || 'unknown' },
  ];
  setText('system-summary', `${systemInfo.environment || 'unknown'} · ${health.overall_status || 'unknown'}`);
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card';
    const title = document.createElement('div');
    title.className = 'item-title';
    title.textContent = item.label;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = item.value;
    li.append(title, meta);
    root.appendChild(li);
  }
}

function renderChatTranscript(items) {
  const root = clearRoot('chat-transcript');
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
    if (Array.isArray(item.tool_calls) && item.tool_calls.length) {
      const tools = document.createElement('div');
      tools.className = 'chat-tools';
      tools.textContent = `Tool calls: ${item.tool_calls.map(call => call.name || call.id || 'tool').join(', ')}`;
      li.append(tools);
    }
    if (item.tool_call_id) {
      const toolResult = document.createElement('div');
      toolResult.className = 'chat-tools';
      toolResult.textContent = `Tool result for: ${item.tool_call_id}`;
      li.append(toolResult);
    }
    root.appendChild(li);
  }
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

function openChatStream(sessionId) {
  closeChatStream();
  activeChatStream = new EventSource(`/ops/chat/stream?session_id=${encodeURIComponent(sessionId)}`);
  setText('chat-stream-status', 'Streaming live transcript…');

  activeChatStream.addEventListener('chat.session', event => {
    const payload = JSON.parse(event.data);
    setChatSummary(payload, payload.message_count || 0);
  });

  activeChatStream.addEventListener('chat.message', () => {
    loadChatTranscript(sessionId).catch(error => {
      setText('chat-stream-status', error.message);
    });
  });

  activeChatStream.onerror = () => {
    setText('chat-stream-status', 'Chat stream disconnected.');
    closeChatStream();
  };
}

async function loadChatTranscript(sessionId) {
  const payload = await fetchJson(`/ops/chat/transcript?session_id=${encodeURIComponent(sessionId)}`);
  setChatSummary(payload.data.session, payload.data.count || 0);
  renderChatTranscript(payload.data.items || []);
  setText('chat-stream-status', `Transcript loaded for ${sessionId}`);
}

async function handleProcessKill(processId) {
  await fetchJson('/ops/processes/kill', {
    method: 'POST',
    body: JSON.stringify({ process_id: processId }),
  });
  await fetchOverview();
}

async function handleCronAction(jobId, action) {
  await fetchJson('/ops/cron/control', {
    method: 'POST',
    body: JSON.stringify({ job_id: jobId, action }),
  });
  await fetchOverview();
}

async function handleApprovalDecision(itemId, decision) {
  await fetchJson('/ops/approvals/resolve', {
    method: 'POST',
    body: JSON.stringify({ item_id: itemId, decision }),
  });
  await fetchOverview();
}

function renderSessions(items) {
  const root = clearRoot('sessions-list');
  if (!items.length) {
    renderEmpty(root);
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card';
    const title = document.createElement('div');
    title.className = 'item-title';
    title.textContent = `${item.session_id} · ${item.status}`;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = `${item.platform || item.source || 'unknown'} · ${item.title || 'Untitled'}`;
    li.append(title, meta, actionButton('Inspect', async () => {
      activeSessionId = item.session_id;
      await loadSessionDetail(item.session_id);
      await loadChatTranscript(item.session_id);
      openChatStream(item.session_id);
    }));
    root.appendChild(li);
  }
}

function renderProcesses(items) {
  const root = clearRoot('processes-list');
  if (!items.length) {
    renderEmpty(root);
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card';
    const title = document.createElement('div');
    title.className = 'item-title';
    title.textContent = `${item.process_id} · ${item.status}`;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = `${item.command || 'no command'} · pid ${item.pid ?? 'n/a'}`;
    li.append(title, meta);
    if (item.status === 'running') {
      li.append(actionButton('Kill', () => handleProcessKill(item.process_id), 'danger'));
    }
    root.appendChild(li);
  }
}

function renderCron(items) {
  const root = clearRoot('cron-list');
  if (!items.length) {
    renderEmpty(root);
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card';
    const title = document.createElement('div');
    title.className = 'item-title';
    title.textContent = `${item.name} · ${item.status}`;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = `${item.schedule || 'manual'} · next ${item.next_run_at || 'n/a'}`;
    const controls = document.createElement('div');
    controls.className = 'actions-row';
    controls.append(
      actionButton('Run', () => handleCronAction(item.job_id, 'run')),
      actionButton(item.enabled ? 'Pause' : 'Resume', () => handleCronAction(item.job_id, item.enabled ? 'pause' : 'resume')),
    );
    li.append(title, meta, controls);
    root.appendChild(li);
  }
}

function renderEvents(items) {
  const root = clearRoot('events-list');
  if (!items.length) {
    renderEmpty(root);
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card';
    li.textContent = `${item.at || 'n/a'} · ${item.kind} ← ${item.source}`;
    root.appendChild(li);
  }
}

function renderApprovals(items) {
  const root = clearRoot('approvals-list');
  const pendingCount = items.filter(item => item.status === 'pending').length;
  setText('approvals-summary', pendingCount ? `${pendingCount} pending item(s)` : 'No pending approvals.');
  if (!items.length) {
    renderEmpty(root, 'No approvals yet');
    return;
  }
  for (const item of items) {
    const li = document.createElement('li');
    li.className = 'item-card';
    const title = document.createElement('div');
    title.className = 'item-title';
    title.textContent = `${item.title} · ${item.status}`;
    const meta = document.createElement('div');
    meta.className = 'item-meta';
    meta.textContent = `${item.kind} · ${item.source}`;
    const summary = document.createElement('div');
    summary.className = 'item-meta';
    summary.textContent = item.summary;
    li.append(title, meta, summary);
    if (item.status === 'pending' && Array.isArray(item.choices) && item.choices.length) {
      const controls = document.createElement('div');
      controls.className = 'actions-row';
      for (const choice of item.choices) {
        controls.append(actionButton(choice, () => handleApprovalDecision(item.id, choice)));
      }
      li.append(controls);
    } else if (item.decision) {
      const resolved = document.createElement('div');
      resolved.className = 'item-meta';
      resolved.textContent = `Decision: ${item.decision}`;
      li.append(resolved);
    }
    root.appendChild(li);
  }
}

async function fetchOverview() {
  const session = await fetchJson('/auth/session');
  setText('auth-status', session.data.authenticated
    ? `Operator: ${session.data.user} (${session.data.auth_mode})`
    : 'Not authenticated');

  const overview = await fetchJson('/ops/overview');
  const approvals = await fetchJson('/ops/approvals');
  const systemInfo = await fetchJson('/system/info');
  const health = await fetchJson('/health');
  setText('generated-at', `Snapshot: ${overview.data.generated_at}`);
  setText('count-agents', String(overview.data.counts.agents));
  setText('count-sessions', String(overview.data.counts.sessions));
  setText('count-processes', String(overview.data.counts.processes));
  setText('count-cron', String(overview.data.counts.cron_jobs));

  renderSessions(overview.data.sessions || []);
  renderProcesses(overview.data.processes || []);
  renderCron(overview.data.cron_jobs || []);
  renderEvents(overview.data.events || []);
  renderApprovals(approvals.data.items || []);
  renderSystemHealth(systemInfo.data, health.data);

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
    renderChatTranscript([]);
  }
}

window.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refresh-button').addEventListener('click', () => {
    fetchOverview().catch(error => {
      setText('auth-status', error.message);
    });
  });

  fetchOverview().catch(error => {
    setText('auth-status', error.message);
  });

  window.addEventListener('beforeunload', () => {
    closeChatStream();
  });
});
