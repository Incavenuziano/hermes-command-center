/* Hermes Command Center — Orchestration page (Hermes ↔ OpenClaw delegation timeline) */
const { useState: usOrch, useEffect: ueOrch } = React;

const POLL_INTERVAL_MS = 5000; // fallback only
const SSE_RECONNECT_MS = 3000;

const EVENT_TONE = {
  'task.delegated': 'accent',
  'task.completed': 'ok',
  'task.failed': 'danger',
  'task.blocked': 'warn',
  'context.shared': 'neutral',
  'human.intervention_requested': 'warn',
};

const EVENT_EMOJI = {
  'task.delegated': '🚀',
  'task.completed': '✅',
  'task.failed': '🔴',
  'task.blocked': '🟡',
  'context.shared': '📎',
  'human.intervention_requested': '🆘',
};

function eventTone(eventType) {
  return EVENT_TONE[eventType] || 'neutral';
}

function eventEmoji(eventType) {
  return EVENT_EMOJI[eventType] || 'ℹ️';
}

function formatRelative(iso) {
  if (!iso) return '';
  try {
    const dt = new Date(iso);
    const diffSecs = Math.floor((Date.now() - dt.getTime()) / 1000);
    if (diffSecs < 0) return 'agora';
    if (diffSecs < 60) return `${diffSecs}s atrás`;
    if (diffSecs < 3600) return `${Math.floor(diffSecs / 60)}m atrás`;
    if (diffSecs < 86400) return `${Math.floor(diffSecs / 3600)}h atrás`;
    return `${Math.floor(diffSecs / 86400)}d atrás`;
  } catch {
    return iso;
  }
}

