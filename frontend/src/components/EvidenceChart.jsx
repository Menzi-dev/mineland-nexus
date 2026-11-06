import React from 'react';

export default function EvidenceChart({ observations = [], predictions = [] }) {
  if (!observations.length) return <div className="quiet-state">No usable satellite observations. Review the data gaps below.</div>;
  const rows = [...observations, ...predictions];
  const xmin = rows[0].year, xmax = Math.max(rows[rows.length - 1].year, xmin + 1);
  const values = rows.flatMap((r) => [r.ndvi, r.lower, r.upper]).filter((v) => v != null);
  const ymin = Math.max(-1, Math.min(-0.1, ...values) - 0.05), ymax = Math.min(1, Math.max(0.6, ...values) + 0.05);
  const x = (v) => 54 + (v - xmin) / (xmax - xmin) * 620;
  const y = (v) => 212 - (v - ymin) / (ymax - ymin) * 180;
  const path = (data, key = 'ndvi') => data.map((r, i) => `${i ? 'L' : 'M'}${x(r.year)},${y(r[key])}`).join(' ');
  const band = predictions.length ? `${path(predictions, 'upper')} ${[...predictions].reverse().map((r) => `L${x(r.year)},${y(r.lower)}`).join(' ')} Z` : '';
  return <div className="chart-wrap"><svg viewBox="0 0 710 255" role="img" aria-label="Measured same-season vegetation index and future baseline prediction with uncertainty band">
    {[0, 1, 2, 3, 4].map((i) => { const v = ymin + (ymax - ymin) * i / 4; return <g key={i}><line x1="54" x2="674" y1={y(v)} y2={y(v)} stroke="#e8ede7" /><text x="43" y={y(v) + 4} textAnchor="end">{v.toFixed(2)}</text></g>; })}
    {band && <path d={band} fill="#d6e6bf" opacity="0.6" />}
    {predictions.length > 0 && <><line x1={x(observations.at(-1).year)} x2={x(observations.at(-1).year)} y1="25" y2="215" stroke="#c5cfc2" strokeDasharray="4 4" /><path d={path([observations.at(-1), ...predictions])} fill="none" stroke="#92a455" strokeWidth="2.5" strokeDasharray="6 5" /></>}
    <path d={path(observations)} fill="none" stroke="#22563c" strokeWidth="3" />
    {observations.map((r) => <g key={r.year}><circle cx={x(r.year)} cy={y(r.ndvi)} r="4.5" fill="#fff" stroke="#22563c" strokeWidth="2"><title>{r.year}: NDVI {r.ndvi}, {r.scene_count} scenes</title></circle></g>)}
    {rows.filter((r, i) => i % Math.max(1, Math.ceil(rows.length / 9)) === 0 || i === rows.length - 1).map((r) => <text key={r.year} x={x(r.year)} y="237" textAnchor="middle">{r.year}</text>)}
  </svg><div className="chart-legend"><span><i className="observed" />Satellite observations</span><span><i className="projected" />Baseline projection</span><span><i className="uncertain" />Approximate uncertainty</span></div></div>;
}
