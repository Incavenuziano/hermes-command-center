/* Hermes Command Center — App root, router, Tweaks panel */
const { useState: usApp, useEffect: ueApp } = React;

const TWEAK_DEFAULTS = {
  "theme": "premium",
  "collapsed": false,
  "fontMono": "geist"
};

const { formatSaoPauloTime } = window.HC_TIME;

function App() {
  const saved = (() => { try { return JSON.parse(localStorage.getItem('hc_state') || '{}'); } catch { return {}; } })();
  const [active, setActive] = usApp(saved.active || 'dashboard');
  const [theme, setTheme] = usApp(saved.theme || TWEAK_DEFAULTS.theme);
  const [collapsed, setCollapsed] = usApp(TWEAK_DEFAULTS.collapsed);
  const [gatewayOnline, setGatewayOnline] = usApp(true);
  const [clock, setClock] = usApp(formatSaoPauloTime());
  const [tweaksOn, setTweaksOn] = usApp(false);
  const [mobileMenu, setMobileMenu] = usApp(false);

  ueApp(() => { document.documentElement.setAttribute('data-theme', theme); }, [theme]);
  ueApp(() => { localStorage.setItem('hc_state', JSON.stringify({ active, theme })); }, [active, theme]);

  ueApp(() => {
    const t = setInterval(() => {
      setClock(formatSaoPauloTime());
    }, 1000);
    return () => clearInterval(t);
  }, []);

  ueApp(() => {
    fetch('/health/live').then(r => {
      if (r.ok) setGatewayOnline(true);
      else setGatewayOnline(false);
    }).catch(() => {});
  }, []);

  ueApp(() => {
    if (!mobileMenu) return undefined;

    const media = window.matchMedia('(max-width: 640px)');
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleViewportChange = (event) => {
      if (!event.matches) {
        setMobileMenu(false);
      }
    };

    const handleKeyDown = (event) => {
      if (event.key === 'Escape') {
        setMobileMenu(false);
      }
    };

    if (typeof media.addEventListener === 'function') {
      media.addEventListener('change', handleViewportChange);
    } else if (typeof media.addListener === 'function') {
      media.addListener(handleViewportChange);
    }
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      if (typeof media.removeEventListener === 'function') {
        media.removeEventListener('change', handleViewportChange);
      } else if (typeof media.removeListener === 'function') {
        media.removeListener(handleViewportChange);
      }
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [mobileMenu]);

  const handleMobileNav = (next) => {
    setActive(next);
    setMobileMenu(false);
  };

  const handleToggleMobile = () => {
    setMobileMenu((open) => !open);
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
      case 'tasks':     return <PlaceholderPage title="Tarefas" hint="Backlog operacional \u00b7 integra com issues do repo." />;
      case 'calendar':  return <PlaceholderPage title="Calend\u00e1rio" hint="Schedule view + agent time-blocking." />;
      case 'integrations': return <PlaceholderPage title="Integra\u00e7\u00f5es" hint="Monday \u00b7 SALIC \u00b7 Compras.gov." />;
      case 'skill':     return <PlaceholderPage title="Skills" hint="Skill catalog with HCC-design-advisor integration." />;
      case 'database':  return <PlaceholderPage title="Database" hint="SQLite inspector \u00b7 migrations \u00b7 retention." />;
      case 'apis':      return <PlaceholderPage title="APIs" hint="Outbound connector registry." />;
      case 'channels':  return <PlaceholderPage title="Canais" hint="Gateway + channel transport state." />;
      case 'hooks':     return <PlaceholderPage title="Seguran\u00e7a Hooks" hint="Pre/post hook audit trail." />;
      case 'preferences': return <PlaceholderPage title="Prefer\u00eancias" hint="Profiles and rules." />;
      case 'tailscale': return <PlaceholderPage title="Tailscale" hint="Network posture and bind overrides." />;
      case 'config':    return <PlaceholderPage title="Config" hint="Hermes runtime configuration." />;
      case 'orchestration': return <OrchestrationPage />;
      default:          return <Dashboard data={data} setActive={setActive} />;
    }
  })();

  return (
    <div className="hc-shell" data-collapsed={collapsed ? 'true' : 'false'}>
      <div
        className={`hc-sidebar-backdrop${mobileMenu ? ' visible' : ''}`}
        onClick={() => setMobileMenu(false)}
        aria-hidden={mobileMenu ? 'false' : 'true'}
      />
      <Sidebar
        active={active}
        onNav={handleMobileNav}
        collapsed={collapsed}
        setCollapsed={setCollapsed}
        mobileOpen={mobileMenu}
      />
      <div className="hc-main">
        <Topbar active={active} onRefresh={() => window.location.reload()}
          gatewayOnline={gatewayOnline} setGatewayOnline={setGatewayOnline} clock={clock}
          onToggleMobile={handleToggleMobile} mobileOpen={mobileMenu} />
        <div className="hc-page">
          <div className="hc-page-header">
            <div className="hc-page-title">
              <h1>{meta.title}</h1>
              {meta.sub && <p>{meta.sub}</p>}
            </div>
            <div className="hc-page-actions">
              <button className="hc-btn sm ghost" onClick={() => setTweaksOn(!tweaksOn)} title="Toggle tweaks panel">
                <Icon name="config" size={12} /> Tweaks
              </button>
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
                <button className={theme === 'premium' ? 'active' : ''} onClick={() => setTheme('premium')}>Premium Ops</button>
                <button className={theme === 'mission' ? 'active' : ''} onClick={() => setTheme('mission')}>Mission Control</button>
              </div>
            </div>
            <div className="hc-tweak-row">
              <label>Sidebar</label>
              <div className="hc-tweak-seg">
                <button className={!collapsed ? 'active' : ''} onClick={() => setCollapsed(false)}>Expanded</button>
                <button className={collapsed ? 'active' : ''} onClick={() => setCollapsed(true)}>Collapsed</button>
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