function formatTime(iso) {
  if (!iso) return '';
  try {
    const dt = new Date(iso);
    return dt.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch {
    return iso;
  }
}

function deriveRunTone(status) {
  return {
    completed: 'ok',
    failed: 'danger',
    blocked: 'warn',
    running: 'accent',
    unknown: 'neutral',
  }[status] || 'neutral';
}

function RunCard({ run, expanded, events, loadingEvents, onToggle }) {
  const tone = deriveRunTone(run.status);
  const summary = run.primary_goal || run.run_id;
  const target = run.target_agent || 'siriguejo';

  return (
    <div className={`hc-card orch-run-card tone-${tone}`} style={{ marginBottom: 12 }}>
      <div
        className="orch-run-header"
        onClick={onToggle}
        style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10 }}
      >
        <span className={`memory-scope-pill ${tone}`} style={{ minWidth: 80, textAlign: 'center' }}>
          {run.status || 'unknown'}
        </span>
        <span style={{ flex: 1, fontWeight: 500, fontSize: 13 }} title={summary}>
          {summary.length > 80 ? summary.slice(0, 77) + '…' : summary}
        </span>
        <span className="hc-muted" style={{ fontSize: 11 }}>
          {target} · {formatRelative(run.updated_at || run.created_at)}
        </span>
        <Icon name={expanded ? 'chevronDown' : 'chevronRight'} size={12} stroke={2} />
      </div>

      {expanded && (
        <div className="orch-run-events" style={{ marginTop: 10, borderTop: '1px solid var(--hc-border)', paddingTop: 10 }}>
          <div className="hc-muted" style={{ fontSize: 10, marginBottom: 6, display: 'flex', justifyContent: 'space-between', gap: 10 }}>
            <span>run_id: <code style={{ userSelect: 'all' }}>{run.run_id}</code></span>
            <span>{run.event_count || 0} evento(s)</span>
          </div>
          {loadingEvents && (
            <div className="hc-muted" style={{ fontSize: 12, marginBottom: 8 }}>Carregando timeline do run…</div>
          )}
          {!loadingEvents && events.length === 0 && (
            <div className="hc-muted" style={{ fontSize: 12, marginBottom: 8 }}>Nenhum evento encontrado para este run.</div>
          )}
          {events.map((ev, i) => (
            <div key={ev.event_id || i} className="orch-event-row" style={{ display: 'flex', gap: 8, alignItems: 'flex-start', padding: '4px 0', borderBottom: '1px solid var(--hc-border-subtle, #f0f0f0)' }}>
              <span style={{ width: 20, textAlign: 'center', flexShrink: 0 }}>{eventEmoji(ev.event_type)}</span>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                  <span className={`memory-scope-pill ${eventTone(ev.event_type)}`} style={{ fontSize: 10, padding: '1px 6px' }}>
                    {ev.event_type}
                  </span>
                  <span className="hc-muted" style={{ fontSize: 10 }}>{formatTime(ev.recorded_at)}</span>
                  {ev.source && <span className="hc-muted" style={{ fontSize: 10 }}>· {ev.source}</span>}
                </div>
                {ev.payload?.summary && (
                  <div style={{ fontSize: 12, marginTop: 3, color: 'var(--hc-text-secondary, #555)' }}>
                    {ev.payload.summary}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function OrchestrationPage() {
  const [runs, setRuns] = usOrch([]);
  const [loading, setLoading] = usOrch(true);
  const [error, setError] = usOrch(null);
  const [expanded, setExpanded] = usOrch({});
  const [filter, setFilter] = usOrch('all');
  const [filterAgent, setFilterAgent] = usOrch('all');
  const [filterDateFrom, setFilterDateFrom] = usOrch('');
  const [filterDateTo, setFilterDateTo] = usOrch('');
  const [filterErrorsOnly, setFilterErrorsOnly] = usOrch(false);
  const [runEvents, setRunEvents] = usOrch({});
  const [loadingRuns, setLoadingRuns] = usOrch({});
  const [sseConnected, setSseConnected] = usOrch(false);
  const [lastSseEventId, setLastSseEventId] = usOrch(null);

  async function fetchRuns() {
    const resp = await fetch('/ops/delegation/runs?limit=100', { credentials: 'same-origin' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const body = await resp.json();
    return body.data?.items || body.items || [];
  }

  async function fetchRunEvents(runId) {
    const resp = await fetch(`/ops/delegation/run-events?run_id=${encodeURIComponent(runId)}&limit=100`, { credentials: 'same-origin' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    const body = await resp.json();
    return body.data?.items || body.items || [];
  }

  async function loadRuns() {
    try {
      const items = await fetchRuns();
      setRuns(items);
      setError(null);
    } catch (err) {
      setError(err.message || 'Erro ao carregar runs');
    } finally {
      setLoading(false);
    }
  }

  async function ensureRunEvents(runId) {
    setLoadingRuns(prev => ({ ...prev, [runId]: true }));
    try {
      const items = await fetchRunEvents(runId);
      setRunEvents(prev => ({ ...prev, [runId]: items }));
      setError(null);
    } catch (err) {
      setError(err.message || 'Erro ao carregar eventos do run');
    } finally {
      setLoadingRuns(prev => ({ ...prev, [runId]: false }));
    }
  }

  // SSE connection with polling fallback
  ueOrch(() => {
    let cancelled = false;
    let source = null;
    let fallbackTimer = null;
    let reconnectTimer = null;
    let lastEventId = lastSseEventId;

    function startFallbackPolling() {
      if (cancelled || fallbackTimer) return;
      fallbackTimer = setInterval(() => {
        if (cancelled) return;
        loadRuns();
        Object.keys(expanded).forEach(runId => {
          if (expanded[runId]) ensureRunEvents(runId);
        });
      }, POLL_INTERVAL_MS);
    }

    function stopFallbackPolling() {
      if (fallbackTimer) {
        clearInterval(fallbackTimer);
        fallbackTimer = null;
      }
    }

    function connectSSE() {
      if (cancelled || typeof EventSource === 'undefined') {
        startFallbackPolling();
        return;
      }
      const query = lastEventId != null ? `?after_id=${encodeURIComponent(lastEventId)}` : '';
      source = new EventSource(`/ops/stream${query}`, { withCredentials: true });

      source.onopen = () => {
        if (!cancelled) {
          setSseConnected(true);
          stopFallbackPolling();
        }
      };

      // Delegation event types emitted by the bridge
      const DELEGATION_EVENTS = ['task.delegated', 'task.completed', 'task.failed', 'task.blocked', 'context.shared', 'human.intervention_requested'];
      DELEGATION_EVENTS.forEach(evtName => {
        source.addEventListener(evtName, (msg) => {
          if (cancelled) return;
          try {
            const parsed = JSON.parse(msg.data || '{}');
            if (msg.lastEventId) {
              lastEventId = msg.lastEventId;
              setLastSseEventId(msg.lastEventId);
            }
            // Reload runs to pick up new/updated run from this event
            if (parsed.channel === 'delegation' || parsed.payload) {
              loadRuns();
              // Also refresh expanded run events
              Object.keys(expanded).forEach(runId => {
                if (expanded[runId]) ensureRunEvents(runId);
              });
            }
          } catch (_) {}
        });
      });

      // Track last-event-id from activity events too
      source.addEventListener('activity', (msg) => {
        if (cancelled) return;
        if (msg.lastEventId) {
          lastEventId = msg.lastEventId;
          setLastSseEventId(msg.lastEventId);
        }
      });

      source.onerror = () => {
        if (cancelled) return;
        setSseConnected(false);
        if (source) { source.close(); source = null; }
        // SSE is finite (server closes after replay) — reconnect after delay
        reconnectTimer = setTimeout(() => {
          if (!cancelled) connectSSE();
        }, SSE_RECONNECT_MS);
      };
    }

    // Initial load + SSE connection
    loadRuns();
    connectSSE();

    return () => {
      cancelled = true;
      setSseConnected(false);
      if (source) { source.close(); source = null; }
      stopFallbackPolling();
      if (reconnectTimer) clearTimeout(reconnectTimer);
    };
  }, [expanded]);

  function toggleRun(runId) {
    const nextExpanded = !expanded[runId];
    setExpanded(prev => ({ ...prev, [runId]: nextExpanded }));
    if (nextExpanded) ensureRunEvents(runId);
  }

  // Derived: unique agents from runs
  const allAgents = [...new Set(runs.flatMap(run => [run.target_agent, run.source_agent].filter(Boolean)))].sort();

  // Apply all filters
  const visibleRuns = runs.filter(run => {
    if (filter !== 'all' && String(run.status || '') !== filter) return false;
    if (filterAgent !== 'all') {
      const matchesAgent = run.target_agent === filterAgent || run.source_agent === filterAgent;
      if (!matchesAgent) return false;
    }
    if (filterDateFrom) {
      const runDate = new Date(run.created_at || run.updated_at || 0);
      if (runDate < new Date(filterDateFrom)) return false;
    }
    if (filterDateTo) {
      const runDate = new Date(run.created_at || run.updated_at || 0);
      const toEnd = new Date(filterDateTo);
      toEnd.setHours(23, 59, 59, 999);
      if (runDate > toEnd) return false;
    }
    if (filterErrorsOnly) {
      const s = run.status || '';
      if (s !== 'failed' && s !== 'blocked') return false;
    }
    return true;
  });

  const hasActiveFilters = filterAgent !== 'all' || filterDateFrom || filterDateTo || filterErrorsOnly;

  function clearExtraFilters() {
    setFilterAgent('all');
    setFilterDateFrom('');
    setFilterDateTo('');
    setFilterErrorsOnly(false);
  }

  const statusCounts = runs.reduce((acc, run) => {
    const key = run.status || 'unknown';
    acc[key] = (acc[key] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="hc-page-body" style={{ padding: '16px 20px' }}>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap' }}>
        {[
          { label: 'Rodando', key: 'running', tone: 'accent' },
          { label: 'Concluídas', key: 'completed', tone: 'ok' },
          { label: 'Falhas', key: 'failed', tone: 'danger' },
          { label: 'Bloqueadas', key: 'blocked', tone: 'warn' },
        ].map(({ label, key, tone }) => (
          <div
            key={key}
            className={`hc-card orch-stat-card ${tone}`}
            onClick={() => setFilter(filter === key ? 'all' : key)}
            style={{ cursor: 'pointer', padding: '8px 14px', minWidth: 100, textAlign: 'center', border: filter === key ? '2px solid var(--hc-accent)' : undefined }}
          >
            <div style={{ fontSize: 20, fontWeight: 700 }}>{statusCounts[key] || 0}</div>
            <div className="hc-muted" style={{ fontSize: 11 }}>{label}</div>
          </div>
        ))}
        <div style={{ flex: 1 }} />
        <button
          className="hc-btn sm ghost"
          onClick={() => loadRuns()}
          title="Recarregar"
          style={{ alignSelf: 'center' }}
        >
          <Icon name="refresh" size={13} stroke={2} />
          &nbsp;Atualizar
        </button>
      </div>

      {/* Extra filters row */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
        <select
          value={filterAgent}
          onChange={e => setFilterAgent(e.target.value)}
          style={{ fontSize: 12, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--hc-border)', background: 'var(--hc-surface)', color: 'var(--hc-text)', cursor: 'pointer' }}
          title="Filtrar por agente"
        >
          <option value="all">Todos agentes</option>
          {allAgents.map(a => <option key={a} value={a}>{a}</option>)}
        </select>

        <input
          type="date"
          value={filterDateFrom}
          onChange={e => setFilterDateFrom(e.target.value)}
          style={{ fontSize: 12, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--hc-border)', background: 'var(--hc-surface)', color: 'var(--hc-text)' }}
          title="Data início"
        />
        <span className="hc-muted" style={{ fontSize: 11 }}>até</span>
        <input
          type="date"
          value={filterDateTo}
          onChange={e => setFilterDateTo(e.target.value)}
          style={{ fontSize: 12, padding: '4px 8px', borderRadius: 6, border: '1px solid var(--hc-border)', background: 'var(--hc-surface)', color: 'var(--hc-text)' }}
          title="Data fim"
        />

        <label style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, cursor: 'pointer', userSelect: 'none' }}>
          <input
            type="checkbox"
            checked={filterErrorsOnly}
            onChange={e => setFilterErrorsOnly(e.target.checked)}
            style={{ cursor: 'pointer' }}
          />
          Apenas erros/retries
        </label>

        {hasActiveFilters && (
          <button className="hc-btn xs ghost" onClick={clearExtraFilters} style={{ fontSize: 11, padding: '2px 8px' }}>
            Limpar filtros
          </button>
        )}
        <span className="hc-muted" style={{ fontSize: 10, marginLeft: 'auto' }}>
          {visibleRuns.length}/{runs.length} run(s)
        </span>
      </div>

      {loading && (
        <div className="hc-muted" style={{ fontSize: 12, marginBottom: 12 }}>Carregando runs…</div>
      )}
      {error && (
        <div className="hc-alert danger" style={{ marginBottom: 12, fontSize: 12 }}>
          <Icon name="alert" size={13} /> {error}
        </div>
      )}
      {!loading && !error && runs.length === 0 && (
        <div className="hc-empty-state">
          <Icon name="orchestration" size={32} stroke={1.5} />
          <p>Nenhuma delegação registrada ainda.</p>
          <p className="hc-muted" style={{ fontSize: 12 }}>Quando Hermes delegar algo ao OpenClaw via bridge, os runs aparecerão aqui.</p>
        </div>
      )}

      {visibleRuns.map(run => (
        <RunCard
          key={run.run_id}
          run={run}
          expanded={!!expanded[run.run_id]}
          events={runEvents[run.run_id] || []}
          loadingEvents={!!loadingRuns[run.run_id]}
          onToggle={() => toggleRun(run.run_id)}
        />
      ))}

      <div className="hc-muted" style={{ fontSize: 10, marginTop: 16, textAlign: 'right' }}>
        {sseConnected ? <span style={{ color: 'var(--hc-ok, #22c55e)' }}>● SSE live</span> : <span style={{ color: 'var(--hc-warn, #f59e0b)' }}>● reconectando… (fallback {POLL_INTERVAL_MS / 1000}s)</span>}
        {' · '}{visibleRuns.length}/{runs.length} run(s)
        {filter !== 'all' && <> · status: <strong>{filter}</strong> <button className="hc-btn xs ghost" onClick={() => setFilter('all')} style={{ fontSize: 10, padding: '1px 6px' }}>limpar</button></>}
        {hasActiveFilters && <> · filtros ativos</>}
      </div>
    </div>
  );
}

window.OrchestrationPage = OrchestrationPage;
