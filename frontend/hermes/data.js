/* Hermes Command Center — data layer
   Tries real backend APIs first, falls back to mock data */

const NOW = new Date();
const SAO_PAULO_TIMEZONE = 'America/Sao_Paulo';

function formatSaoPauloTime(date = new Date()) {
  const parts = new Intl.DateTimeFormat('pt-BR', {
    timeZone: SAO_PAULO_TIMEZONE,
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  }).formatToParts(date);
  const lookup = Object.fromEntries(parts.filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
  return `${lookup.hour}:${lookup.minute}:${lookup.second} BRT`;
}

window.HC_TIME = {
  formatSaoPauloTime,
  timeZone: SAO_PAULO_TIMEZONE,
};

const agents = [
  { id: 'hermes-primary', role: 'orchestrator', status: 'active', lastSeen: '2s ago', model: 'claude-opus-4.5', sessions: 3, tokens24h: 142839, cost24h: 2.87, avatar: 'HP' },
  { id: 'scout-salic',    role: 'worker',       status: 'active', lastSeen: '12s ago', model: 'claude-haiku-4.5', sessions: 2, tokens24h: 58210, cost24h: 0.41, avatar: 'SC' },
  { id: 'cron-runner',    role: 'worker',       status: 'idle',   lastSeen: '4m ago', model: 'claude-haiku-4.5', sessions: 0, tokens24h: 11290, cost24h: 0.08, avatar: 'CR' },
  { id: 'indexer-docs',   role: 'worker',       status: 'active', lastSeen: '28s ago', model: 'claude-sonnet-4.5', sessions: 1, tokens24h: 34102, cost24h: 0.62, avatar: 'IX' },
  { id: 'watchdog',       role: 'monitor',      status: 'degraded', lastSeen: '1m ago', model: 'claude-haiku-4.5', sessions: 1, tokens24h: 2408, cost24h: 0.02, avatar: 'WD' },
  { id: 'design-advisor', role: 'advisor',      status: 'idle',   lastSeen: '18m ago', model: 'claude-sonnet-4.5', sessions: 0, tokens24h: 4210, cost24h: 0.11, avatar: 'DA' },
];

const sessions = [
  { id: 'sess_9f21c4',  agent: 'hermes-primary', status: 'active', platform: 'cli', title: 'Refactor salic-monday ingest pipeline', msgs: 42, started: '11:02 BRT', tokens: 18240 },
  { id: 'sess_9f1d87',  agent: 'scout-salic',    status: 'active', platform: 'http', title: 'Scrape deliverable index 2026-Q2', msgs: 18, started: '11:11 BRT', tokens: 6402 },
  { id: 'sess_9f0a12',  agent: 'indexer-docs',   status: 'active', platform: 'cli', title: 'Rebuild embeddings for docs/architecture', msgs: 7, started: '11:20 BRT', tokens: 3821 },
  { id: 'sess_9e9f03',  agent: 'hermes-primary', status: 'paused', platform: 'cli', title: 'Generate release notes for m1', msgs: 24, started: '10:44 BRT', tokens: 9812 },
  { id: 'sess_9e82b1',  agent: 'watchdog',       status: 'active', platform: 'http', title: 'Heartbeat loop · runtime probe', msgs: 124, started: '04:10 BRT', tokens: 2408 },
  { id: 'sess_9e7a12',  agent: 'cron-runner',    status: 'completed', platform: 'cron', title: 'Nightly backup · s3://hermes-state', msgs: 3, started: '23:00 BRT', tokens: 1120 },
];

const transcript = [
  { role: 'user', name: 'operator', time: '11:28:02 BRT', content: 'Rebuild the ingest pipeline so failures in salic-monday don\'t poison the whole run. Keep retries bounded.' },
  { role: 'agent', name: 'hermes-primary', time: '11:28:05 BRT', content: 'Understood. Reading the current pipeline and wrapping each stage in a Result<> to isolate failures.', tool: { name: 'read_file', args: 'backend/ingest/salic.py · 412 lines' } },
  { role: 'agent', name: 'hermes-primary', time: '11:28:14 BRT', content: 'Stage 2 (normalize) and stage 4 (dedup) already share exception handling. I\'ll split them and add a bounded retry (max 3, exp backoff).', tool: { name: 'edit_file', args: '3 stages isolated · 48 lines changed' } },
  { role: 'agent', name: 'hermes-primary', time: '11:28:22 BRT', content: 'Running tests for the new error boundaries.', tool: { name: 'run_tests', args: 'pytest backend/ingest/ -k salic' } },
  { role: 'agent', name: 'hermes-primary', time: '11:28:29 BRT', content: '12 tests passed, 0 failed. Coverage 94%. Ready to commit — requesting approval for the diff.' },
  { role: 'user', name: 'operator', time: '11:29:11 BRT', content: 'Show me the bounded-retry block before approving.' },
];

const processes = [
  { id: 'proc_8aa1', command: 'python -m backend.ingest.salic --full', status: 'running', pid: 48291, cpu: 34, mem: 412, started: '11:02:10 BRT', agent: 'hermes-primary' },
  { id: 'proc_8a99', command: 'node indexer/rebuild.js --docs', status: 'running', pid: 48310, cpu: 18, mem: 280, started: '11:20:44 BRT', agent: 'indexer-docs' },
  { id: 'proc_8a94', command: 'salic-scraper --q 2026-Q2', status: 'running', pid: 48275, cpu: 8,  mem: 104, started: '11:11:05 BRT', agent: 'scout-salic' },
  { id: 'proc_8a88', command: 'hermes watchdog --loop 30s', status: 'running', pid: 47210, cpu: 2,  mem: 28,  started: '07:10:00', agent: 'watchdog' },
  { id: 'proc_8a71', command: 'backup.sh s3://hermes-state', status: 'done',    pid: '—',   cpu: 0,  mem: 0,   started: '23:00:00 BRT', agent: 'cron-runner' },
];

const cron = [
  { id: 'cr_backup',     name: 'Nightly state backup',      schedule: '0 2 * * *',   next: '23:00 BRT', last: 'ok',   enabled: true,  duration: '4m 12s' },
  { id: 'cr_salic',      name: 'SALIC deliverables refresh',schedule: '*/30 * * * *',next: '12:00 BRT', last: 'ok',   enabled: true,  duration: '48s' },
  { id: 'cr_reindex',    name: 'Rebuild docs embeddings',   schedule: '0 4 * * 0',   next: 'Sun 01:00 BRT', last: 'ok',   enabled: true,  duration: '11m 02s' },
  { id: 'cr_healthcheck',name: 'Gateway health probe',      schedule: '*/5 * * * *', next: '11:35 BRT', last: 'warn', enabled: true,  duration: '2s' },
  { id: 'cr_monday',     name: 'Monday sync',               schedule: '0 */2 * * *', next: '13:00 BRT', last: 'err',  enabled: false, duration: '\u2014' },
  { id: 'cr_cleanup',    name: 'Event retention cleanup',   schedule: '0 3 * * *',   next: '00:00 BRT', last: 'ok',   enabled: true,  duration: '18s' },
];

const events = [
  { t: '11:32:18', kind: 'approval.requested', source: 'hermes-primary',  title: 'Approval requested \u00b7 edit backend/ingest/salic.py', tone: 'acc', detail: 'Diff adds bounded retry wrapper.' },
  { t: '11:32:04', kind: 'tool.invoked',       source: 'hermes-primary',  title: 'run_tests \u00b7 pytest backend/ingest/', tone: 'ok', detail: '12 passed, 0 failed' },
  { t: '11:31:47', kind: 'agent.message',      source: 'hermes-primary',  title: 'Assistant replied \u00b7 48 lines of reasoning', tone: '', detail: 'session sess_9f21c4' },
  { t: '11:31:32', kind: 'process.spawn',      source: 'indexer-docs',    title: 'Spawned \u00b7 node indexer/rebuild.js', tone: '', detail: 'pid 48310' },
  { t: '11:31:11', kind: 'cost.threshold',     source: 'cost-controls',   title: 'Daily spend at 41% of budget ($4.11 / $10.00)', tone: 'warn', detail: 'projected burn 7.2h' },
  { t: '11:30:58', kind: 'cron.completed',     source: 'cron-runner',     title: 'cr_salic \u00b7 SALIC deliverables refresh', tone: 'ok', detail: 'exit 0 \u00b7 48s' },
  { t: '11:30:42', kind: 'gateway.heartbeat',  source: 'watchdog',        title: 'Gateway healthy \u00b7 142ms p99', tone: 'ok', detail: 'all probes passing' },
  { t: '11:30:19', kind: 'tool.invoked',       source: 'hermes-primary',  title: 'read_file \u00b7 backend/ingest/salic.py', tone: '', detail: '412 lines' },
  { t: '11:30:02', kind: 'session.started',    source: 'indexer-docs',    title: 'New session \u00b7 sess_9f0a12', tone: 'acc', detail: 'Rebuild docs embeddings' },
  { t: '11:29:48', kind: 'approval.resolved',  source: 'operator',        title: 'Approved \u00b7 edit backend/chat_protocol.py', tone: 'ok', detail: 'by operator' },
  { t: '11:29:22', kind: 'memory.write',       source: 'hermes-primary',  title: 'Memory scope "project.salic" updated', tone: '', detail: '2 facts added' },
  { t: '11:29:01', kind: 'cron.missed',        source: 'cr_monday',       title: 'Cron missed \u00b7 Monday sync disabled', tone: 'err', detail: 'last run err \u00b7 11:27 BRT' },
];

const approvals = [
  { id: 'ap_991', title: 'Edit backend/ingest/salic.py', kind: 'file.edit', source: 'hermes-primary', at: '11:32:18 BRT', risk: 'medium', preview: '+ 48 lines \u00b7 bounded retry wrapper', choices: ['approve', 'deny', 'inspect'] },
  { id: 'ap_988', title: 'Run migration 20260417_add_retention_index', kind: 'db.migrate', source: 'hermes-primary', at: '11:24:02 BRT', risk: 'high',   preview: 'CREATE INDEX ON events(recorded_at)', choices: ['approve', 'deny'] },
  { id: 'ap_987', title: 'Exec shell \u00b7 rg "salic_id" -g "*.py"', kind: 'shell.run', source: 'scout-salic', at: '11:22:11 BRT', risk: 'low',    preview: 'ripgrep for salic_id references', choices: ['approve', 'deny'] },
];

const usage = {
  today: { tokens: 482910, cost: 4.11, budget: 10.00, sessions: 14, requests: 318 },
  breaker: { tripped: false, maxCost: 10.00, maxTokens: 1500000 },
  agents: [
    { id: 'hermes-primary', tokens: 302145, cost: 2.87, sessions: 8 },
    { id: 'indexer-docs', tokens: 78102, cost: 0.62, sessions: 2 },
    { id: 'scout-salic', tokens: 58210, cost: 0.41, sessions: 3 },
    { id: 'design-advisor', tokens: 22140, cost: 0.11, sessions: 1 },
    { id: 'cron-runner', tokens: 18913, cost: 0.08, sessions: 0 },
    { id: 'watchdog', tokens: 3400, cost: 0.02, sessions: 1 },
  ],
  hourly: [12, 18, 22, 28, 19, 24, 31, 42, 38, 44, 52, 48, 61, 58, 72, 64, 78, 82, 71, 68, 84, 92, 78, 88],
};

const memory = [
  { scope: 'project.salic',     preview: 'API key rotation due 2026-05-01. Use staging creds until signed off.', updated: '11:29:22 BRT' },
  { scope: 'operator.prefs',    preview: 'Prefer concise commits, conventional-commits format, no co-author lines.', updated: '2d ago' },
  { scope: 'system.invariants', preview: 'Never push to main without green CI. Always run migrations in a transaction.', updated: '4d ago' },
  { scope: 'project.hermes',    preview: 'm1 ships when auth-posture exception is closed + passkey flow lands.', updated: '6h ago' },
  { scope: 'project.rouanet',   preview: 'Deadline submission window closes 2026-06-30 for Lei Rouanet proposals.', updated: '1d ago' },
];

const files = [
  { path: 'backend/ingest/salic.py',     size: '14.2 KB', updated: '11:31 BRT', preview: 'Bounded-retry wrapper under review.' },
  { path: 'backend/chat_protocol.py',    size: '3.4 KB',  updated: '11:29 BRT', preview: 'Streaming protocol \u00b7 edit approved.' },
  { path: 'docs/product-vision.md',      size: '1.6 KB',  updated: '2d ago', preview: 'Single-user operator command center.' },
  { path: 'docs/release/release-readiness.md', size: '0.7 KB', updated: '4h ago', preview: 'm1 gating checklist.' },
  { path: 'scripts/verify_phase0_foundation.py', size: '2.6 KB', updated: '6d ago', preview: 'Phase 0 smoke test runner.' },
  { path: 'frontend/styles.css',         size: '4.3 KB',  updated: '3h ago', preview: 'Dark ops palette.' },
];

const logs = [
  { level: 'info',  t: '11:32:18', source: 'http',    msg: 'POST /ops/approvals/resolve 200 \u00b7 14ms' },
  { level: 'info',  t: '11:32:17', source: 'event',   msg: 'emit approval.requested \u00b7 ap_991' },
  { level: 'info',  t: '11:32:04', source: 'runner',  msg: 'pytest backend/ingest/ -k salic \u00b7 ok \u00b7 12/12' },
  { level: 'warn',  t: '11:31:11', source: 'cost',    msg: 'daily spend 41% \u00b7 projection 7.2h to budget' },
  { level: 'info',  t: '11:30:58', source: 'cron',    msg: 'cr_salic completed exit=0 duration=48s' },
  { level: 'err',   t: '11:29:01', source: 'cron',    msg: 'cr_monday failed: 503 upstream \u00b7 disabled after 3 consecutive' },
  { level: 'info',  t: '11:28:41', source: 'http',    msg: 'GET /ops/overview 200 \u00b7 6ms' },
  { level: 'info',  t: '11:28:14', source: 'agent',   msg: 'hermes-primary edit_file \u00b7 3 stages isolated' },
  { level: 'dim',   t: '11:28:02', source: 'chat',    msg: 'operator message received \u00b7 sess_9f21c4' },
  { level: 'info',  t: '11:27:50', source: 'runtime', msg: 'heartbeat ok \u00b7 runtime=online \u00b7 event_bus=online' },
  { level: 'warn',  t: '11:27:11', source: 'http',    msg: 'GET /ops/files 200 \u00b7 412ms (slow)' },
];

const doctor = [
  { name: 'Runtime',       status: 'ok',   detail: 'gateway online \u00b7 142ms p99' },
  { name: 'Event bus',     status: 'ok',   detail: 'sse \u00b7 3 listeners \u00b7 0 dropped' },
  { name: 'Database',      status: 'ok',   detail: 'sqlite \u00b7 48 MB \u00b7 migrations up to date' },
  { name: 'Secrets store', status: 'ok',   detail: 'keychain \u00b7 unlocked' },
  { name: 'Passkeys',      status: 'warn', detail: 'auth posture exception open until m1' },
  { name: 'Tailscale',     status: 'warn', detail: 'non-default bind \u00b7 m0-05 exception' },
  { name: 'Cost controls', status: 'ok',   detail: 'breaker healthy \u00b7 41% of budget' },
  { name: 'Cron registry', status: 'err',  detail: 'cr_monday disabled after 3 failures' },
];

const systemHealth = {
  env: 'production',
  bind: '127.0.0.1:8787',
  auth: 'passkey + loopback',
  uptime: '3d 14h 22m',
  version: 'hermes/0.9.4-rc3',
};

window.HC_DATA = {
  agents, sessions, transcript, processes, cron, events, approvals,
  usage, memory, files, logs, doctor, systemHealth,
};

async function fetchJson(path) {
  try {
    const r = await fetch(path, { credentials: 'same-origin', headers: { 'Content-Type': 'application/json' } });
    if (!r.ok) return null;
    return await r.json();
  } catch { return null; }
}

function unwrapData(payload) {
  return payload && typeof payload === 'object' && payload.data ? payload.data : payload;
}

function safeNumber(value, fallback = 0) {
  return Number.isFinite(value) ? value : fallback;
}

function formatRelativeOrBrt(isoValue, fallback = '—') {
  if (!isoValue) return fallback;
  try {
    const date = new Date(isoValue);
    if (Number.isNaN(date.getTime())) return fallback;
    const ageMs = Date.now() - date.getTime();
    const ageSec = Math.round(ageMs / 1000);
    if (ageSec >= 0 && ageSec < 60) return `${ageSec}s ago`;
    const ageMin = Math.round(ageSec / 60);
    if (ageMin > 0 && ageMin < 60) return `${ageMin}m ago`;
    return formatSaoPauloTime(date).replace(':00 BRT', ' BRT');
  } catch {
    return fallback;
  }
}

function mapLiveOverview(overview) {
  if (!overview) return null;

  return {
    agents: Array.isArray(overview.agents)
      ? overview.agents.map((agent, index) => ({
          id: agent.agent_id || `agent-${index + 1}`,
          role: agent.role || 'worker',
          status: agent.status === 'running' ? 'active' : (agent.status || 'idle'),
          lastSeen: formatRelativeOrBrt(agent.last_seen_at, '—'),
          model: agent.model || 'runtime',
          sessions: safeNumber(agent.session_count, 0),
          tokens24h: safeNumber(agent.total_tokens, 0),
          cost24h: safeNumber(agent.actual_cost_usd ?? agent.estimated_cost_usd, 0),
          avatar: (agent.agent_id || `A${index + 1}`).slice(0, 2).toUpperCase(),
        }))
      : null,
    sessions: Array.isArray(overview.sessions)
      ? overview.sessions.map((session, index) => ({
          id: session.session_id || `session-${index + 1}`,
          agent: session.agent_id || 'agent-main',
          status: session.status === 'running' ? 'active' : (session.status || 'active'),
          platform: session.platform || session.source || 'runtime',
          title: session.display_name || session.title || session.session_id || `session-${index + 1}`,
          msgs: safeNumber(session.message_count, 0),
          started: formatRelativeOrBrt(session.started_at || session.updated_at, '—'),
          tokens: safeNumber((session.input_tokens || 0) + (session.output_tokens || 0) + (session.reasoning_tokens || 0), 0),
        }))
      : null,
    events: Array.isArray(overview.events)
      ? overview.events.map((event, index) => ({
          t: formatSaoPauloTime(new Date(event.at || Date.now())).replace(' BRT', ''),
          kind: event.kind || 'event',
          source: event.source || 'runtime',
          title: event.kind || `event-${index + 1}`,
          tone: (event.kind || '').includes('error') ? 'err' : ((event.kind || '').includes('approval') ? 'acc' : ''),
          detail: JSON.stringify(event.data || {}),
        }))
      : null,
    approvals: Array.isArray(overview.approvals)
      ? overview.approvals.map((approval, index) => ({
          id: approval.id || `approval-${index + 1}`,
          title: approval.title || approval.kind || `Approval ${index + 1}`,
          kind: approval.kind || 'approval.requested',
          source: approval.source || 'runtime',
          at: formatRelativeOrBrt(approval.at, '—'),
          risk: approval.risk || 'medium',
          preview: approval.preview || '',
          choices: approval.choices || ['approve', 'deny'],
        }))
      : null,
    systemHealth: overview.system_health
      ? {
          env: overview.service || 'production',
          bind: overview.system_health.bind || '100.65.45.58:8788',
          auth: overview.system_health.auth || 'trusted-local',
          uptime: overview.system_health.uptime || 'runtime',
          version: overview.system_health.version || overview.service || 'hermes-command-center',
        }
      : null,
  };
}

function mapLiveUsage(usageData) {
  if (!usageData || !usageData.totals) return null;
  const totals = usageData.totals;
  const breaker = usageData.circuit_breaker || {};
  const config = breaker.config || {};
  const agents = Array.isArray(usageData.agent_breakdown) ? usageData.agent_breakdown : [];

  return {
    today: {
      tokens: safeNumber(totals.total_tokens, 0),
      cost: safeNumber(totals.actual_cost_usd ?? totals.estimated_cost_usd, 0),
      budget: safeNumber(config.max_actual_cost_usd, 10),
      sessions: safeNumber(totals.session_count, 0),
      requests: safeNumber(usageData.load_smoke?.requests_executed, 0),
    },
    breaker: {
      tripped: !!breaker.tripped,
      maxCost: safeNumber(config.max_actual_cost_usd, 10),
      maxTokens: safeNumber(config.max_total_tokens, Math.max(safeNumber(totals.total_tokens, 0), 1)),
    },
    agents: agents.map((agent, index) => ({
      id: agent.agent_id || `agent-${index + 1}`,
      tokens: safeNumber(agent.total_tokens, 0),
      cost: safeNumber(agent.actual_cost_usd ?? agent.estimated_cost_usd, 0),
      sessions: safeNumber(agent.session_count, 0),
    })),
    hourly: Array.isArray(usageData.hourly)
      ? usageData.hourly
      : [
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.03)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.04)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.05)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.06)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.08)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.1)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.12)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.14)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.12)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.1)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.09)),
          Math.max(1, Math.round(safeNumber(totals.total_tokens, 0) * 0.07)),
        ],
  };
}

