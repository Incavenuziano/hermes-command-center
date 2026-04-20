/* Hermes Command Center — data layer
   Tries real backend APIs first, falls back to mock data */

const NOW = new Date();

const agents = [
  { id: 'hermes-primary', role: 'orchestrator', status: 'active', lastSeen: '2s ago', model: 'claude-opus-4.5', sessions: 3, tokens24h: 142839, cost24h: 2.87, avatar: 'HP' },
  { id: 'scout-salic',    role: 'worker',       status: 'active', lastSeen: '12s ago', model: 'claude-haiku-4.5', sessions: 2, tokens24h: 58210, cost24h: 0.41, avatar: 'SC' },
  { id: 'cron-runner',    role: 'worker',       status: 'idle',   lastSeen: '4m ago', model: 'claude-haiku-4.5', sessions: 0, tokens24h: 11290, cost24h: 0.08, avatar: 'CR' },
  { id: 'indexer-docs',   role: 'worker',       status: 'active', lastSeen: '28s ago', model: 'claude-sonnet-4.5', sessions: 1, tokens24h: 34102, cost24h: 0.62, avatar: 'IX' },
  { id: 'watchdog',       role: 'monitor',      status: 'degraded', lastSeen: '1m ago', model: 'claude-haiku-4.5', sessions: 1, tokens24h: 2408, cost24h: 0.02, avatar: 'WD' },
  { id: 'design-advisor', role: 'advisor',      status: 'idle',   lastSeen: '18m ago', model: 'claude-sonnet-4.5', sessions: 0, tokens24h: 4210, cost24h: 0.11, avatar: 'DA' },
];

const sessions = [
  { id: 'sess_9f21c4',  agent: 'hermes-primary', status: 'active', platform: 'cli', title: 'Refactor salic-monday ingest pipeline', msgs: 42, started: '14:02', tokens: 18240 },
  { id: 'sess_9f1d87',  agent: 'scout-salic',    status: 'active', platform: 'http', title: 'Scrape deliverable index 2026-Q2', msgs: 18, started: '14:11', tokens: 6402 },
  { id: 'sess_9f0a12',  agent: 'indexer-docs',   status: 'active', platform: 'cli', title: 'Rebuild embeddings for docs/architecture', msgs: 7, started: '14:20', tokens: 3821 },
  { id: 'sess_9e9f03',  agent: 'hermes-primary', status: 'paused', platform: 'cli', title: 'Generate release notes for m1', msgs: 24, started: '13:44', tokens: 9812 },
  { id: 'sess_9e82b1',  agent: 'watchdog',       status: 'active', platform: 'http', title: 'Heartbeat loop · runtime probe', msgs: 124, started: '07:10', tokens: 2408 },
  { id: 'sess_9e7a12',  agent: 'cron-runner',    status: 'completed', platform: 'cron', title: 'Nightly backup · s3://hermes-state', msgs: 3, started: '02:00', tokens: 1120 },
];

const transcript = [
  { role: 'user', name: 'operator', time: '14:28:02', content: 'Rebuild the ingest pipeline so failures in salic-monday don\'t poison the whole run. Keep retries bounded.' },
  { role: 'agent', name: 'hermes-primary', time: '14:28:05', content: 'Understood. Reading the current pipeline and wrapping each stage in a Result<> to isolate failures.', tool: { name: 'read_file', args: 'backend/ingest/salic.py · 412 lines' } },
  { role: 'agent', name: 'hermes-primary', time: '14:28:14', content: 'Stage 2 (normalize) and stage 4 (dedup) already share exception handling. I\'ll split them and add a bounded retry (max 3, exp backoff).', tool: { name: 'edit_file', args: '3 stages isolated · 48 lines changed' } },
  { role: 'agent', name: 'hermes-primary', time: '14:28:22', content: 'Running tests for the new error boundaries.', tool: { name: 'run_tests', args: 'pytest backend/ingest/ -k salic' } },
  { role: 'agent', name: 'hermes-primary', time: '14:28:29', content: '12 tests passed, 0 failed. Coverage 94%. Ready to commit — requesting approval for the diff.' },
  { role: 'user', name: 'operator', time: '14:29:11', content: 'Show me the bounded-retry block before approving.' },
];

