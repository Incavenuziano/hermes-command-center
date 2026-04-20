/* Hermes Command Center — Pages C: Terminal, Logs, Doctor, Config, Processes, other */
const { useState: usC, useEffect: ueC, useRef: urC } = React;
const { formatSaoPauloTime } = window.HC_TIME;

function TerminalPage({ data }) {
  const [lines, setLines] = usC([
    { t: 'info', text: '$ hermes connect --loopback' },
    { t: 'dim',  text: 'establishing session on 127.0.0.1:8787\u2026' },
    { t: 'info', text: 'passkey verified \u00b7 operator' },
    { t: 'dim',  text: 'loaded skills: 6 \u00b7 memory scopes: 5' },
    { t: 'out',  text: 'hermes runtime online \u00b7 event bus attached \u00b7 watchdog heartbeating' },
    { t: 'dim',  text: '$ hermes tail --filter approval' },
  ]);
  const termRef = urC(null);
  ueC(() => {
    const pool = [
      { t: 'out',  text: '[14:32:18] approval.requested \u00b7 ap_991 \u00b7 file.edit backend/ingest/salic.py' },
      { t: 'info', text: '[14:32:21] operator: approve ap_991' },
      { t: 'out',  text: '[14:32:22] approval.resolved \u00b7 ap_991 \u00b7 approved by operator' },
      { t: 'dim',  text: '[14:32:25] agent hermes-primary committed diff \u00b7 48 lines' },
      { t: 'warn', text: '[14:32:41] cost.threshold \u00b7 42% of daily budget ($4.20 / $10.00)' },
      { t: 'out',  text: '[14:33:02] tool.invoked \u00b7 run_tests \u00b7 pytest backend/ingest/ -k salic' },
      { t: 'dim',  text: '[14:33:08] pytest passed \u00b7 12/12 \u00b7 6.4s' },
    ];
    let i = 0;
    const timer = setInterval(() => {
      if (i >= pool.length) return clearInterval(timer);
      setLines(prev => [...prev, pool[i++]]);
      if (termRef.current) termRef.current.scrollTop = termRef.current.scrollHeight;
    }, 1400);
    return () => clearInterval(timer);
  }, []);
  return (
    <div className="hc-grid hc-grid-1-2" style={{ height: 'calc(100vh - 56px - 40px - 60px)', minHeight: 560 }}>
      <Panel title="Terminal policy" icon="shield" sub="risk posture">
        <dl className="hc-kv">
          <dt>mode</dt><dd><Tag tone="warn">limited</Tag></dd>
          <dt>interactive</dt><dd><Tag tone="err">disabled</Tag></dd>
          <dt>risk posture</dt><dd>restrictive</dd>
          <dt>revisit</dt><dd className="hc-mono">milestone m2</dd>
        </dl>
        <div className="hc-divider" />
        <p className="hc-text-sec" style={{ fontSize: 12, lineHeight: 1.55 }}>
          Interactive terminal sessions are gated behind an explicit operator gesture. Automated agents may only invoke whitelisted commands through the <span className="hc-mono hc-text-primary">shell.run</span> approval flow.
        </p>
        <div className="hc-flex-col" style={{ gap: 8, marginTop: 12 }}>
          <button className="hc-btn primary" style={{ justifyContent: 'center' }}><Icon name="play" size={12} /> Open read-only shell</button>
          <button className="hc-btn" style={{ justifyContent: 'center' }}>Request elevated session</button>
        </div>
      </Panel>

      <Panel title="hermes \u00b7 loopback" icon="terminal" sub="operator@hermes:~"
        actions={[
          <Tag key="l" tone="ok"><Icon name="radio" size={10} />&nbsp;LIVE</Tag>,
          <button key="c" className="hc-btn sm ghost"><Icon name="x" size={12} /> Clear</button>,
        ]}
        className="hc-split-detail">
        <div ref={termRef} className="hc-term">
          {lines.map((l, i) => (
            <div key={i} className={l.t === 'dim' ? 'dim' : l.t === 'warn' ? 'warn' : l.t === 'err' ? 'err' : l.t === 'info' ? 'info' : ''}>
              {l.text}
            </div>
          ))}
          <div><span className="dim">$ </span><span className="hc-term-cursor" /></div>
        </div>
      </Panel>
    </div>
  );
}

