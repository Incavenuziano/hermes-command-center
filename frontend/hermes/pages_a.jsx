/* Hermes Command Center — Pages A: Dashboard, Agents, Sessions, Chat, Activity */
const { useState: usA, useEffect: ueA, useMemo: umA, useRef: urA } = React;
const { formatSaoPauloTime } = window.HC_TIME;

function postJson(path, body) {
  return fetch(path, {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
    .then(async (r) => {
      if (!r.ok) return null;
      try {
        return await r.json();
      } catch {
        return null;
      }
    })
    .catch(() => null);
}

function Dashboard({ data, setActive }) {
  const seedEvents = data.events.slice(0, 14).map((event, index) => ({
    ...event,
    _id: [event.kind || 'event', event.source || 'runtime', event.t || '—', event.title || `event-${index + 1}`, event.detail || ''].join('|'),
  }));
  const [liveEvents, setLiveEvents] = usA(seedEvents);
  const [newIds, setNewIds] = usA(new Set());
  const [streamConnected, setStreamConnected] = usA(false);
  const [streamEverOpened, setStreamEverOpened] = usA(false);
  const [realFeedReady, setRealFeedReady] = usA(false);
  const [lastEventId, setLastEventId] = usA(null);
  const lastEventIdRef = urA(null);
  const streamEverOpenedRef = urA(false);
  const realFeedReadyRef = urA(false);

  ueA(() => {
    let cancelled = false;
    let source = null;

    function eventFingerprint(event, index) {
      return event._id || [event.kind || 'event', event.source || 'runtime', event.t || '—', event.title || `event-${index + 1}`, event.detail || '', index].join('|');
    }

    function semanticFingerprint(event, index) {
      return [event.kind || 'event', event.source || 'runtime', event.t || '—', event.title || `event-${index + 1}`, event.detail || ''].join('|');
    }

    function normalizeSseEvent(messageEvent) {
      let parsed;
      try {
        parsed = JSON.parse(messageEvent.data || '{}');
      } catch {
        return null;
      }

      if (messageEvent.type === 'activity') {
        const eventId = messageEvent.lastEventId || parsed.id || null;
        return {
          _id: eventId ? `evt_${eventId}` : [parsed.kind || 'event', parsed.source || 'runtime', parsed.t || '—', parsed.title || messageEvent.type, parsed.detail || ''].join('|'),
          eventId: eventId ? String(eventId) : null,
          t: parsed.t ? formatSaoPauloTime(new Date(parsed.t)).replace(' BRT', '') : formatSaoPauloTime(new Date()).replace(' BRT', ''),
          kind: parsed.kind || 'event',
          source: parsed.source || 'runtime',
          title: parsed.title || messageEvent.type,
          tone: parsed.tone || '',
          detail: parsed.detail || '',
        };
      }

      const recordedAt = parsed.recorded_at || parsed.payload?.recorded_at || parsed.payload?.data?.recorded_at || null;
      const eventId = messageEvent.lastEventId || parsed.event_id || parsed.id || null;
      const envelopePayload = parsed.payload && typeof parsed.payload === 'object' ? parsed.payload : parsed;
      const payload = envelopePayload.data && typeof envelopePayload.data === 'object' ? envelopePayload.data : envelopePayload;
      const title = payload.title || payload.display_name || payload.session_id || payload.status || messageEvent.type;
      const detailValue = payload.detail || payload.preview || payload.result || payload.status || payload.data || '';
      const detail = typeof detailValue === 'string' ? detailValue : JSON.stringify(detailValue);

      return {
        _id: eventId ? `evt_${eventId}` : [messageEvent.type, parsed.source || payload.source || 'runtime', recordedAt || 'now', title, detail].join('|'),
        eventId: eventId ? String(eventId) : null,
        t: recordedAt ? formatSaoPauloTime(new Date(recordedAt)).replace(' BRT', '') : formatSaoPauloTime(new Date()).replace(' BRT', ''),
        kind: messageEvent.type || 'event',
        source: parsed.source || payload.source || 'runtime',
        title,
        tone: (messageEvent.type || '').includes('error') ? 'err' : ((messageEvent.type || '').includes('approval') ? 'acc' : ((payload.status || '').includes('fail') ? 'err' : '')),
        detail,
      };
    }

    function applyIncomingEvent(nextEvent) {
      if (!nextEvent || cancelled) return;
      if (nextEvent.eventId) {
        lastEventIdRef.current = nextEvent.eventId;
        setLastEventId(nextEvent.eventId);
      }
      setLiveEvents((prev) => {
        const existing = new Set(prev.map((event, index) => semanticFingerprint(event, index)));
        const nextFingerprint = semanticFingerprint(nextEvent, 0);
        if (existing.has(nextFingerprint)) {
          return prev;
        }
        return [nextEvent, ...prev].slice(0, 14);
      });
      setNewIds((prevNew) => {
        const next = new Set(prevNew);
        next.add(nextEvent._id);
        return next;
      });
      window.setTimeout(() => {
        setNewIds((prevNew) => {
          const next = new Set(prevNew);
          next.delete(nextEvent._id);
          return next;
        });
      }, 1200);
      realFeedReadyRef.current = true;
      setRealFeedReady(true);
    }

    function connectStream(afterId = null) {
      if (cancelled || typeof EventSource === 'undefined') return;
      const query = afterId ? `?after_id=${encodeURIComponent(afterId)}` : '';
      const streamUrl = `/ops/stream${query}`;
      source = new EventSource(streamUrl, { withCredentials: true });

      source.onopen = () => {
        if (!cancelled) {
          streamEverOpenedRef.current = true;
          setStreamConnected(true);
          setStreamEverOpened(true);
        }
      };

      ['activity'].forEach((eventName) => {
        source.addEventListener(eventName, (messageEvent) => {
          const normalized = normalizeSseEvent(messageEvent);
          applyIncomingEvent(normalized);
        });
      });

      source.onerror = () => {
        if (cancelled) return;
        if (source && source.readyState === EventSource.CLOSED) {
          setStreamConnected(streamEverOpenedRef.current || realFeedReadyRef.current);
          return;
        }
        setStreamConnected(false);
      };
    }

    connectStream(lastEventIdRef.current);
    return () => {
      cancelled = true;
      if (source) source.close();
    };
  }, []);

  const liveActivitySub = realFeedReady
    ? 'last 14 events · live stream'
    : (streamConnected ? 'last 14 events · awaiting first live activity' : 'connecting to live stream');
  const liveActivityTone = realFeedReady ? 'ok' : (streamConnected ? 'acc' : 'warn');
  const liveActivityBadge = realFeedReady ? 'REAL' : (streamConnected ? 'CONNECTED' : 'SYNCING');

  return (
    <div className="hc-flex-col" style={{ gap: 16 }}>
      <div className="hc-grid hc-grid-4">
        <Stat label="Agents" value={data.agents.filter(a=>a.status==='active').length + ' / ' + data.agents.length} delta="+2" deltaDir="up" icon="agents" spark={[2,3,3,4,4,4,5,4,4,5,5,5]} />
        <Stat label="Sessions" value={data.sessions.filter(s=>s.status==='active').length} delta="+1" deltaDir="up" icon="sessions" spark={[1,2,2,3,4,3,3,4,4,5,4,4]} />
        <Stat label="Tokens today" value={(data.usage.today.tokens/1000).toFixed(1) + 'k'} delta="+24%" deltaDir="up" icon="zap" spark={data.usage.hourly.slice(-12)} />
        <Stat label="Cost today" value={'$' + data.usage.today.cost.toFixed(2)} delta={`${Math.round(data.usage.today.cost/data.usage.today.budget*100)}% of budget`} deltaDir="" icon="usage" spark={data.usage.hourly.slice(-12).map(v => v * 0.008)} />
      </div>

      <div className="hc-grid hc-grid-2-1">
        <Panel title="Live activity" icon="activity" sub={liveActivitySub}
          actions={[<span key="r" className={`hc-tag ${liveActivityTone}`}><Icon name="radio" size={10} />&nbsp;{liveActivityBadge}</span>,
                    <button key="b" className="hc-btn sm" onClick={() => setActive('activity')}>Open timeline</button>]}>
          <div className="hc-feed" style={{ margin: -14 }}>
            {liveEvents.length
              ? liveEvents.map((e, i) => <FeedItem key={(e._id || i) + '_' + i} event={e} isNew={newIds.has(e._id)} />)
              : <div className="hc-empty"><Icon name="activity" size={32} /><div className="msg">Waiting for real events…</div></div>}
          </div>
        </Panel>

        <div className="hc-flex-col" style={{ gap: 16 }}>
          <Panel title="Pending approvals" icon="alert" sub={data.approvals.length + ' awaiting'}
            actions={<button className="hc-btn sm">Review all</button>}>
            <div className="hc-flex-col" style={{ gap: 10 }}>
              {data.approvals.map(a => (
                <div key={a.id} style={{ padding: 10, border: '1px solid var(--border-subtle)', borderRadius: 8, background: 'var(--bg-surface)' }}>
                  <div className="hc-flex" style={{ justifyContent: 'space-between' }}>
                    <span className="hc-text-primary" style={{ fontSize: 13, fontWeight: 500 }}>{a.title}</span>
                    <Tag tone={a.risk === 'high' ? 'err' : a.risk === 'medium' ? 'warn' : ''}>{a.risk}</Tag>
                  </div>
                  <div className="hc-mono hc-muted" style={{ fontSize: 11, marginTop: 4 }}>{a.kind} {'\u00b7'} {a.source} {'\u00b7'} {a.at}</div>
                  <div className="hc-text-sec" style={{ fontSize: 12, marginTop: 6 }}>{a.preview}</div>
                  <div className="hc-flex" style={{ marginTop: 8, gap: 6 }}>
                    <button className="hc-btn sm primary" onClick={() => postJson('/ops/approvals/resolve', { item_id: a.id, decision: 'approve' }).then((r) => { if (r) window.location.reload(); })}>Approve</button>
                    <button className="hc-btn sm danger" onClick={() => postJson('/ops/approvals/resolve', { item_id: a.id, decision: 'deny' }).then((r) => { if (r) window.location.reload(); })}>Deny</button>
                    <button className="hc-btn sm ghost">Inspect</button>
                  </div>
                </div>
              ))}
            </div>
          </Panel>

          <Panel title="System health" icon="heart" sub={data.systemHealth.env}>
            <dl className="hc-kv">
              <dt>service</dt><dd className="hc-mono">{data.systemHealth.version}</dd>
              <dt>bind</dt><dd className="hc-mono">{data.systemHealth.bind}</dd>
              <dt>auth</dt><dd className="hc-mono">{data.systemHealth.auth}</dd>
              <dt>uptime</dt><dd className="hc-mono">{data.systemHealth.uptime}</dd>
              <dt>runtime</dt><dd><Tag tone="ok">online</Tag></dd>
              <dt>event bus</dt><dd><Tag tone="ok">online</Tag></dd>
              <dt>cost breaker</dt><dd><Tag tone="ok">healthy</Tag></dd>
            </dl>
          </Panel>
        </div>
      </div>

      <div className="hc-grid hc-grid-2">
        <Panel title="Top agents" icon="agents" sub="by token burn today"
          actions={<button className="hc-btn sm ghost" onClick={() => setActive('agents')}>All agents <Icon name="arrow_up_right" size={12} /></button>}>
          <div style={{ margin: -14 }}>
            {data.agents.slice(0, 5).map(a => (
              <div key={a.id} className="hc-row">
                <div className="hc-agent-avatar">{a.avatar}<span className={`dot ${agentStatusTone(a.status)}`} /></div>
                <div className="hc-grow">
                  <div className="hc-text-primary" style={{ fontSize: 13, fontWeight: 500 }}>{a.id}</div>
                  <div className="hc-meta-line">{a.role} {'\u00b7'} {a.model} {'\u00b7'} last seen {a.lastSeen}</div>
                </div>
                <div style={{ width: 140 }}>
                  <div className="hc-flex" style={{ justifyContent: 'space-between', fontSize: 11 }}>
                    <span className="hc-muted hc-mono">{(a.tokens24h/1000).toFixed(1)}k tok</span>
                    <span className="hc-mono hc-text-sec">${a.cost24h.toFixed(2)}</span>
                  </div>
                  <Bar value={a.tokens24h} max={300000} tone={a.tokens24h > 200000 ? 'warn' : 'ok'} />
                </div>
              </div>
            ))}
          </div>
        </Panel>

        <Panel title="Cron schedule" icon="cron" sub="next 24h"
          actions={<button className="hc-btn sm ghost" onClick={() => setActive('cron')}>Open crons <Icon name="arrow_up_right" size={12} /></button>}>
          <div style={{ margin: -14 }}>
            {data.cron.map(c => (
              <div key={c.id} className="hc-row">
                <Icon name="clock" size={14} stroke={1.75} style={{ color: c.last === 'err' ? 'var(--danger)' : c.last === 'warn' ? 'var(--warning)' : 'var(--success)' }} />
                <div className="hc-grow">
                  <div className="hc-text-primary" style={{ fontSize: 13, fontWeight: 500 }}>{c.name}</div>
                  <div className="hc-meta-line">{c.schedule} {'\u00b7'} next {c.next}</div>
                </div>
                <Tag tone={c.last === 'err' ? 'err' : c.last === 'warn' ? 'warn' : 'ok'}>{c.last}</Tag>
                <button className="hc-btn sm ghost" onClick={() => postJson('/ops/cron/control', { job_id: c.id, action: c.enabled ? 'pause' : 'resume' }).then((r) => { if (r) window.location.reload(); })}><Icon name={c.enabled ? 'pause' : 'play'} size={12} /></button>
              </div>
            ))}
          </div>
        </Panel>
      </div>
    </div>
  );
}

function AgentsPage({ data }) {
  const [sel, setSel] = usA(data.agents[0]);
  return (
    <div className="hc-split">
      <Panel title="Agents" icon="agents" sub={`${data.agents.length} registered`}
        actions={<button className="hc-btn sm primary"><Icon name="plus" size={12} /> New</button>}
        className="hc-split-list">
        <div style={{ margin: -14 }}>
          {data.agents.map(a => (
            <div key={a.id} className={`hc-row ${sel?.id === a.id ? 'selected' : ''}`} onClick={() => setSel(a)}>
              <div className="hc-agent-avatar">{a.avatar}<span className={`dot ${agentStatusTone(a.status)}`} /></div>
              <div className="hc-grow">
                <div className="hc-text-primary" style={{ fontSize: 13, fontWeight: 500 }}>{a.id}</div>
                <div className="hc-meta-line">{a.role} {'\u00b7'} {a.model}</div>
              </div>
              <Tag tone={agentStatusTone(a.status)}>{a.status}</Tag>
            </div>
          ))}
        </div>
      </Panel>

      {sel && (
        <Panel title={sel.id} icon="agents" sub={sel.role}
          actions={[
            <button key="k" className="hc-btn sm danger"><Icon name="kill" size={12} /> Kill</button>,
            <button key="p" className="hc-btn sm"><Icon name="pause" size={12} /> Pause</button>,
            <button key="i" className="hc-btn sm primary"><Icon name="chat" size={12} /> Open chat</button>,
          ]}
          className="hc-split-detail">
          <div className="hc-grid hc-grid-2" style={{ marginBottom: 14 }}>
            <Stat label="Tokens 24h" value={(sel.tokens24h/1000).toFixed(1) + 'k'} spark={[8,12,10,16,22,18,24,30,28,34,40,38]} />
            <Stat label="Cost 24h" value={'$' + sel.cost24h.toFixed(2)} spark={[1,1,2,1,2,2,3,2,3,3,4,4]} />
          </div>
          <dl className="hc-kv">
            <dt>status</dt><dd><Tag tone={agentStatusTone(sel.status)}>{sel.status}</Tag></dd>
            <dt>model</dt><dd className="hc-mono">{sel.model}</dd>
            <dt>role</dt><dd>{sel.role}</dd>
            <dt>sessions</dt><dd className="hc-mono">{sel.sessions}</dd>
            <dt>last seen</dt><dd className="hc-mono">{sel.lastSeen}</dd>
            <dt>created</dt><dd className="hc-mono">2026-01-14 06:22 BRT</dd>
            <dt>capabilities</dt><dd><Tag>tools</Tag> <Tag>memory</Tag> <Tag>mcp</Tag> {sel.role==='orchestrator' && <Tag tone="accent">subagents</Tag>}</dd>
          </dl>
          <div className="hc-divider" />
          <div className="hc-panel-head" style={{ padding: 0, marginBottom: 10, borderBottom: 'none' }}>
            <h2><Icon name="sessions" size={14} /> Recent sessions</h2>
          </div>
          <table className="hc-tbl">
            <thead><tr><th>Session</th><th>Title</th><th>Msgs</th><th className="col-r">Tokens</th><th>Status</th></tr></thead>
            <tbody>
              {data.sessions.filter(s => s.agent === sel.id).concat(data.sessions.slice(0, 2)).slice(0, 5).map((s, i) => (
                <tr key={s.id + i}>
                  <td className="mono">{s.id}</td>
                  <td className="hc-text-primary">{s.title}</td>
                  <td className="mono">{s.msgs}</td>
                  <td className="mono col-r">{s.tokens.toLocaleString()}</td>
                  <td><Tag tone={s.status === 'active' ? 'ok' : s.status === 'paused' ? 'warn' : ''}>{s.status}</Tag></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Panel>
      )}
    </div>
  );
}

function SessionsPage({ data }) {
  const [sel, setSel] = usA(data.sessions[0]);
  return (
    <div className="hc-split">
      <Panel title="Sessions" icon="sessions" sub={`${data.sessions.length} total`} className="hc-split-list">
        <div style={{ margin: -14 }}>
          {data.sessions.map(s => (
            <div key={s.id} className={`hc-row ${sel?.id === s.id ? 'selected' : ''}`} onClick={() => setSel(s)}>
              <div className="hc-agent-avatar"><Icon name="sessions" size={13} /><span className={`dot ${s.status === 'active' ? 'ok' : s.status === 'paused' ? 'warn' : ''}`} /></div>
              <div className="hc-grow" style={{ minWidth: 0 }}>
                <div className="hc-text-primary" style={{ fontSize: 13, fontWeight: 500, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.title}</div>
                <div className="hc-meta-line">{s.id} {'\u00b7'} {s.agent} {'\u00b7'} {s.platform}</div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <div className="hc-mono" style={{ fontSize: 11, color: 'var(--text-secondary)' }}>{s.msgs} msgs</div>
                <div className="hc-mono hc-muted" style={{ fontSize: 10 }}>{s.started}</div>
              </div>
            </div>
          ))}
        </div>
      </Panel>

      {sel && <ChatPanel sel={sel} data={data} />}
    </div>
  );
}

function ChatPanel({ sel, data }) {
  return (
    <Panel title="Conversar" icon="chat" sub={sel.id}
      actions={[
        <Tag key="st" tone={sel.status==='active'?'ok':sel.status==='paused'?'warn':''}>{sel.status}</Tag>,
        <button key="i" className="hc-btn sm ghost"><Icon name="eye" size={12} /> Inspect</button>,
        <button key="p" className="hc-btn sm"><Icon name={sel.status==='paused'?'play':'pause'} size={12} /> {sel.status==='paused'?'Resume':'Pause'}</button>,
      ]}
      foot={<>
        <span className="hc-mono">session {sel.id} {'\u00b7'} {sel.msgs} messages {'\u00b7'} {sel.tokens.toLocaleString()} tokens</span>
        <span><Tag tone="ok"><Icon name="radio" size={9} />&nbsp;streaming</Tag></span>
      </>}
      className="hc-split-detail">
      <div className="hc-chat">
        <div className="hc-chat-msgs">
          {data.transcript.map((m, i) => (
            <div key={i} className={`hc-msg ${m.role}`}>
              <div className="hc-msg-avatar">{m.role === 'user' ? 'OP' : 'HP'}</div>
              <div className="hc-msg-body">
                <div className="hc-msg-head">
                  <span className="name">{m.name}</span>
                  <span className="time">{m.time}</span>
                </div>
                <div className="hc-msg-content">{m.content}</div>
                {m.tool && (
                  <div className="hc-msg-tool"><span className="tk">{m.tool.name}</span> <span className="hc-muted">{'\u00b7'}</span> {m.tool.args}</div>
                )}
              </div>
            </div>
          ))}
          <div className="hc-msg agent">
            <div className="hc-msg-avatar">HP</div>
            <div className="hc-msg-body">
              <div className="hc-msg-head">
                <span className="name">hermes-primary</span>
                <span className="time">typing{'\u2026'}</span>
              </div>
              <div className="hc-msg-content hc-muted">
                <span className="hc-term-cursor" style={{ background: 'var(--accent)' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </Panel>
  );
}

function ActivityPage({ data }) {
  const [filter, setFilter] = usA('all');
  const [selected, setSelected] = usA(null);
  const filtered = data.events.filter(e => filter === 'all' || (filter === 'errors' && e.tone === 'err') || (filter === 'approvals' && e.kind.startsWith('approval')));
  return (
    <div className="hc-split">
      <Panel title="Event timeline" icon="activity" sub={`${filtered.length} events`}
        actions={[
          <div key="seg" className="hc-tweak-seg" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
            {['all','errors','approvals'].map(f => (
              <button key={f} className={filter === f ? 'active' : ''} onClick={() => setFilter(f)}>{f}</button>
            ))}
          </div>,
          <button key="r" className="hc-btn sm ghost"><Icon name="download" size={12} /></button>,
        ]}
        className="hc-split-list">
        <div className="hc-feed" style={{ margin: -14 }}>
          {filtered.map((e, i) => (
            <div key={i} onClick={() => setSelected(e)} style={{ cursor: 'pointer', background: selected === e ? 'var(--bg-hover)' : '' }}>
              <FeedItem event={e} />
            </div>
          ))}
        </div>
      </Panel>

      <Panel title="Event detail" icon="eye" sub={selected ? selected.kind : 'select an event'} className="hc-split-detail">
        {selected ? (
          <>
            <div className="hc-flex" style={{ gap: 8, marginBottom: 12 }}>
              <Tag tone={selected.tone}>{selected.kind}</Tag>
              <span className="hc-mono hc-muted" style={{ fontSize: 12 }}>{selected.t} BRT {'\u00b7'} {selected.source}</span>
            </div>
            <h3 style={{ margin: 0, fontSize: 15 }}>{selected.title}</h3>
            <p className="hc-text-sec" style={{ marginTop: 6 }}>{selected.detail}</p>
            <div className="hc-divider" />
            <pre className="hc-pre">{JSON.stringify({ kind: selected.kind, source: selected.source, recorded_at: `2026-04-17T${selected.t}-03:00`, timezone: 'America/Sao_Paulo', payload: { title: selected.title, detail: selected.detail } }, null, 2)}</pre>
          </>
        ) : (
          <div className="hc-empty"><Icon name="activity" size={32} /><div className="msg">Pick an event from the timeline.</div></div>
        )}
      </Panel>
    </div>
  );
}

window.Dashboard = Dashboard;
window.AgentsPage = AgentsPage;
window.SessionsPage = SessionsPage;
window.ActivityPage = ActivityPage;