const processes = [
  { id: 'proc_8aa1', command: 'python -m backend.ingest.salic --full', status: 'running', pid: 48291, cpu: 34, mem: 412, started: '14:02:10', agent: 'hermes-primary' },
  { id: 'proc_8a99', command: 'node indexer/rebuild.js --docs', status: 'running', pid: 48310, cpu: 18, mem: 280, started: '14:20:44', agent: 'indexer-docs' },
  { id: 'proc_8a94', command: 'salic-scraper --q 2026-Q2', status: 'running', pid: 48275, cpu: 8,  mem: 104, started: '14:11:05', agent: 'scout-salic' },
  { id: 'proc_8a88', command: 'hermes watchdog --loop 30s', status: 'running', pid: 47210, cpu: 2,  mem: 28,  started: '07:10:00', agent: 'watchdog' },
  { id: 'proc_8a71', command: 'backup.sh s3://hermes-state', status: 'done',    pid: '—',   cpu: 0,  mem: 0,   started: '02:00:00', agent: 'cron-runner' },
];

const cron = [
  { id: 'cr_backup',     name: 'Nightly state backup',      schedule: '0 2 * * *',   next: '02:00 UTC', last: 'ok',   enabled: true,  duration: '4m 12s' },
  { id: 'cr_salic',      name: 'SALIC deliverables refresh',schedule: '*/30 * * * *',next: '15:00 UTC', last: 'ok',   enabled: true,  duration: '48s' },
  { id: 'cr_reindex',    name: 'Rebuild docs embeddings',   schedule: '0 4 * * 0',   next: 'Sun 04:00', last: 'ok',   enabled: true,  duration: '11m 02s' },
  { id: 'cr_healthcheck',name: 'Gateway health probe',      schedule: '*/5 * * * *', next: '14:35 UTC', last: 'warn', enabled: true,  duration: '2s' },
  { id: 'cr_monday',     name: 'Monday sync',               schedule: '0 */2 * * *', next: '16:00 UTC', last: 'err',  enabled: false, duration: '\u2014' },
  { id: 'cr_cleanup',    name: 'Event retention cleanup',   schedule: '0 3 * * *',   next: '03:00 UTC', last: 'ok',   enabled: true,  duration: '18s' },
];

const events = [
  { t: '14:32:18', kind: 'approval.requested', source: 'hermes-primary',  title: 'Approval requested \u00b7 edit backend/ingest/salic.py', tone: 'acc', detail: 'Diff adds bounded retry wrapper.' },
  { t: '14:32:04', kind: 'tool.invoked',       source: 'hermes-primary',  title: 'run_tests \u00b7 pytest backend/ingest/', tone: 'ok', detail: '12 passed, 0 failed' },
  { t: '14:31:47', kind: 'agent.message',      source: 'hermes-primary',  title: 'Assistant replied \u00b7 48 lines of reasoning', tone: '', detail: 'session sess_9f21c4' },
  { t: '14:31:32', kind: 'process.spawn',      source: 'indexer-docs',    title: 'Spawned \u00b7 node indexer/rebuild.js', tone: '', detail: 'pid 48310' },
  { t: '14:31:11', kind: 'cost.threshold',     source: 'cost-controls',   title: 'Daily spend at 41% of budget ($4.11 / $10.00)', tone: 'warn', detail: 'projected burn 7.2h' },
  { t: '14:30:58', kind: 'cron.completed',     source: 'cron-runner',     title: 'cr_salic \u00b7 SALIC deliverables refresh', tone: 'ok', detail: 'exit 0 \u00b7 48s' },
  { t: '14:30:42', kind: 'gateway.heartbeat',  source: 'watchdog',        title: 'Gateway healthy \u00b7 142ms p99', tone: 'ok', detail: 'all probes passing' },
  { t: '14:30:19', kind: 'tool.invoked',       source: 'hermes-primary',  title: 'read_file \u00b7 backend/ingest/salic.py', tone: '', detail: '412 lines' },
  { t: '14:30:02', kind: 'session.started',    source: 'indexer-docs',    title: 'New session \u00b7 sess_9f0a12', tone: 'acc', detail: 'Rebuild docs embeddings' },
  { t: '14:29:48', kind: 'approval.resolved',  source: 'operator',        title: 'Approved \u00b7 edit backend/chat_protocol.py', tone: 'ok', detail: 'by operator' },
  { t: '14:29:22', kind: 'memory.write',       source: 'hermes-primary',  title: 'Memory scope "project.salic" updated', tone: '', detail: '2 facts added' },
  { t: '14:29:01', kind: 'cron.missed',        source: 'cr_monday',       title: 'Cron missed \u00b7 Monday sync disabled', tone: 'err', detail: 'last run err \u00b7 14:27 UTC' },
];

