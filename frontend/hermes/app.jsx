/* Hermes Command Center — App root, router, Tweaks panel */
const { useState: usApp, useEffect: ueApp, useMemo: umApp } = React;

const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "theme": "premium",
  "collapsed": false,
  "fontMono": "geist"
}/*EDITMODE-END*/;

function App() {
  const saved = (() => { try { return JSON.parse(localStorage.getItem('hc_state') || '{}'); } catch { return {}; } })();
  const [active, setActive] = usApp(saved.active || 'dashboard');
  const [theme, setTheme] = usApp(TWEAK_DEFAULTS.theme);
  const [collapsed, setCollapsed] = usApp(TWEAK_DEFAULTS.collapsed);
  const [gatewayOnline, setGatewayOnline] = usApp(true);
  const [clock, setClock] = usApp('14:32:18 UTC');
  const [tweaksOn, setTweaksOn] = usApp(false);

  ueApp(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);
  ueApp(() => { localStorage.setItem('hc_state', JSON.stringify({ active })); }, [active]);

  ueApp(() => {
    const t = setInterval(() => {
      const d = new Date();
      setClock(`${String(d.getUTCHours()).padStart(2,'0')}:${String(d.getUTCMinutes()).padStart(2,'0')}:${String(d.getUTCSeconds()).padStart(2,'0')} UTC`);
    }, 1000);
    return () => clearInterval(t);
  }, []);

  // Tweaks protocol
  ueApp(() => {
    function onMessage(e) {
      if (!e.data) return;
      if (e.data.type === '__activate_edit_mode') setTweaksOn(true);
      if (e.data.type === '__deactivate_edit_mode') setTweaksOn(false);
    }
    window.addEventListener('message', onMessage);
    window.parent.postMessage({ type: '__edit_mode_available' }, '*');
    return () => window.removeEventListener('message', onMessage);
  }, []);

  const persist = (edits) => {
    try { window.parent.postMessage({ type: '__edit_mode_set_keys', edits }, '*'); } catch {}
  };

  const data = window.HC_DATA;
  const meta = window.PAGE_META[active] || {};

  const Page = (() => {
    switch (active) {
      case 'dashboard': return <Dashboard data={data} setActive={setActive} />;
      case 'agents':    return <AgentsPage data={data} />;
      case 'sessions':  return <SessionsPage data={data} />;
      case 'chat':      return <SessionsPage data={data} />;
      case 'activity':  return <ActivityPage data={data} />;
      case 'usage':     return <UsagePage data={data} />;
      case 'cron':      return <CronPage data={data} />;
      case 'memory':    return <MemoryPage data={data} />;
      case 'documents': return <DocumentsPage data={data} />;
      case 'terminal':  return <TerminalPage data={data} />;
      case 'logs':      return <LogsPage data={data} />;
      case 'doctor':    return <DoctorPage data={data} />;
      case 'tasks':     return <PlaceholderPage title="Tarefas" hint="Backlog operacional · integra com issues do repo." />;
      case 'calendar':  return <PlaceholderPage title="Calendário" hint="Schedule view + agent time-blocking." />;
      case 'integrations': return <PlaceholderPage title="Integrações" hint="Monday · SALIC · Compras.gov." />;
      case 'skill':     return <PlaceholderPage title="Skills" hint="Skill catalog with HCC-design-advisor integration." />;
      case 'database':  return <PlaceholderPage title="Database" hint="SQLite inspector · migrations · retention." />;
      case 'apis':      return <PlaceholderPage title="APIs" hint="Outbound connector registry." />;
      case 'channels':  return <PlaceholderPage title="Canais" hint="Gateway + channel transport state." />;
      case 'hooks':     return <PlaceholderPage title="Segurança Hooks" hint="Pre/post hook audit trail." />;
      case 'preferences': return <PlaceholderPage title="Preferências" hint="Profiles and rules." />;
      case 'tailscale': return <PlaceholderPage title="Tailscale" hint="Network posture and bind overrides." />;
      case 'config':    return <PlaceholderPage title="Config" hint="Hermes runtime configuration." />;
      default:          return <Dashboard data={data} setActive={setActive} />;
    }
  })();

  return (
    <div className="hc-shell" data-collapsed={collapsed ? 'true' : 'false'}>
      <Sidebar active={active} onNav={setActive} collapsed={collapsed} setCollapsed={setCollapsed} />
      <div className="hc-main">
        <Topbar active={active} onRefresh={() => {}} onNav={setActive}
          gatewayOnline={gatewayOnline} setGatewayOnline={setGatewayOnline} clock={clock} />
        <div className="hc-page">
          <div className="hc-page-header">
            <div className="hc-page-title">
              <h1>{meta.title}</h1>
              {meta.sub && <p>{meta.sub}</p>}
            </div>
            <div className="hc-page-actions">
              <Tag tone="accent"><Icon name="dot" size={10} />&nbsp;{theme === 'premium' ? 'Premium ops' : 'Mission control'}</Tag>
              <button className="hc-btn sm ghost"><Icon name="filter" size={12} /> Filter</button>
              <button className="hc-btn sm"><Icon name="download" size={12} /> Export</button>
            </div>
          </div>
          {Page}
        </div>
      </div>

      {tweaksOn && (
        <div className="hc-tweaks">
          <div className="hc-tweaks-head">
            <span><Icon name="config" size={12} />&nbsp;&nbsp;Tweaks</span>
            <button className="hc-btn sm ghost" onClick={() => setTweaksOn(false)}><Icon name="x" size={12} /></button>
          </div>
          <div className="hc-tweaks-body">
            <div className="hc-tweak-row">
              <label>Visual direction</label>
              <div className="hc-tweak-seg">
                <button className={theme === 'premium' ? 'active' : ''} onClick={() => { setTheme('premium'); persist({ theme: 'premium' }); }}>Premium Ops</button>
                <button className={theme === 'mission' ? 'active' : ''} onClick={() => { setTheme('mission'); persist({ theme: 'mission' }); }}>Mission Control</button>
              </div>
            </div>
            <div className="hc-tweak-row">
              <label>Sidebar</label>
              <div className="hc-tweak-seg">
                <button className={!collapsed ? 'active' : ''} onClick={() => { setCollapsed(false); persist({ collapsed: false }); }}>Expanded</button>
                <button className={collapsed ? 'active' : ''} onClick={() => { setCollapsed(true); persist({ collapsed: true }); }}>Collapsed</button>
              </div>
            </div>
            <div className="hc-tweak-row">
              <label>Quick jump</label>
              <div className="hc-tweak-seg" style={{ gridTemplateColumns: '1fr 1fr 1fr' }}>
                <button onClick={() => setActive('dashboard')}>Dash</button>
                <button onClick={() => setActive('agents')}>Agents</button>
                <button onClick={() => setActive('terminal')}>Term</button>
              </div>
            </div>
            <div className="hc-text-sec" style={{ fontSize: 11, marginTop: 4, lineHeight: 1.5 }}>
              Toggle themes to compare <span className="hc-text-primary">Premium Ops</span> (Linear/Vercel) vs <span className="hc-text-primary">Mission Control</span> (phosphor + amber + alert red).
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
