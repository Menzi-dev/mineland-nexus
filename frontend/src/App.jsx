import React, { useEffect, useRef, useState } from 'react';
import { ArrowRight, ArrowUpRight, BookOpen, CheckCircle2, ChevronRight, Compass, Database, FileJson, FolderOpen, Globe2, Layers3, Leaf, Loader2, MapPin, Menu, Plus, Satellite, Search, ShieldCheck, TriangleAlert, UploadCloud, X } from 'lucide-react';
import { asset, client, errorText } from './services/national';
import LocationHelp from './components/LocationHelp';

const LazyMap = React.lazy(() => import('./components/AssessmentMap'));
const LazyReport = React.lazy(() => import('./components/AssessmentReport'));
function AssessmentMap(props) { return <React.Suspense fallback={<div className="assessment-map quiet-state">Loading map…</div>}><LazyMap {...props} /></React.Suspense>; }
function AssessmentReport(props) { return <React.Suspense fallback={<div className="quiet-state">Loading report…</div>}><LazyReport {...props} /></React.Suspense>; }

const running = (row) => row && ['queued', 'running'].includes(row.status);
const seasonNames = ['Jan–Mar', 'Feb–Apr', 'Mar–May', 'Apr–Jun', 'May–Jul', 'Jun–Aug', 'Jul–Sep', 'Aug–Oct', 'Sep–Nov', 'Oct–Dec'];

