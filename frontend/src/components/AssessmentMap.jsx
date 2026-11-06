import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Crosshair, Layers, MousePointer2, Pentagon, RotateCcw, Undo2, Check } from 'lucide-react';
import { asset } from '../services/national';

maplibregl.setWorkerUrl(workerUrl);

const empty = { type: 'FeatureCollection', features: [] };
const feature = (geometry) => ({ type: 'Feature', properties: {}, geometry });

export default function AssessmentMap({ boundary, onBoundary, focus, overlay, readOnly = false }) {
  const container = useRef(null), mapRef = useRef(null), points = useRef([]), drawingRef = useRef(false), callback = useRef(onBoundary);
  const [ready, setReady] = useState(false), [drawing, setDrawing] = useState(false), [count, setCount] = useState(0), [imagery, setImagery] = useState(true), [mapError, setMapError] = useState('');
  const [picking, setPicking] = useState(false), pickingRef = useRef(false), readOnlyRef = useRef(readOnly);
  readOnlyRef.current = readOnly;
  callback.current = onBoundary;
  const refreshSketch = () => {
    const map = mapRef.current;
    const rows = points.current.map((coordinates) => feature({ type: 'Point', coordinates }));
    if (points.current.length > 1) rows.push(feature({ type: 'LineString', coordinates: points.current }));
    map?.getSource('sketch')?.setData({ type: 'FeatureCollection', features: rows });
    setCount(points.current.length);
  };
  useEffect(() => {
    const map = new maplibregl.Map({ container: container.current, center: [24.1, -29], zoom: 4.5, maxZoom: 18,
      style: { version: 8, sources: {
        satellite: { type: 'raster', tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'], tileSize: 256, attribution: 'Imagery © Esri, Maxar, Earthstar Geographics; capture dates vary' },
        streets: { type: 'raster', tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'], tileSize: 256, maxzoom: 19, attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' },
      }, layers: [{ id: 'satellite', type: 'raster', source: 'satellite' }, { id: 'streets', type: 'raster', source: 'streets', layout: { visibility: 'none' } }] } });
    mapRef.current = map;
    if (import.meta.env.DEV) container.current.__assessmentMap = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    map.on('load', () => {
      for (const id of ['boundary', 'sketch']) map.addSource(id, { type: 'geojson', data: empty });
      map.addSource('photo-location', { type: 'geojson', data: empty });
      map.addLayer({ id: 'photo-location', type: 'circle', source: 'photo-location', paint: { 'circle-radius': 8, 'circle-color': '#ffffff', 'circle-stroke-color': '#28694e', 'circle-stroke-width': 4 } });
      map.addLayer({ id: 'boundary-fill', type: 'fill', source: 'boundary', paint: { 'fill-color': '#d1ef8d', 'fill-opacity': 0.12 } });
      map.addLayer({ id: 'boundary-line', type: 'line', source: 'boundary', paint: { 'line-color': '#e1ffa3', 'line-width': 3, 'line-dasharray': [2, 2] } });
      map.addLayer({ id: 'sketch-line', type: 'line', source: 'sketch', filter: ['==', '$type', 'LineString'], paint: { 'line-color': '#ffffff', 'line-width': 2, 'line-dasharray': [2, 1] } });
      map.addLayer({ id: 'sketch-points', type: 'circle', source: 'sketch', filter: ['==', '$type', 'Point'], paint: { 'circle-radius': 5, 'circle-color': '#dbf6a7', 'circle-stroke-color': '#172c24', 'circle-stroke-width': 2 } });
      setReady(true);
    });
    map.on('click', (event) => {
      if (readOnlyRef.current) return;
      if (pickingRef.current) {
        selectSquare(event.lngLat.lat, event.lngLat.lng, 100);
        pickingRef.current = false; setPicking(false); map.getCanvas().style.cursor = '';
        return;
      }
      if (!drawingRef.current) return;
      points.current.push([Number(event.lngLat.lng.toFixed(7)), Number(event.lngLat.lat.toFixed(7))]);
      refreshSketch();
    });
    map.on('error', (event) => {
      if (import.meta.env.DEV) console.error('Map error:', event.error);
      if (event.error?.message?.includes('Failed to fetch')) setMapError('Some map tiles could not load. Try the street map or check your connection.');
      else if (event.error?.message?.includes('Worker')) setMapError('The map drawing worker could not load. Refresh the page before selecting a boundary.');
    });
    const resize = new ResizeObserver(() => map.resize());
    resize.observe(container.current);
    return () => { resize.disconnect(); map.remove(); mapRef.current = null; };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!ready || !map) return;
    map.getSource('boundary').setData(boundary ? feature(boundary) : empty);
    if (boundary) {
      const coords = boundary.type === 'Polygon' ? boundary.coordinates.flat() : boundary.coordinates.flat(2);
      const bounds = coords.reduce((box, p) => box.extend(p), new maplibregl.LngLatBounds(coords[0], coords[0]));
      map.fitBounds(bounds, { padding: 65, maxZoom: 16, duration: 0 });
    }
  }, [ready, boundary]);
  useEffect(() => {
    if (!ready) return;
    mapRef.current.getSource('photo-location').setData(focus ? feature({ type: 'Point', coordinates: [focus.lon, focus.lat] }) : empty);
    if (focus) mapRef.current.flyTo({ center: [focus.lon, focus.lat], zoom: 14, duration: 900 });
  }, [ready, focus]);
  useEffect(() => {
    if (!ready) return;
    mapRef.current.setLayoutProperty('satellite', 'visibility', imagery ? 'visible' : 'none');
    mapRef.current.setLayoutProperty('streets', 'visibility', imagery ? 'none' : 'visible');
  }, [ready, imagery]);
  useEffect(() => {
    const map = mapRef.current;
    if (!ready) return;
    if (map.getLayer('ndvi')) map.removeLayer('ndvi');
    if (map.getSource('ndvi')) map.removeSource('ndvi');
    if (overlay) {
      map.addSource('ndvi', { type: 'image', url: asset(overlay.url), coordinates: overlay.coordinates });
      map.addLayer({ id: 'ndvi', type: 'raster', source: 'ndvi', paint: { 'raster-opacity': 0.7, 'raster-fade-duration': 0 } }, 'boundary-line');
    }
  }, [ready, overlay]);

  function startDrawing() {
    pickingRef.current = false; setPicking(false);
    points.current = []; refreshSketch(); drawingRef.current = true; setDrawing(true);
    mapRef.current.getCanvas().style.cursor = 'crosshair';
  }
  function finish() {
    if (points.current.length < 3) return;
    callback.current({ type: 'Polygon', coordinates: [[...points.current, points.current[0]]] });
    drawingRef.current = false; setDrawing(false); points.current = []; refreshSketch();
    mapRef.current.getCanvas().style.cursor = '';
  }
  function square() {
    const center = mapRef.current.getCenter(), lat = center.lat, lon = center.lng;
    selectSquare(lat, lon, 500);
  }
  function selectSquare(lat, lon, halfWidth) {
    drawingRef.current = false; setDrawing(false); points.current = []; refreshSketch();
    pickingRef.current = false; setPicking(false); mapRef.current.getCanvas().style.cursor = '';
    const dy = halfWidth / 111320, dx = halfWidth / (111320 * Math.cos(lat * Math.PI / 180));
    callback.current({ type: 'Polygon', coordinates: [[[lon-dx, lat-dy], [lon+dx, lat-dy], [lon+dx, lat+dy], [lon-dx, lat+dy], [lon-dx, lat-dy]]] });
  }
  return <div className="assessment-map">
    <div ref={container} className="map-canvas" aria-label="Interactive land assessment map" />
    <div className="map-top"><span className="map-tag"><span /> {overlay ? `Observed NDVI · ${overlay.date}` : imagery ? 'Satellite basemap · dates vary' : 'OpenStreetMap'}</span><button className="map-control" onClick={() => setImagery(!imagery)} aria-label="Switch map layer"><Layers size={17} /></button></div>
    {!readOnly && ready && <div className="map-draw-tools">{!drawing ? <><button onClick={startDrawing}><Pentagon size={16} />Draw boundary</button><button onClick={square}><Crosshair size={16} />Use 1 km² at map centre</button></> : <><span>{count} corners</span><button onClick={() => { points.current.pop(); refreshSketch(); }} disabled={!count}><Undo2 size={15} />Undo</button><button onClick={finish} disabled={count < 3}><Check size={15} />Finish boundary</button><button onClick={() => { drawingRef.current = false; setDrawing(false); points.current = []; refreshSketch(); mapRef.current.getCanvas().style.cursor = ''; }}>Cancel</button></>}{boundary && !drawing && <button onClick={() => callback.current(null)} aria-label="Clear boundary"><RotateCcw size={15} />Clear</button>}</div>}
    {drawing && <div className="map-instruction"><MousePointer2 size={15} />Click each corner of your land, then finish the boundary.</div>}
    {!readOnly && ready && !drawing && <button className={`small-plot-button ${picking ? 'active' : ''}`} onClick={() => { pickingRef.current = !pickingRef.current; setPicking(pickingRef.current); mapRef.current.getCanvas().style.cursor = pickingRef.current ? 'crosshair' : ''; }}><MapPinIcon />{picking ? 'Click the centre of your plot · 4 ha square' : 'Select a small plot on the map'}</button>}
    {mapError && <div className="map-error">{mapError}</div>}
  </div>;
}

function MapPinIcon() { return <Crosshair size={16} />; }