function mapLiveCron(cronData) {
  const items = Array.isArray(cronData?.items) ? cronData.items : Array.isArray(cronData?.jobs) ? cronData.jobs : null;
  if (!items) return null;
  return items.map((job, index) => ({
    id: job.job_id || `cron-${index + 1}`,
    name: job.name || `Job ${index + 1}`,
    schedule: job.schedule || '—',
    next: formatRelativeOrBrt(job.next_run_at, '—'),
    last: job.last_status || job.status || 'ok',
    enabled: job.enabled !== false,
    duration: job.duration || '—',
  }));
}

function mapLiveDoctor(doctorData) {
  return Array.isArray(doctorData?.checks) ? doctorData.checks : null;
}

async function tryLoadLiveData() {
  const overviewPayload = await fetchJson('/ops/overview');
  const overview = unwrapData(overviewPayload);
  if (!overview) return;

  const mappedOverview = mapLiveOverview(overview);
  if (mappedOverview?.agents) window.HC_DATA.agents = mappedOverview.agents;
  if (mappedOverview?.sessions) window.HC_DATA.sessions = mappedOverview.sessions;
  if (mappedOverview?.events) window.HC_DATA.events = mappedOverview.events;
  if (mappedOverview?.approvals) window.HC_DATA.approvals = mappedOverview.approvals;
  if (mappedOverview?.systemHealth) window.HC_DATA.systemHealth = mappedOverview.systemHealth;

  const usagePayload = await fetchJson('/ops/usage');
  const usageData = unwrapData(usagePayload);
  const mappedUsage = mapLiveUsage(usageData);
  if (mappedUsage) window.HC_DATA.usage = mappedUsage;

  const cronPayload = await fetchJson('/runtime/cron/jobs');
  const cronData = unwrapData(cronPayload);
  const mappedCron = mapLiveCron(cronData);
  if (mappedCron) window.HC_DATA.cron = mappedCron;

  const doctorPayload = await fetchJson('/health/doctor');
  const doctorData = unwrapData(doctorPayload);
  const mappedDoctor = mapLiveDoctor(doctorData);
  if (mappedDoctor) window.HC_DATA.doctor = mappedDoctor;
}

tryLoadLiveData();