export default function App() {
  const [view, setView] = useState('home'), [sidebar, setSidebar] = useState(false), [health, setHealth] = useState('checking'), [capabilities, setCapabilities] = useState(null);
  const [assessments, setAssessments] = useState([]), [selected, setSelected] = useState(null), [error, setError] = useState('');
  const [boundary, setBoundary] = useState(null), [focus, setFocus] = useState(null), [confirmed, setConfirmed] = useState(false), [name, setName] = useState('');
  const [query, setQuery] = useState(''), [places, setPlaces] = useState([]), [searching, setSearching] = useState(false), [lat, setLat] = useState(''), [lon, setLon] = useState('');
  const [photo, setPhoto] = useState(null), [uploading, setUploading] = useState(false), [submitting, setSubmitting] = useState(false), [notes, setNotes] = useState('');
  const [propertyRef, setPropertyRef] = useState('');
  const [submissionIssues, setSubmissionIssues] = useState([]);
  const submissionFeedback = useRef(null);
  const [startYear, setStartYear] = useState(2018), [endYear, setEndYear] = useState(new Date().getFullYear() - 1), [month, setMonth] = useState(1), [horizon, setHorizon] = useState(5);
  const fileInput = useRef(null), geoInput = useRef(null);
  async function refresh() {
    const response = await client.get('/api/assessments');
    setAssessments(response.data.assessments);
  }
  useEffect(() => {
    Promise.all([client.get('/health'), client.get('/api/capabilities')]).then(([, c]) => { setHealth('connected'); setCapabilities(c.data); setEndYear(c.data.latest_complete_year); }).catch(() => setHealth('offline'));
    refresh().catch(() => {});
  }, []);
  useEffect(() => {
    if (!running(selected)) return;
    let cancelled = false, timer;
    async function poll() {
      try {
        const response = await client.get(`/api/assessments/${selected.id}`);
        if (cancelled) return;
        setSelected(response.data);
        if (!running(response.data)) { refresh().catch(() => {}); return; }
      } catch (e) { if (!cancelled) setError(`Progress update failed: ${errorText(e)}`); }
      if (!cancelled) timer = setTimeout(poll, 3000);
    }
    timer = setTimeout(poll, 1500);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [selected?.id, selected?.status]);
  const navigate = (next) => { setView(next); setSidebar(false); setError(''); };
  const begin = () => { setSelected(null); setName(''); setBoundary(null); setPhoto(null); setConfirmed(false); setNotes(''); setPropertyRef(''); setQuery(''); setPlaces([]); setLat(''); setLon(''); setFocus(null); setSubmissionIssues([]); navigate('new'); };
  const changeBoundary = (geometry) => { setBoundary(geometry); setConfirmed(false); };
  function reassess(row) { begin(); changeBoundary(row.site.geometry); setName(row.name); setPhoto(row.result?.photo || null); setNotes(row.user_notes || ''); setPropertyRef(row.property_reference || ''); setStartYear(row.options.start_year); setEndYear(row.options.end_year); setMonth(row.options.season_month); setHorizon(row.options.horizon); }
  async function openAssessment(id) {
    try { const response = await client.get(`/api/assessments/${id}`); setSelected(response.data); navigate('report'); }
    catch (e) { setError(errorText(e)); }
  }
  async function search(event) {
    event.preventDefault(); if (query.trim().length < 3) return;
    setSearching(true); setError('');
    try { const response = await client.get('/api/places', { params: { q: query.trim() } }); setPlaces(response.data.results); if (!response.data.results.length) setError('No results. Try a nearby town, coordinates, or locate the land directly on the map.'); }
    catch (e) { setError(errorText(e)); } finally { setSearching(false); }
  }
  function choosePlace(place) { setFocus({ lat: place.lat, lon: place.lon }); setLat(String(place.lat)); setLon(String(place.lon)); setPlaces([]); setQuery(place.name); changeBoundary(null); }
  function coordinates(event) {
    event.preventDefault(); const latitude = Number(lat), longitude = Number(lon);
    if (!lat.trim() || !lon.trim() || !Number.isFinite(latitude) || !Number.isFinite(longitude) || latitude < -35 || latitude > -22 || longitude < 16 || longitude > 33.1) { setError('Enter coordinates within South Africa. Latitude is negative, longitude is positive.'); return; }
    setFocus({ lat: latitude, lon: longitude }); changeBoundary(null); setError('');
  }
  async function upload(file) {
    if (!file) return;
    if (file.size > 10 * 1024 * 1024) { setError('Choose an image smaller than 10 MB.'); return; }
    setUploading(true); setError(''); setConfirmed(false); setBoundary(null); setFocus(null); setPhoto(null); setQuery(''); setPlaces([]); setLat(''); setLon('');
    const form = new FormData(); form.append('file', file);
    try { const response = await client.post('/api/photos', form); setPhoto(response.data); if (response.data.gps) choosePlace({ ...response.data.gps, name: 'Photo GPS location — confirm on map' }); }
    catch (e) { setError(errorText(e)); } finally { setUploading(false); }
  }
  async function importGeometry(file) {
    if (!file) return;
    try {
      if (file.size > 1024 * 1024) throw new Error('Use a GeoJSON file smaller than 1 MB.');
      let geometry = JSON.parse(await file.text());
      if (geometry.type === 'FeatureCollection') { if (geometry.features.length !== 1) throw new Error('Import one land boundary per assessment.'); geometry = geometry.features[0]; }
      if (geometry.type === 'Feature') geometry = geometry.geometry;
      if (!['Polygon', 'MultiPolygon'].includes(geometry?.type)) throw new Error('Use a GeoJSON Polygon or MultiPolygon in longitude, latitude.');
      const coords = geometry.type === 'Polygon' ? geometry.coordinates.flat() : geometry.coordinates.flat(2);
      if (coords.length < 4 || coords.some((p) => !Number.isFinite(p[0]) || !Number.isFinite(p[1]) || p[0] < 16 || p[0] > 33.1 || p[1] < -35 || p[1] > -22)) throw new Error('Boundary coordinates must be inside the South Africa region.');
      changeBoundary(geometry); setError('');
    } catch (e) { setError(e.message || 'Could not read the GeoJSON file.'); }
  }
  async function submit(event) {
    event.preventDefault();
    if (submitting) return;
    const issues = [];
    const first = Number(startYear), last = Number(endYear), latestYear = capabilities?.latest_complete_year || new Date().getFullYear() - 1;
    if (!name.trim()) issues.push('Enter an assessment name, for example "My farm assessment".');
    if (!boundary) issues.push('Select the land boundary on the map. Use "Draw boundary", "Select a small plot", or the 1 km² square. A photo or place search alone does not select the land area.');
    else if (!confirmed) issues.push('Tick "I have checked the map location and boundary" below the site notes. Changing the location or boundary clears this confirmation.');
    if (!Number.isInteger(first) || !Number.isInteger(last) || first < 2017 || last > latestYear || last - first < 4) issues.push(`Choose at least five complete years: first year 2017 or later, last year ${latestYear} or earlier. For example, ${latestYear - 4} to ${latestYear}.`);
    if (last + Number(horizon) + 9 > 2050) issues.push('Choose a shorter outlook horizon. The climate comparison must finish by 2050.');
    if (uploading) issues.push('Wait for the photograph upload to finish before starting.');
    if (issues.length) { setSubmissionIssues(issues); return; }
    setSubmissionIssues([]); setSubmitting(true); setError('');
    try {
      const response = await client.post('/api/assessments', { name: name.trim(), geometry: boundary, location_confirmed: confirmed,
        photo_id: photo?.id || null, start_year: Number(startYear), end_year: Number(endYear), season_month: Number(month), horizon: Number(horizon), notes, property_reference: propertyRef });
      setHealth('connected'); setSelected(response.data); navigate('report'); window.scrollTo({ top: 0, behavior: 'instant' }); refresh().catch(() => {});
    } catch (e) {
      setSubmissionIssues([e.response ? errorText(e) : 'The assessment service could not be reached. Your selections are saved in this form. Check that the local backend is running, then press Start assessment again.']);
    } finally { setSubmitting(false); }
  }
  useEffect(() => {
    if (submissionIssues.length) {
      submissionFeedback.current?.scrollIntoView({ behavior: 'smooth', block: 'center' });
      submissionFeedback.current?.focus({ preventScroll: true });
    }
  }, [submissionIssues]);
  const nav = [{ id: 'home', label: 'Overview', icon: Compass }, { id: 'new', label: 'Assess land', icon: MapPin }, { id: 'library', label: 'Assessment library', icon: FolderOpen }, { id: 'sources', label: 'Data & methodology', icon: Layers3 }];
  return <div className="national-app"><aside className={`app-sidebar ${sidebar ? 'is-open' : ''}`}><a href="#" className="brand" onClick={(e) => { e.preventDefault(); navigate('home'); }}><span className="brand-mark"><Layers3 size={21} /></span><span>MineLand<span className="brand-sub">NEXUS / LAND INTELLIGENCE</span></span></a><div className="sidebar-country"><Globe2 size={15} />South Africa<span className="country-dot" /></div><div className="eyebrow">WORKSPACE</div><nav className="side-nav" aria-label="Main navigation">{nav.map(({ id, label, icon: Icon }) => <button key={id} className={view === id || id === 'library' && view === 'report' ? 'active' : ''} onClick={() => navigate(id)}><Icon size={18} /><span>{label}</span><ChevronRight size={13} /></button>)}</nav><div className="sidebar-note"><Satellite size={27} /><strong>See change.<br />Understand possibility.</strong><p>Satellite evidence for the next chapter of South Africa’s land.</p><span>NO ON-SITE SENSORS REQUIRED</span></div><div className="sidebar-foot"><span className={`status-dot ${health}`} /><span>{health === 'connected' ? 'Local service connected' : health === 'checking' ? 'Checking local service' : 'Local service offline'}</span></div></aside>
    {sidebar && <button className="scrim" aria-label="Close navigation" onClick={() => setSidebar(false)} />}
    <main className="app-main"><header className="topbar"><button className="icon-button menu-button" aria-label="Open navigation" onClick={() => setSidebar(true)}><Menu size={20} /></button><div className="breadcrumbs"><span>Workspace</span><ChevronRight size={13} /><strong>{view === 'report' ? 'Assessment report' : nav.find((r) => r.id === view)?.label}</strong></div><div className="topbar-right"><span className="free-badge"><ShieldCheck size={14} />Open data. Clear evidence.</span><button className="primary-button small" onClick={begin}><Plus size={16} />New assessment</button></div></header>
    <div className="page-content">{error && <div role="alert" className="error-banner"><TriangleAlert size={18} /><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss error"><X size={17} /></button></div>}
    {health === 'offline' && <div className="error-banner"><TriangleAlert size={18} /><span>The backend is offline. Run <code>.\start-backend.ps1</code> from the project folder, then refresh.</span></div>}
    {view === 'home' && <><div className="page-intro"><div><div className="kicker">A NEW PERSPECTIVE ON LAND</div><h1>Every landscape<br />has a next chapter<span className="green-period">.</span></h1><p>Understand how land has changed. Explore what it could become.<br className="desktop-break" /> Grounded in satellite observations, across South Africa.</p><button className="primary-button hero-button" onClick={begin}>Explore a piece of land<ArrowRight size={17} /></button></div><div className="hero-orbit" aria-hidden="true"><div className="orbit orbit-a" /><div className="orbit orbit-b" /><div className="orbit orbit-c" /><div className="land-shape shape-1" /><div className="land-shape shape-2" /><div className="land-shape shape-3" /><div className="land-shape shape-4" /><div className="orbit-dot" /><div className="orbit-label"><Satellite size={17} /><span>OBSERVE → UNDERSTAND → PLAN</span></div><div className="hero-coordinate">22°S — 35°S / SOUTH AFRICA</div></div></div>
      <div className="intro-strip"><span><Globe2 size={17} />National coverage</span><span><Satellite size={17} />Real satellite observations</span><span><Database size={17} />Free public data sources</span><span><ShieldCheck size={17} />Uncertainty made visible</span></div>
      <div className="section-heading"><div><div className="kicker">FROM A PHOTO TO AN INFORMED PLAN</div><h2>One land. A fuller picture.</h2></div><span className="muted">Your evidence, in four steps</span></div><div className="journey-grid">{[
        { number: '01', icon: UploadCloud, title: 'Bring your land', text: 'Upload a photo, search for a place, or import a GeoJSON boundary.' },
        { number: '02', icon: MapPin, title: 'Put it on the map', text: 'Confirm the location and draw the exact area you want to assess.' },
        { number: '03', icon: Satellite, title: 'Read the changes', text: 'Compare clear satellite observations with weather and terrain evidence.' },
        { number: '04', icon: Leaf, title: 'Explore the future', text: 'Review tested baseline projections, climate pressures and possible pathways.' },
      ].map(({ number, icon: Icon, title, text }) => <article className="journey-card" key={number}><div><span>{number}</span><Icon size={22} /></div><h3>{title}</h3><p>{text}</p></article>)}</div>
      <div className="home-bottom"><section className="panel recent-panel"><div className="panel-heading"><div><div className="kicker">YOUR WORKSPACE</div><h2>Recent assessments</h2></div><button className="text-button" onClick={() => navigate('library')}>View library<ArrowUpRight size={15} /></button></div>{assessments.length ? <AssessmentList rows={assessments.slice(0, 3)} onOpen={openAssessment} /> : <div className="first-assessment"><span className="empty-icon"><MapPin size={25} /></span><h3>A fresh start for your next site</h3><p>Your assessments will appear here once you select and analyse land.</p><button className="secondary-button" onClick={begin}>Create your first assessment<ArrowRight size={15} /></button></div>}</section><section className="honesty-card"><ShieldCheck size={27} /><div className="kicker">BUILT AROUND EVIDENCE</div><h2>Useful answers.<br />Honest unknowns.</h2><p>A photo alone cannot prove where land is, when it was abandoned or why. We show what the evidence supports—and what needs a closer look.</p><button className="text-button" onClick={() => navigate('sources')}>Understand the methodology<ArrowUpRight size={16} /></button></section></div>
    </>}
    {view === 'new' && <><div className="compact-intro"><div className="kicker">SITE WORKSPACE</div><h1>Let’s understand your land.</h1><p>Start with a photo or a location. The boundary you confirm determines the assessment.</p></div><div className="setup-grid"><aside className="setup-sidebar"><section className="panel padded"><div className="step-title"><span>1</span><h2>Locate the land</h2></div><input type="file" accept="image/jpeg,image/png,image/webp" ref={fileInput} hidden onChange={(e) => { upload(e.target.files[0]); e.target.value = ''; }} /><button className={`photo-drop ${photo ? 'has-photo' : ''}`} onClick={() => fileInput.current.click()} disabled={uploading}>{photo ? <img src={asset(photo.preview_url)} alt="Uploaded site photograph" /> : uploading ? <Loader2 className="spin" size={27} /> : <UploadCloud size={28} />}<strong>{photo ? 'Replace photograph' : uploading ? 'Reading photograph…' : 'Upload a land photograph'}</strong><span>JPEG, PNG or WebP · up to 10 MB</span></button>{photo && <div className="photo-metadata"><CheckCircle2 size={16} /><div><strong>{photo.gps ? 'GPS metadata found' : 'No GPS metadata found'}</strong><p>{photo.gps ? 'Location moved to photo GPS. Confirm it on the map.' : 'Locate this land using search, coordinates or the map.'}</p>{photo.captured_at && <small>Photo metadata date: {photo.captured_at} · unverified</small>}</div></div>}<div className="form-divider">OR FIND A LOCATION</div><form onSubmit={search} className="search-form"><label htmlFor="place-search">Town, farm or place name</label><div className="input-action"><input id="place-search" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="e.g. Carletonville, Gauteng" /><button type="submit" disabled={searching || query.trim().length < 3} aria-label="Search South Africa">{searching ? <Loader2 className="spin" size={17} /> : <Search size={17} />}</button></div></form>{places.length > 0 && <div className="place-results">{places.map((p, i) => <button key={i} onClick={() => choosePlace(p)}><MapPin size={15} /><span>{p.name}</span></button>)}</div>}<details className="coordinates-details"><summary>Use latitude & longitude</summary><form onSubmit={coordinates}><div className="two-fields"><label>Latitude<input value={lat} onChange={(e) => setLat(e.target.value)} placeholder="−26.2041" /></label><label>Longitude<input value={lon} onChange={(e) => setLon(e.target.value)} placeholder="28.0473" /></label></div><button className="secondary-button" type="submit">Go to coordinates<ArrowRight size={14} /></button></form></details><input type="file" accept=".geojson,.json,application/geo+json" ref={geoInput} hidden onChange={(e) => { importGeometry(e.target.files[0]); e.target.value = ''; }} /><button className="file-import" onClick={() => geoInput.current.click()}><FileJson size={17} />Import a GeoJSON boundary</button></section><div className="soft-note"><ShieldCheck size={18} /><span>Location is never guessed from image colours. You confirm the site before analysis.</span></div></aside><div className="setup-main"><LocationHelp photo={photo} boundary={boundary} onPhoto={setPhoto} onName={setName} /><section className="panel"><div className="panel-heading"><div className="step-title"><span>2</span><div><h2>Define the assessment area</h2><p>Zoom in and draw around the land. Assess 1–2,500 hectares at a time.</p></div></div></div><AssessmentMap boundary={boundary} onBoundary={changeBoundary} focus={focus} /><div className="panel-foot">The 1 km² shortcut selects an approximate square at the map centre. It does not detect a property boundary. GeoJSON must use WGS84 longitude, latitude.</div></section><form className="panel assessment-form padded" onSubmit={submit} noValidate><div className="step-title"><span>3</span><h2>Set up your assessment</h2></div><label>Assessment name <span className="optional">required - a name you will recognise</span><input required maxLength={120} value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. West Rand rehabilitation site" /></label><label>Property or farm/erf reference <span className="optional">optional - useful for a title-record search</span><input maxLength={250} value={propertyRef} onChange={(e) => setPropertyRef(e.target.value)} placeholder="e.g. Erf 123, township name; or farm name, number and portion" /></label><p className="field-help">Copy this from an existing title deed or municipal record if you have one. A street address alone may not identify the registered property. We save your reference as unverified; no ownership search is connected.</p><div className="four-fields"><label>First year <span className="optional">2017 or later</span><input type="number" min="2017" max={endYear - 4} value={startYear} onChange={(e) => setStartYear(e.target.value)} required /></label><label>Last complete year <span className="optional">at least 5 years of history</span><input type="number" min={Number(startYear) + 4} max={capabilities?.latest_complete_year || new Date().getFullYear() - 1} value={endYear} onChange={(e) => setEndYear(e.target.value)} required /></label><label>Comparable season <span className="optional">same 3 months each year</span><select value={month} onChange={(e) => setMonth(e.target.value)}>{seasonNames.map((s, i) => <option key={s} value={i + 1}>{s}</option>)}</select></label><label>Outlook horizon <span className="optional">how far ahead to explore</span><select value={horizon} onChange={(e) => setHorizon(e.target.value)}>{[3, 5, 10, 15].map((v) => <option key={v} value={v}>{v} years</option>)}</select></label></div><p className="field-help">You can keep the suggested years and 5-year outlook. Choose the same three months to compare vegetation fairly; Jan-Mar often captures summer growth, while winter-rainfall areas may need Jul-Sep. These satellite samples are seasonal, not annual averages.</p><label>Site notes <span className="optional">optional · treated as unverified</span><textarea maxLength={3000} rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Optional: known past use and source, current condition, or your planned use…" /></label><label className="confirmation"><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} disabled={!boundary} /><span>I have checked the map location and boundary. This is the land I want to assess.</span></label>{submissionIssues.length > 0 && <div className="submission-feedback" role="alert" tabIndex={-1} ref={submissionFeedback}><strong>The assessment has not started yet</strong><ul>{submissionIssues.map((issue) => <li key={issue}>{issue}</li>)}</ul><p>Correct the details above, then press Start assessment again.</p></div>}<div className="form-footer"><span><Database size={15} />Free public datasets · internet required<br />Research includes history, moisture, rainfall and future options. Processing can take several minutes.</span><button type="submit" className="primary-button" disabled={submitting}>{submitting ? <Loader2 size={17} className="spin" /> : <Satellite size={17} />}{submitting ? 'Starting assessment...' : 'Start assessment'}<ArrowRight size={17} /></button></div></form></div></div></>}
    {view === 'library' && <><div className="compact-intro"><div className="kicker">YOUR SAVED WORK</div><h1>Assessment library</h1><p>Reopen site reports, inspect their evidence and export the full record.</p></div><section className="panel"><div className="panel-heading"><h2>{assessments.length} saved assessment{assessments.length === 1 ? '' : 's'}</h2><button className="text-button" onClick={() => refresh().catch((e) => setError(errorText(e)))}>Refresh</button></div>{assessments.length ? <AssessmentList rows={assessments} onOpen={openAssessment} /> : <div className="quiet-state">No assessments yet. Select “New assessment” to begin.</div>}</section></>}
    {view === 'report' && selected && <>{running(selected) ? <section className="processing-card panel"><div className="processing-icon"><Satellite size={38} /></div><div className="kicker">READING THE LANDSCAPE</div><h1>{selected.name}</h1><p aria-live="polite">{selected.stage}</p><div className="processing-track"><i style={{ width: `${selected.progress || 0}%` }} /></div><span>{selected.progress || 0}% · Processing real datasets</span><div className="soft-note"><BookOpen size={18} /><span>This may take several minutes. You can visit the library and reopen this assessment while the backend continues processing.</span></div><button className="secondary-button" onClick={() => navigate('library')}>Back to library<ArrowRight size={16} /></button></section> : selected.result ? <AssessmentReport assessment={selected} onReassess={() => reassess(selected)} /> : <section className="panel padded"><TriangleAlert size={28} /><h2>{selected.status === 'interrupted' ? 'Processing was interrupted' : 'The assessment could not finish'}</h2><p>{selected.error || selected.stage}</p><button className="primary-button" onClick={() => { changeBoundary(selected.site.geometry); setName(selected.name); setStartYear(selected.options.start_year); setEndYear(selected.options.end_year); setMonth(selected.options.season_month); setHorizon(selected.options.horizon); navigate('new'); }}>Review boundary and retry<ArrowRight size={16} /></button></section>}</>}
    {view === 'sources' && <><div className="compact-intro"><div className="kicker">THE FOUNDATION OF EVERY ANSWER</div><h1>Open data. Visible limits.</h1><p>A local research system built on real observations and explicit assumptions.</p></div><div className="method-grid">{[
      { icon: Satellite, title: 'Satellite observations', body: 'Sentinel-2 Collection 1 surface reflectance. Up to three clear acquisitions per year in the same season; cloud, shadow, snow and unclassified pixels excluded. At least 70% valid site coverage per scene. Indices are sampled at approximately 20m, coarser for large areas.' },
      { icon: Globe2, title: 'Weather & climate', body: 'ERA5 historical reanalysis provides regional temperature, rain and solar radiation. Two CMIP6 HighResMIP models compare decadal climate periods. These are gridded models, not measurements from a sensor on your land.' },
      { icon: BookOpen, title: 'Forecasts that face a test', body: 'At least five observed years are required. A linear NDVI trend competes against persistence using rolling-origin historical errors. The better baseline is projected with an approximate uncertainty band. Climate projections are reported separately, not disguised as a trained vegetation model.' },
      { icon: Leaf, title: 'Screening, with a reason', body: 'Solar and restoration pathways use visible formulas based on retrieved observations. The rubric has not been validated against real land-use outcomes. Food production, grazing, batteries and development are withheld until the necessary safety, soil, water and infrastructure evidence exists.' },
      { icon: MapPin, title: 'History without invented stories', body: 'Photo GPS and your confirmed boundary locate the assessment. Vegetation and mapped land use offer clues. The system does not assert that land is abandoned, date its last use, identify its owner or invent a closure reason.' },
      { icon: ShieldCheck, title: 'Free for this research workflow', body: 'No paid API keys, sensor hardware or subscription is required. Public providers have usage limits. Open-Meteo’s free hosted service is for non-commercial use; review licences and hosting terms before commercial use. Photos and reports stay in your local backend storage.' },
    ].map(({ icon: Icon, title, body }) => <article className="panel padded" key={title}><Icon size={25} /><h2>{title}</h2><p>{body}</p></article>)}</div><section className="panel padded source-links"><h2>Source documentation & attribution</h2>{capabilities?.sources?.map((s) => <a key={s.name} href={s.url} target="_blank" rel="noreferrer">{s.name}<ArrowUpRight size={16} /></a>)}<p>National boundary: geoBoundaries gbOpen / original contributors. Base maps: Esri imagery and © OpenStreetMap contributors. All records link to their sources when available.</p></section></>}
    <footer className="app-footer"><span>MINELAND NEXUS</span><span>South Africa · Evidence before answers.</span><span>Research screening · v5.0</span></footer></div></main></div>;
}

function AssessmentList({ rows, onOpen }) {
  return <div className="assessment-list">{rows.map((row) => <button key={row.id} data-assessment-id={row.id} onClick={() => onOpen(row.id)}><span className="list-site-icon"><MapPin size={20} /></span><span className="list-site-info"><strong>{row.name}</strong><small>{row.site.area_ha.toLocaleString()} ha · {row.site.center.lat.toFixed(3)}, {row.site.center.lon.toFixed(3)} · {new Date(row.created_at).toLocaleDateString()}</small></span><span className={`pill ${row.status === 'partial' ? 'warning' : ''}`}>{row.status}</span><ArrowUpRight size={17} /></button>)}</div>;
}
