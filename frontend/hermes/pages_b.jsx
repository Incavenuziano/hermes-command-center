/* Hermes Command Center — Pages B: Usage, Cron, Memory, Documents */
const { useState: usB } = React;

function postJsonB(path, body) {
  return fetch(path, { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
    .then(r => r.json()).catch(() => null);
}

function UsagePage({ data }) {
  const u = data.usage;
  const pct = Math.round((u.today.cost / u.today.budget) * 100);
  return (
    <div className="hc-flex-col" style={{ gap: 16 }}>
      <div className="hc-grid hc-grid-4">
        <Stat label="Tokens today" value={(u.today.tokens/1000).toFixed(1)+'k'} delta="+24%" deltaDir="up" icon="zap" spark={u.hourly.slice(-12)} />
        <Stat label="Actual cost" value={'$'+u.today.cost.toFixed(2)} delta={`${pct}% of $${u.today.budget.toFixed(2)}`} deltaDir="" icon="usage" spark={u.hourly.slice(-12).map(v=>v*0.008)} />
        <Stat label="Sessions" value={u.today.sessions} delta="+3" deltaDir="up" icon="sessions" />
        <Stat label="Requests" value={u.today.requests} delta="+41" deltaDir="up" icon="apis" />
      </div>

      <div className="hc-grid hc-grid-2-1">
        <Panel title="Hourly burn" icon="trending" sub="last 24h \u00b7 tokens per hour"
          actions={<Tag tone={pct > 80 ? 'warn' : 'ok'}>{pct}% of budget</Tag>}>
          <UsageChart values={u.hourly} />
          <div className="hc-flex" style={{ justifyContent: 'space-between', marginTop: 8 }}>
            <span className="hc-mono hc-muted" style={{ fontSize: 11 }}>-24h</span>
            <span className="hc-mono hc-muted" style={{ fontSize: 11 }}>-18h</span>
            <span className="hc-mono hc-muted" style={{ fontSize: 11 }}>-12h</span>
            <span className="hc-mono hc-muted" style={{ fontSize: 11 }}>-6h</span>
            <span className="hc-mono hc-muted" style={{ fontSize: 11 }}>now</span>
          </div>
        </Panel>

        <Panel title="Circuit breaker" icon="shield" sub={u.breaker.tripped ? 'tripped' : 'healthy'}>
          <dl className="hc-kv">
            <dt>status</dt><dd><Tag tone={u.breaker.tripped ? 'err' : 'ok'}>{u.breaker.tripped ? 'tripped' : 'healthy'}</Tag></dd>
            <dt>max cost</dt><dd className="hc-mono">${u.breaker.maxCost.toFixed(2)}</dd>
            <dt>max tokens</dt><dd className="hc-mono">{u.breaker.maxTokens.toLocaleString()}</dd>
          </dl>
          <div className="hc-divider" />
          <label className="hc-tweak-row"><label style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Max cost (USD)</label>
            <input id="hc-breaker-cost" defaultValue={u.breaker.maxCost.toFixed(2)} style={{ padding: '6px 10px', background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', borderRadius: 6, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: 13, outline: 'none' }} />
          </label>
          <label className="hc-tweak-row"><label style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Max tokens</label>
            <input id="hc-breaker-tokens" defaultValue={u.breaker.maxTokens} style={{ padding: '6px 10px', background: 'var(--bg-input)', border: '1px solid var(--border-subtle)', borderRadius: 6, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)', fontSize: 13, outline: 'none' }} />
          </label>
          <button className="hc-btn primary" style={{ width: '100%', marginTop: 8, justifyContent: 'center' }}
            onClick={() => {
              const cost = parseFloat(document.getElementById('hc-breaker-cost')?.value);
              const tokens = parseInt(document.getElementById('hc-breaker-tokens')?.value, 10);
              if (!isNaN(cost) && !isNaN(tokens)) postJsonB('/ops/costs/circuit-breaker', { max_actual_cost_usd: cost, max_total_tokens: tokens }).then(r => { if (r) window.location.reload(); });
            }}>Update breaker</button>
        </Panel>
      </div>

      <Panel title="Agent breakdown" icon="agents" sub="tokens \u00b7 cost \u00b7 sessions">
        <table className="hc-tbl">
          <thead><tr><th>Agent</th><th>Sessions</th><th>Tokens</th><th className="col-r">% share</th><th className="col-r">Cost</th></tr></thead>
          <tbody>
            {u.agents.map(a => {
              const share = (a.tokens / u.today.tokens) * 100;
              return (
                <tr key={a.id}>
                  <td className="hc-text-primary">{a.id}</td>
                  <td className="mono">{a.sessions}</td>
                  <td className="mono">{a.tokens.toLocaleString()}</td>
                  <td style={{ width: 220 }}>
                    <div className="hc-flex" style={{ gap: 8 }}>
                      <Bar value={share} max={100} tone={share > 50 ? 'warn' : ''} />
                      <span className="mono" style={{ width: 44, textAlign: 'right' }}>{share.toFixed(1)}%</span>
                    </div>
                  </td>
                  <td className="mono col-r">${a.cost.toFixed(2)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Panel>
    </div>
  );
}

function UsageChart({ values }) {
  const w = 800, h = 180, pad = 16;
  const max = Math.max(...values, 1);
  const step = (w - pad * 2) / (values.length - 1);
  const pts = values.map((v, i) => [pad + i * step, h - pad - (v / max) * (h - pad * 2)]);
  const line = pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ',' + p[1].toFixed(1)).join(' ');
  const area = line + ` L${w - pad},${h - pad} L${pad},${h - pad} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} style={{ width: '100%', height: 180 }} preserveAspectRatio="none">
      <defs>
        <linearGradient id="hc-usage-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.35" />
          <stop offset="100%" stopColor="var(--accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75].map(g => <line key={g} x1={pad} x2={w-pad} y1={pad + (h - pad*2) * g} y2={pad + (h - pad*2) * g} stroke="var(--grid-lines)" />)}
      <path d={area} fill="url(#hc-usage-grad)" />
      <path d={line} fill="none" stroke="var(--accent)" strokeWidth="1.75" />
      {pts.map((p, i) => i % 4 === 0 && <circle key={i} cx={p[0]} cy={p[1]} r="2" fill="var(--accent)" />)}
    </svg>
  );
}

function CronPage({ data }) {
  const [sel, setSel] = usB(data.cron[0]);
  const history = [
    { id: sel.id + '_h1', at: '11:30:58 BRT', status: 'ok',   duration: '48s',   exit: 0 },
    { id: sel.id + '_h2', at: '11:00:58 BRT', status: 'ok',   duration: '51s',   exit: 0 },
    { id: sel.id + '_h3', at: '10:30:58 BRT', status: 'warn', duration: '2m 14s',exit: 0 },
    { id: sel.id + '_h4', at: '10:00:58 BRT', status: 'ok',   duration: '44s',   exit: 0 },
    { id: sel.id + '_h5', at: '09:30:58 BRT', status: 'err',  duration: '5m 12s',exit: 503 },
  ];
  return (
    <div className="hc-split">
      <Panel title="Cron jobs" icon="cron" sub={`${data.cron.length} jobs \u00b7 1 disabled`}
        actions={<button className="hc-btn sm primary"><Icon name="plus" size={12} /> New job</button>}
        className="hc-split-list">
        <table className="hc-tbl">
          <thead><tr><th>Name</th><th>Schedule</th><th>Last</th><th>Next</th><th></th></tr></thead>
          <tbody>
            {data.cron.map(c => (
              <tr key={c.id} className={sel?.id === c.id ? 'selected' : ''} onClick={() => setSel(c)}>
                <td>
                  <div className="hc-text-primary">{c.name}</div>
                  <div className="hc-meta-line" style={{ marginTop: 2 }}>{c.id} {'\u00b7'} {c.duration}</div>
                </td>
                <td className="mono">{c.schedule}</td>
                <td><Tag tone={c.last === 'err' ? 'err' : c.last === 'warn' ? 'warn' : 'ok'}>{c.last}</Tag></td>
                <td className="mono">{c.next}</td>
                <td>
                  <button className="hc-btn sm ghost" onClick={(e) => { e.stopPropagation(); postJsonB('/ops/cron/control', { job_id: c.id, action: c.enabled ? 'pause' : 'resume' }).then(r => { if (r) window.location.reload(); }); }}><Icon name={c.enabled ? 'pause' : 'play'} size={12} /></button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      {sel && (
        <Panel title={sel.name} icon="cron" sub={sel.id}
          actions={[
            <button key="r" className="hc-btn sm primary" onClick={() => postJsonB('/ops/cron/control', { job_id: sel.id, action: 'run' }).then(r => { if (r) window.location.reload(); })}><Icon name="play" size={12} /> Run now</button>,
            <button key="p" className="hc-btn sm" onClick={() => postJsonB('/ops/cron/control', { job_id: sel.id, action: sel.enabled ? 'pause' : 'resume' }).then(r => { if (r) window.location.reload(); })}><Icon name={sel.enabled ? 'pause' : 'play'} size={12} /> {sel.enabled ? 'Pause' : 'Resume'}</button>,
          ]}
          className="hc-split-detail">
          <dl className="hc-kv">
            <dt>schedule</dt><dd className="hc-mono">{sel.schedule}</dd>
            <dt>next run</dt><dd className="hc-mono">{sel.next}</dd>
            <dt>last run</dt><dd><Tag tone={sel.last==='err'?'err':sel.last==='warn'?'warn':'ok'}>{sel.last}</Tag></dd>
            <dt>avg duration</dt><dd className="hc-mono">{sel.duration}</dd>
            <dt>enabled</dt><dd>{sel.enabled ? <Tag tone="ok">yes</Tag> : <Tag tone="warn">paused</Tag>}</dd>
          </dl>
          <div className="hc-divider" />
          <div className="hc-panel-head" style={{ padding: 0, marginBottom: 10, borderBottom: 'none' }}>
            <h2><Icon name="clock" size={14} /> Run history</h2>
            <span className="sub">last 5</span>
          </div>
          <table className="hc-tbl">
            <thead><tr><th>When</th><th>Status</th><th>Duration</th><th className="col-r">Exit</th></tr></thead>
            <tbody>
              {history.map(h => (
                <tr key={h.id}>
                  <td className="mono">{h.at}</td>
                  <td><Tag tone={h.status}>{h.status}</Tag></td>
                  <td className="mono">{h.duration}</td>
                  <td className="mono col-r">{h.exit}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="hc-divider" />
          <div className="hc-panel-head" style={{ padding: 0, marginBottom: 10, borderBottom: 'none' }}>
            <h2><Icon name="terminal" size={14} /> Last output</h2>
          </div>
          <pre className="hc-pre">{`$ ${sel.name.toLowerCase().replace(/ /g,'-')} --run
[11:30:58 BRT] starting\u2026
[11:30:58 BRT] fetched 248 records
[11:31:14 BRT] normalized 248 records
[11:31:32 BRT] deduped \u00b7 12 duplicates dropped
[11:31:46 BRT] upserted \u00b7 236 rows
[11:31:46 BRT] done \u00b7 exit 0
# timezone: America/Sao_Paulo (BRT, UTC-03:00)`}</pre>
        </Panel>
      )}
    </div>
  );
}

function MemoryPage({ data }) {
  const [sel, setSel] = usB(data.memory[0]);
  return (
    <div className="hc-split">
      <Panel title="Memory" icon="memory" sub={`${data.memory.length} scopes`}
        actions={<button className="hc-btn sm primary"><Icon name="plus" size={12} /> New scope</button>}
        className="hc-split-list">
        <div style={{ margin: -14 }}>
          {data.memory.map(m => (
            <div key={m.scope} className={`hc-row ${sel?.scope === m.scope ? 'selected' : ''}`} onClick={() => setSel(m)}>
              <Icon name="memory" size={14} style={{ color: 'var(--text-muted)' }} />
              <div className="hc-grow" style={{ minWidth: 0 }}>
                <div className="hc-mono hc-text-primary" style={{ fontSize: 12 }}>{m.scope}</div>
                <div className="hc-text-sec" style={{ fontSize: 12, marginTop: 2, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{m.preview}</div>
              </div>
              <span className="hc-mono hc-muted" style={{ fontSize: 10 }}>{m.updated}</span>
            </div>
          ))}
        </div>
      </Panel>

      {sel && (
        <Panel title={sel.scope} icon="memory" sub={'updated ' + sel.updated}
          actions={[<button key="e" className="hc-btn sm ghost">Edit</button>, <button key="d" className="hc-btn sm danger"><Icon name="x" size={12} /></button>]}
          className="hc-split-detail">
          <p className="hc-text-primary" style={{ lineHeight: 1.6 }}>{sel.preview}</p>
          <div className="hc-divider" />
          <pre className="hc-pre">{JSON.stringify({ scope: sel.scope, preview: sel.preview, updated_at: sel.updated, facts: [{ id: 'f_1', text: sel.preview, provenance: 'operator', confidence: 0.98 }] }, null, 2)}</pre>
        </Panel>
      )}
    </div>
  );
}

function DocumentsPage({ data }) {
  const [sel, setSel] = usB(data.files[0]);
  return (
    <div className="hc-split">
      <Panel title="Workspace files" icon="documents" sub={`${data.files.length} tracked`} className="hc-split-list">
        <table className="hc-tbl">
          <thead><tr><th>Path</th><th className="col-r">Size</th><th>Updated</th></tr></thead>
          <tbody>
            {data.files.map(f => (
              <tr key={f.path} className={sel?.path === f.path ? 'selected' : ''} onClick={() => setSel(f)}>
                <td>
                  <div className="hc-mono hc-text-primary">{f.path}</div>
                  <div className="hc-meta-line" style={{ marginTop: 2 }}>{f.preview}</div>
                </td>
                <td className="mono col-r">{f.size}</td>
                <td className="mono">{f.updated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
      {sel && (
        <Panel title={sel.path.split('/').pop()} icon="documents" sub={sel.path}
          actions={[<button key="o" className="hc-btn sm ghost"><Icon name="eye" size={12} /> Open</button>,<button key="d" className="hc-btn sm"><Icon name="download" size={12} /></button>]}
          className="hc-split-detail">
          <dl className="hc-kv">
            <dt>path</dt><dd className="hc-mono">{sel.path}</dd>
            <dt>size</dt><dd className="hc-mono">{sel.size}</dd>
            <dt>updated</dt><dd className="hc-mono">{sel.updated}</dd>
            <dt>preview</dt><dd>{sel.preview}</dd>
          </dl>
          <div className="hc-divider" />
          <pre className="hc-pre">{`# ${sel.path}
# ${sel.size} \u00b7 updated ${sel.updated}

${sel.preview}

...`}</pre>
        </Panel>
      )}
    </div>
  );
}

window.UsagePage = UsagePage;
window.CronPage = CronPage;
window.MemoryPage = MemoryPage;
window.DocumentsPage = DocumentsPage;
