import React, { useEffect, useRef, useState } from 'react';
import { MapPin, Loader2, CheckCircle2, TriangleAlert } from 'lucide-react';
import { client, errorText } from '../services/national';

export default function LocationHelp({ photo, boundary, onPhoto, onName }) {
  const [place, setPlace] = useState(null), [looking, setLooking] = useState(false), [lookupError, setLookupError] = useState('');
  const [ai, setAI] = useState(null), [analysing, setAnalysing] = useState(false), [aiError, setAIError] = useState('');
  const activePhoto = useRef(null), attempted = useRef(null);
  activePhoto.current = photo?.id;
  useEffect(() => { client.get('/api/ai/status').then((r) => setAI(r.data)).catch(() => {}); }, []);
  useEffect(() => {
    if (photo?.id && ai?.status === 'ready' && !photo.visual_analysis && attempted.current !== photo.id) {
      attempted.current = photo.id; analyse();
    }
  }, [photo?.id, ai?.status]);
  useEffect(() => {
    setPlace(null); setLookupError(''); setLooking(false);
    if (!boundary) return;
    const coordinates = boundary.type === 'Polygon' ? boundary.coordinates.flat() : boundary.coordinates.flat(2);
    const lat = (Math.min(...coordinates.map((p) => p[1])) + Math.max(...coordinates.map((p) => p[1]))) / 2;
    const lon = (Math.min(...coordinates.map((p) => p[0])) + Math.max(...coordinates.map((p) => p[0]))) / 2;
    let cancelled = false;
    setLooking(true);
    const timer = setTimeout(() => client.get('/api/location', { params: { lat, lon } }).then((r) => {
      if (!cancelled) setPlace(r.data);
    }).catch(() => { if (!cancelled) setLookupError('The address search did not respond. You can still assess the selected coordinates.'); }).finally(() => { if (!cancelled) setLooking(false); }), 500);
    return () => { cancelled = true; clearTimeout(timer); };
  }, [boundary]);
  async function analyse() {
    const identifier = photo.id;
    setAnalysing(true); setAIError('');
    try { const response = await client.post(`/api/photos/${identifier}/analyse`, {}, { timeout: 120000 }); if (activePhoto.current === identifier) onPhoto(response.data); }
    catch (e) { setAIError(errorText(e)); } finally { setAnalysing(false); }
  }
  return <section className="panel padded location-help"><div className="kicker">LOCATION & PHOTO CHECK</div><h3>{boundary ? 'Your selected land' : 'Help us match the right land'}</h3>
    {looking && <p role="status"><Loader2 size={15} className="spin" /> Searching the selected place…</p>}
    {place && <><p><MapPin size={17} /> <strong>{place.name}</strong></p><small>{place.note}</small><button type="button" className="text-button" onClick={() => onName(place.address?.farm || place.address?.village || place.address?.suburb || place.address?.town || place.address?.city || 'My land assessment')}>Use this place as the assessment name</button></>}
    {lookupError && <p>{lookupError}</p>}
    {!boundary && <ol><li>Upload a photo with GPS, search a nearby place, or enter coordinates.</li><li>Zoom in on the map. Draw the land boundary or choose “Select a small plot”.</li><li>Check the outlined land, enter a name, and confirm before starting.</li></ol>}
    {photo && <><div className="soft-note">{photo.gps ? <CheckCircle2 size={18} /> : <TriangleAlert size={18} />}<span>{photo.gps ? 'The white map point marks the photo camera location. Draw around the land shown; the camera may be outside its boundary.' : 'This photo has no GPS. Exact location cannot be established from a small, unrecognisable land image. Search for the nearest known place and select the land yourself.'}</span></div>
      {ai?.status === 'ready' ? <button className="secondary-button" type="button" disabled={analysing} onClick={analyse}>{analysing ? <Loader2 size={16} className="spin" /> : <CheckCircle2 size={16} />}{analysing ? 'Reading visible photo clues…' : 'Read photo clues with local AI'}</button> : <p className="field-help">Photo AI is not configured on this computer. Photo GPS, map selection and automated public-data research remain available.</p>}
      {aiError && <p role="alert">{aiError}</p>}
      {photo.visual_analysis?.status === 'available' && <div className="visual-clues"><strong>Possible visible features · AI interpretation</strong><ul>{photo.visual_analysis.visible_features.map((r, i) => <li key={i}>{r}</li>)}</ul>{photo.visual_analysis.readable_signs?.length > 0 && <p>Possible sign text: {photo.visual_analysis.readable_signs.join('; ')}</p>}<p className="field-help">{photo.visual_analysis.notice}</p></div>}
      {photo.visual_analysis && photo.visual_analysis.status !== 'available' && <p>{photo.visual_analysis.message}</p>}
    </>}
    {boundary && <p className="field-help">The same satellite, history, moisture and recommendation research runs whether you start with a photo or select the place directly on the map.</p>}
  </section>;
}