const approvals = [
  { id: 'ap_991', title: 'Edit backend/ingest/salic.py', kind: 'file.edit', source: 'hermes-primary', at: '14:32:18', risk: 'medium', preview: '+ 48 lines \u00b7 bounded retry wrapper', choices: ['approve', 'deny', 'inspect'] },
  { id: 'ap_988', title: 'Run migration 20260417_add_retention_index', kind: 'db.migrate', source: 'hermes-primary', at: '14:24:02', risk: 'high',   preview: 'CREATE INDEX ON events(recorded_at)', choices: ['approve', 'deny'] },
  { id: 'ap_987', title: 'Exec shell \u00b7 rg "salic_id" -g "*.py"', kind: 'shell.run', source: 'scout-salic', at: '14:22:11', risk: 'low',    preview: 'ripgrep for salic_id references', choices: ['approve', 'deny'] },
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
  { scope: 'project.salic',     preview: 'API key rotation due 2026-05-01. Use staging creds until signed off.', updated: '14:29:22' },
  { scope: 'operator.prefs',    preview: 'Prefer concise commits, conventional-commits format, no co-author lines.', updated: '2d ago' },
  { scope: 'system.invariants', preview: 'Never push to main without green CI. Always run migrations in a transaction.', updated: '4d ago' },
  { scope: 'project.hermes',    preview: 'm1 ships when auth-posture exception is closed + passkey flow lands.', updated: '6h ago' },
  { scope: 'project.rouanet',   preview: 'Deadline submission window closes 2026-06-30 for Lei Rouanet proposals.', updated: '1d ago' },
];

const files = [
  { path: 'backend/ingest/salic.py',     size: '14.2 KB', updated: '14:31', preview: 'Bounded-retry wrapper under review.' },
  { path: 'backend/chat_protocol.py',    size: '3.4 KB',  updated: '14:29', preview: 'Streaming protocol \u00b7 edit approved.' },
  { path: 'docs/product-vision.md',      size: '1.6 KB',  updated: '2d ago', preview: 'Single-user operator command center.' },
  { path: 'docs/release/release-readiness.md', size: '0.7 KB', updated: '4h ago', preview: 'm1 gating checklist.' },
  { path: 'scripts/verify_phase0_foundation.py', size: '2.6 KB', updated: '6d ago', preview: 'Phase 0 smoke test runner.' },
  { path: 'frontend/styles.css',         size: '4.3 KB',  updated: '3h ago', preview: 'Dark ops palette.' },
];

const logs = [
  { level: 'info',  t: '14:32:18', source: 'http',    msg: 'POST /ops/approvals/resolve 200 \u00b7 14ms' },
  { level: 'info',  t: '14:32:17', source: 'event',   msg: 'emit approval.requested \u00b7 ap_991' },
  { level: 'info',  t: '14:32:04', source: 'runner',  msg: 'pytest backend/ingest/ -k salic \u00b7 ok \u00b7 12/12' },
  { level: 'warn',  t: '14:31:11', source: 'cost',    msg: 'daily spend 41% \u00b7 projection 7.2h to budget' },
  { level: 'info',  t: '14:30:58', source: 'cron',    msg: 'cr_salic completed exit=0 duration=48s' },
  { level: 'err',   t: '14:29:01', source: 'cron',    msg: 'cr_monday failed: 503 upstream \u00b7 disabled after 3 consecutive' },
  { level: 'info',  t: '14:28:41', source: 'http',    msg: 'GET /ops/overview 200 \u00b7 6ms' },
  { level: 'info',  t: '14:28:14', source: 'agent',   msg: 'hermes-primary edit_file \u00b7 3 stages isolated' },
  { level: 'dim',   t: '14:28:02', source: 'chat',    msg: 'operator message received \u00b7 sess_9f21c4' },
  { level: 'info',  t: '14:27:50', source: 'runtime', msg: 'heartbeat ok \u00b7 runtime=online \u00b7 event_bus=online' },
  { level: 'warn',  t: '14:27:11', source: 'http',    msg: 'GET /ops/files 200 \u00b7 412ms (slow)' },
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

async function tryLoadLiveData() {
  const overview = await fetchJson('/ops/overview');
  if (!overview) return;

  if (overview.agents) window.HC_DATA.agents = overview.agents;
  if (overview.sessions) window.HC_DATA.sessions = overview.sessions;
  if (overview.events) window.HC_DATA.events = overview.events;
  if (overview.approvals) window.HC_DATA.approvals = overview.approvals;
  if (overview.system_health) window.HC_DATA.systemHealth = overview.system_health;

  const usageData = await fetchJson('/ops/usage');
  if (usageData) window.HC_DATA.usage = usageData;

  const cronData = await fetchJson('/runtime/cron/jobs');
  if (cronData && cronData.jobs) window.HC_DATA.cron = cronData.jobs;

  const doctorData = await fetchJson('/health/doctor');
  if (doctorData && doctorData.checks) window.HC_DATA.doctor = doctorData.checks;
}

tryLoadLiveData();