function LogsPage({ data }) {
  const [filter, setFilter] = usC('all');
  const [extras, setExtras] = usC([]);
  ueC(() => {
    const pool = [
      { level: 'info', source: 'http',    msg: 'GET /ops/cron/jobs 200 \u00b7 8ms' },
      { level: 'info', source: 'event',   msg: 'emit tool.invoked \u00b7 hermes-primary \u00b7 grep_search' },
      { level: 'warn', source: 'cost',    msg: 'projection 6.8h \u00b7 consider raising budget' },
      { level: 'info', source: 'agent',   msg: 'indexer-docs committed embedding batch \u00b7 128 docs' },
    ];
    const timer = setInterval(() => {
      const e = pool[Math.floor(Math.random() * pool.length)];
      const t = formatSaoPauloTime(new Date()).replace(' BRT', '');
      setExtras(prev => [{ ...e, t, _id: 'l_' + Math.random().toString(36).slice(2,6) }, ...prev].slice(0, 20));
    }, 2400);
    return () => clearInterval(timer);
  }, []);

  const all = [...extras, ...data.logs];
  const filtered = filter === 'all' ? all : all.filter(l => l.level === filter);

  return (
    <Panel title="Log stream" icon="logs" sub={`${filtered.length} entries`}
      actions={[
        <div key="seg" className="hc-tweak-seg" style={{ gridTemplateColumns: 'repeat(4, 1fr)' }}>
          {['all','info','warn','err'].map(f => (
            <button key={f} className={filter === f ? 'active' : ''} onClick={() => setFilter(f)}>{f}</button>
          ))}
        </div>,
        <Tag key="l" tone="ok"><Icon name="radio" size={10} />&nbsp;LIVE</Tag>,
        <button key="d" className="hc-btn sm ghost"><Icon name="download" size={12} /></button>,
      ]}>
      <div className="hc-pre" style={{ maxHeight: 560, overflow: 'auto', background: '#000', fontSize: 12, lineHeight: 1.7 }}>
        {filtered.map((l, i) => (
          <div key={l._id || i} style={{ color: l.level === 'warn' ? 'var(--warning)' : l.level === 'err' ? 'var(--danger)' : l.level === 'dim' ? 'var(--text-muted)' : 'var(--text-secondary)' }}>
            <span style={{ color: 'var(--text-muted)' }}>{l.t}</span>
            <span style={{ color: 'var(--accent)', marginLeft: 8 }}>{l.level.toUpperCase().padEnd(4)}</span>
            <span style={{ color: 'var(--text-muted)', marginLeft: 8 }}>[{l.source.padEnd(7)}]</span>
            <span style={{ marginLeft: 8 }}>{l.msg}</span>
          </div>
        ))}
      </div>
    </Panel>
  );
}

function DoctorPage({ data }) {
  const counts = data.doctor.reduce((a, x) => (a[x.status] = (a[x.status] || 0) + 1, a), {});
  return (
    <div className="hc-flex-col" style={{ gap: 16 }}>
      <div className="hc-grid hc-grid-4">
        <Stat label="Checks" value={data.doctor.length} icon="doctor" />
        <Stat label="OK"     value={counts.ok || 0} delta="healthy" icon="check" />
        <Stat label="Warn"   value={counts.warn || 0} delta="open exceptions" deltaDir="" icon="alert" />
        <Stat label="Errors" value={counts.err || 0} delta="action required" deltaDir="down" icon="alert" />
      </div>

      <Panel title="Diagnostics" icon="doctor" sub="hermes runtime + subsystems"
        actions={<button className="hc-btn sm primary"><Icon name="refresh" size={12} /> Re-run</button>}>
        <table className="hc-tbl">
          <thead><tr><th>Check</th><th>Status</th><th>Detail</th><th></th></tr></thead>
          <tbody>
            {data.doctor.map(d => (
              <tr key={d.name}>
                <td className="hc-text-primary">{d.name}</td>
                <td><Tag tone={d.status}>{d.status}</Tag></td>
                <td className="hc-text-sec">{d.detail}</td>
                <td><button className="hc-btn sm ghost"><Icon name="eye" size={12} /></button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      <div className="hc-grid hc-grid-2">
        <Panel title="System info" icon="server">
          <dl className="hc-kv">
            <dt>service</dt><dd className="hc-mono">hermes-command-center</dd>
            <dt>version</dt><dd className="hc-mono">{data.systemHealth.version}</dd>
            <dt>environment</dt><dd className="hc-mono">{data.systemHealth.env}</dd>
            <dt>bind</dt><dd className="hc-mono">{data.systemHealth.bind}</dd>
            <dt>auth</dt><dd className="hc-mono">{data.systemHealth.auth}</dd>
            <dt>uptime</dt><dd className="hc-mono">{data.systemHealth.uptime}</dd>
          </dl>
        </Panel>
        <Panel title="Processes" icon="cpu" sub={`${data.processes.length} tracked`}>
          <table className="hc-tbl">
            <thead><tr><th>Process</th><th>PID</th><th>CPU</th><th>Mem</th></tr></thead>
            <tbody>
              {data.processes.map(p => (
                <tr key={p.id}>
                  <td>
                    <div className="hc-mono hc-text-primary" style={{ fontSize: 12 }}>{p.id}</div>
                    <div className="hc-meta-line" style={{ marginTop: 2 }}>{p.command}</div>
                  </td>
                  <td className="mono">{p.pid}</td>
                  <td className="mono">{p.cpu}%</td>
                  <td className="mono">{p.mem}MB</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      </div>
    </div>
  );
}

function PlaceholderPage({ title, hint }) {
  return (
    <Panel title={title}>
      <div className="hc-empty">
        <Icon name="config" size={32} />
        <div className="msg">{hint || 'Ainda n\u00e3o populada.'}</div>
        <div className="msg hc-mono" style={{ fontSize: 11 }}>Page scope captured in backlog {'\u00b7'} m1</div>
      </div>
    </Panel>
  );
}

window.TerminalPage = TerminalPage;
window.LogsPage = LogsPage;
window.DoctorPage = DoctorPage;
window.PlaceholderPage = PlaceholderPage;
