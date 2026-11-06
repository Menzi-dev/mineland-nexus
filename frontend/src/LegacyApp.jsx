import React, { useEffect, useState } from 'react';
import { Activity, ArrowUpRight, BarChart3, ChevronRight, Database, Leaf, MapPinned, Menu, Radio, ShieldAlert, UploadCloud } from 'lucide-react';
import { getDashboardData } from './services/api';
import Map from './components/Map';
import Upload from './components/Upload';
import SuitabilityDashboard from './components/SuitabilityDashboard';

function App() {
  const [apiState, setApiState] = useState({ loading: true, error: null, data: null });
  const [activeView, setActiveView] = useState('overview');
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    getDashboardData()
      .then(([health, cached, suitability, recommendation]) => setApiState({ loading: false, error: null, data: { health: health.data, cached: cached.data, suitability: suitability.data, recommendation: recommendation.data } }))
      .catch((error) => setApiState({ loading: false, error: error.message, data: null }));
  }, []);

  const data = apiState.data;
  const scores = data?.suitability?.all_scores_sorted || data?.suitability?.scores || [];
  const bestUse = data?.recommendation?.recommendation || 'Analysis pending';
  const bestScore = data?.recommendation?.recommendation_score;
  const miningFeatures = data?.cached?.data?.mining?.data?.features || data?.cached?.mining?.data?.features || data?.cached?.mining?.features || [];
  const ndvi = data?.cached?.data?.ndvi?.statistics?.mean ?? data?.cached?.ndvi?.statistics?.mean;
  const solar = data?.cached?.data?.solar?.solar_suitability_score ?? data?.cached?.solar?.solar_suitability_score;
  const navItems = [{ id: 'overview', label: 'Overview', icon: BarChart3 }, { id: 'map', label: 'Mine map', icon: MapPinned }, { id: 'land', label: 'Land intelligence', icon: Leaf }, { id: 'uploads', label: 'Media & uploads', icon: UploadCloud }];
  const metricCards = [
    { label: 'Mapped mining areas', value: apiState.loading ? '—' : miningFeatures.length, detail: 'Northern Cape study area', icon: MapPinned, tone: 'green' },
    { label: 'Land recovery signal', value: ndvi == null ? '—' : `${Math.round(Number(ndvi) * 100)}%`, detail: 'Latest NDVI mean', icon: Leaf, tone: 'sage' },
    { label: 'Solar suitability', value: solar == null ? '—' : `${Math.round(Number(solar))}%`, detail: 'NASA POWER and terrain', icon: Activity, tone: 'gold' },
    { label: 'Live data status', value: apiState.loading ? 'Syncing' : apiState.error ? 'Offline' : 'Connected', detail: data?.health?.timestamp ? new Date(data.health.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Backend health', icon: Radio, tone: apiState.error ? 'red' : 'green' },
  ];
  const navigate = (view) => { setActiveView(view); setSidebarOpen(false); };

  return <div className="min-h-screen bg-[#f4f6f2] text-[#18211d]">
    <aside className={`app-sidebar ${sidebarOpen ? 'is-open' : ''}`}><div className="brand"><span className="brand-mark"><Database size={18} /></span><span>MineLife <strong>AI</strong></span></div><div className="eyebrow">LAND INTELLIGENCE PLATFORM</div><nav className="side-nav" aria-label="Primary navigation">{navItems.map(({ id, label, icon: Icon }) => <button key={id} className={activeView === id ? 'active' : ''} onClick={() => navigate(id)}><Icon size={18} /><span>{label}</span>{activeView === id && <ChevronRight size={15} />}</button>)}</nav><div className="sidebar-foot"><span className="status-dot" /> <span>{apiState.error ? 'Backend unavailable' : 'Real data connection'}</span></div></aside>
    {sidebarOpen && <button className="scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
    <main className="app-main"><header className="topbar"><button className="icon-button menu-button" onClick={() => setSidebarOpen(true)} aria-label="Open navigation"><Menu size={20} /></button><div className="topbar-context"><span className="kicker">NORTHERN CAPE / NABABEEP</span><span className="topbar-title">Operational view</span></div><button className="upload-button" onClick={() => navigate('uploads')}><UploadCloud size={17} /> Add assessment</button></header>
      {activeView === 'overview' && <section className="page-content"><div className="page-intro"><div><div className="kicker">MINE RESPONSIBILITY, MADE VISIBLE</div><h1>Monitor. Protect. Rehabilitate.</h1><p>Live environmental and land-use intelligence for the post-mining landscape.</p></div><div className="data-badge"><span className="status-dot" /> {apiState.loading ? 'Syncing sources' : apiState.error ? 'Connection issue' : 'Connected to live services'}</div></div>{apiState.error && <div className="notice error"><ShieldAlert size={18} /><span>Live services could not be reached. Start the FastAPI service to view current data.</span></div>}<div className="metric-grid">{metricCards.map(({ label, value, detail, icon: Icon, tone }) => <div className={`metric-card tone-${tone}`} key={label}><div className="metric-icon"><Icon size={18} /></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-detail">{detail}</div></div>)}</div><div className="overview-grid"><div className="panel map-panel"><div className="panel-heading"><div><div className="kicker">GEOSPATIAL VIEW</div><h2>Mining footprint</h2></div><button className="text-button" onClick={() => navigate('map')}>Open map <ArrowUpRight size={15} /></button></div><div className="mini-map"><Map compact /></div></div><div className="panel signal-panel"><div className="panel-heading"><div><div className="kicker">DECISION SUPPORT</div><h2>What the data says</h2></div><BarChart3 size={19} /></div><div className="recommendation"><span className="recommendation-tag">CURRENT RECOMMENDATION</span><strong>{bestUse}</strong><span className="recommendation-score">{bestScore == null ? '—' : `${Math.round(Number(bestScore))}%`} suitability</span><p>{data?.recommendation?.reason || 'Waiting for the comprehensive analysis response.'}</p></div><div className="signal-list">{scores.slice(0, 3).map((item, index) => <div className="signal-row" key={item.name || item.use || index}><span>{item.name || item.use || 'Land use score'}</span><strong>{item.score == null ? '—' : `${Math.round(Number(item.score))}%`}</strong></div>)}{!scores.length && <div className="empty-state">No suitability scores returned yet.</div>}</div></div></div></section>}
      {activeView === 'map' && <section className="page-content view-page"><div className="page-intro"><div><div className="kicker">GEOSPATIAL VIEW</div><h1>Mine map</h1><p>Explore real mining boundaries and energy infrastructure in the Northern Cape.</p></div></div><Map /></section>}
      {activeView === 'land' && <section className="page-content view-page"><div className="page-intro"><div><div className="kicker">LAND INTELLIGENCE</div><h1>Recovery and future use</h1><p>Transparent suitability analysis based on the connected environmental data sources.</p></div></div><SuitabilityDashboard /></section>}
      {activeView === 'uploads' && <section className="page-content view-page"><div className="page-intro"><div><div className="kicker">MEDIA EVIDENCE</div><h1>Mine assessments</h1><p>Upload field evidence to the connected FastAPI media store.</p></div></div><Upload /></section>}
    </main></div>;
}

export default App;
