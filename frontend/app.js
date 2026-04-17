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

async function loadSessionDetail(sessionId) {
  const payload = await fetchJson(`/ops/session?session_id=${encodeURIComponent(sessionId)}`);
  setText('session-detail', JSON.stringify(payload.data.session, null, 2));
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
    li.append(title, meta, actionButton('Inspect', () => loadSessionDetail(item.session_id)));
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

  if ((overview.data.sessions || []).length) {
    await loadSessionDetail(overview.data.sessions[0].session_id);
  } else {
    setText('session-detail', 'No session selected.');
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
});
