/* Hermes Command Center — Layout (Sidebar + Topbar) */
const NAV = [
  { sector: 'Core ops', items: [
    { key: 'dashboard', icon: 'dashboard', label: 'Dashboard', badge: null },
    { key: 'activity',  icon: 'activity',  label: 'Atividade', badge: '12' },
    { key: 'usage',     icon: 'usage',     label: 'Usage',     badge: null },
    { key: 'agents',    icon: 'agents',    label: 'Agentes',   badge: '6' },
    { key: 'chat',      icon: 'chat',      label: 'Conversar', badge: null },
    { key: 'sessions',  icon: 'sessions',  label: 'Sessões',   badge: '3' },
    { key: 'cron',      icon: 'cron',      label: 'Crons',     badge: '!' },
    { key: 'doctor',    icon: 'doctor',    label: 'Doctor',    badge: null },
    { key: 'logs',      icon: 'logs',      label: 'Logs',      badge: null },
  ]},
  { sector: 'Workspace', items: [
    { key: 'memory',    icon: 'memory',    label: 'Memória',   badge: null },
    { key: 'documents', icon: 'documents', label: 'Documentos',badge: null },
    { key: 'channels',  icon: 'channels',  label: 'Canais',    badge: null },
    { key: 'skill',     icon: 'skill',     label: 'Skills',    badge: null },
  ]},
  { sector: 'Orquestração', items: [
    { key: 'orchestration', icon: 'orchestration', label: 'Orquestração', badge: null },
  ]},
  { sector: 'Advanced', items: [
    { key: 'terminal',  icon: 'terminal',  label: 'Terminal',  badge: null },
  ]},
];

const PAGE_META = {
  dashboard: { title: 'Dashboard',   sub: 'Control plane overview' },
  activity:  { title: 'Atividade',   sub: 'Live event timeline' },
  usage:     { title: 'Usage',       sub: 'Tokens \u00b7 cost \u00b7 burn rate' },
  agents:    { title: 'Agentes',     sub: 'Multi-agent supervis\u00e3o' },
  chat:      { title: 'Conversar',   sub: 'Live agent transcript' },
  sessions:  { title: 'Sess\u00f5es',     sub: 'Session history and detail' },
  tasks:     { title: 'Tarefas',     sub: 'Backlog operacional' },
  cron:      { title: 'Crons',       sub: 'Scheduled jobs & history' },
  calendar:  { title: 'Calend\u00e1rio',  sub: '' },
  integrations:{ title: 'Integra\u00e7\u00f5es', sub: '' },
  skill:     { title: 'Skills',      sub: 'Agent skill catalog' },
  memory:    { title: 'Mem\u00f3ria',     sub: 'Scoped memory entries' },
  documents: { title: 'Documentos',  sub: 'Workspace files' },
  database:  { title: 'Database',    sub: '' },
  apis:      { title: "API's",       sub: '' },
  channels:  { title: 'Canais',      sub: 'Gateway + channel status' },
  hooks:     { title: 'Seguran\u00e7a',   sub: 'Security hooks' },
  preferences:{ title: 'Prefer\u00eancias', sub: 'Profiles and rules' },
  doctor:    { title: 'Doctor',      sub: 'Operational diagnostics' },
  terminal:  { title: 'Terminal',    sub: 'Risk posture \u00b7 interactive shell' },
  logs:      { title: 'Logs',        sub: 'Structured event log' },
  tailscale: { title: 'Tailscale',   sub: 'Network posture' },
  config:    { title: 'Config',      sub: '' },
  orchestration: { title: 'Orquestração', sub: 'Delegações Hermes \u2194 OpenClaw \u00b7 timeline ao vivo' },
};

function Sidebar({ active, onNav, collapsed, setCollapsed, mobileOpen }) {
  return (
    <aside id="hc-sidebar-nav" className={`hc-sidebar${mobileOpen ? ' mobile-open' : ''}`}>
      <div className="hc-brand">
        <div className="hc-brand-mark" title="Hermes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 20L12 4l8 16M7 14h10" />
          </svg>
        </div>
        <div className="hc-brand-text">
          <span className="n">Hermes</span>
          <span className="t">command{'\u00b7'}center</span>
        </div>
      </div>

      <div className="hc-sidebar-scroll">
        {NAV.map(sector => (
          <div key={sector.sector} className="hc-nav-sector">
            <h3>{sector.sector}</h3>
            {sector.items.map(item => (
              <button
                key={item.key}
                className={`hc-nav-item ${active === item.key ? 'active' : ''}`}
                onClick={() => onNav(item.key)}
                title={item.label}
              >
                <Icon name={item.icon} size={16} stroke={1.75} />
                <span className="label">{item.label}</span>
                {item.badge && <span className="badge">{item.badge}</span>}
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className="hc-sidebar-footer">
        <div className="hc-operator">
          <div className="hc-operator-avatar">OP</div>
          <div className="hc-operator-text">
            <div className="n">operator</div>
            <div className="t">passkey {'\u00b7'} loopback</div>
          </div>
        </div>
        <button className="hc-collapse-btn" onClick={() => setCollapsed(!collapsed)} title={collapsed ? 'Expand' : 'Collapse'}>
          <Icon name={collapsed ? 'chevronRight' : 'chevronLeft'} size={14} stroke={2} />
        </button>
      </div>
    </aside>
  );
}

function Topbar({ active, onRefresh, gatewayOnline, setGatewayOnline, clock, onToggleMobile, mobileOpen }) {
  const meta = PAGE_META[active] || {};
  return (
    <header className="hc-topbar">
      <button
        className="hc-mobile-toggle"
        onClick={onToggleMobile}
        aria-label="Menu"
        aria-expanded={mobileOpen ? 'true' : 'false'}
        aria-controls="hc-sidebar-nav"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
      <div className="hc-breadcrumb">
        <span>Hermes</span>
        <span className="sep">/</span>
        <span className="cur">{meta.title}</span>
      </div>

      <div className="hc-topbar-spacer" />

      <div className="hc-search">
        <Icon name="search" size={14} stroke={2} />
        <input placeholder="Search across agents, sessions, files\u2026" />
        <kbd>{'\u2318'}K</kbd>
      </div>

      <span className={`hc-status-pill ${gatewayOnline ? 'online' : 'offline'}`}>
        <span className="dot" />
        {gatewayOnline ? 'Gateway online' : 'Gateway offline'}
      </span>

      <span className="hc-mono hc-muted" style={{fontSize:12}}>{clock}</span>

      <button className="hc-btn ghost" onClick={onRefresh} title="Refresh">
        <Icon name="refresh" size={14} stroke={2} />
      </button>
      <button
        className={`hc-btn ${gatewayOnline ? 'danger' : 'primary'}`}
        onClick={() => {
          const action = gatewayOnline ? 'kill' : 'start';
          fetch('/ops/gateway-runtime', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ action }),
          })
            .then(async (r) => {
              if (!r.ok) return null;
              try {
                return await r.json();
              } catch {
                return null;
              }
            })
            .then((payload) => {
              const runtime = payload?.data?.runtime || payload?.runtime || null;
              if (runtime && typeof runtime.running === 'boolean') {
                setGatewayOnline(runtime.running);
              }
            })
            .catch(() => {});
        }}
      >
        <Icon name={gatewayOnline ? 'kill' : 'play'} size={14} stroke={2} />
        {gatewayOnline ? 'Kill gateway' : 'Start gateway'}
      </button>
    </header>
  );
}

window.Sidebar = Sidebar;
window.Topbar = Topbar;
window.PAGE_META = PAGE_META;
window.NAV = NAV;
