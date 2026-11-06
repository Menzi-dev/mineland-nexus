import React, { useState } from 'react';
import { getNDVI, getNDWI } from '../services/api';

function SatelliteDashboard() {
  const [loading, setLoading] = useState(false);
  const [ndviData, setNdviData] = useState(null);
  const [ndwiData, setNdwiData] = useState(null);
  const [error, setError] = useState(null);
  const [startDate, setStartDate] = useState('2026-08-15');
  const [endDate, setEndDate] = useState('2026-08-20');

  const fetchNDVI = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getNDVI(startDate, endDate);
      setNdviData(response.data);
      console.log('NDVI Data:', response.data);
    } catch (err) {
      setError('Failed to fetch NDVI: ' + err.message);
      console.error(err);
    }
    setLoading(false);
  };

  const fetchNDWI = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getNDWI(startDate, endDate);
      setNdwiData(response.data);
      console.log('NDWI Data:', response.data);
    } catch (err) {
      setError('Failed to fetch NDWI: ' + err.message);
      console.error(err);
    }
    setLoading(false);
  };

  const quickTest = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getNDVI('2026-08-15', '2026-08-20');
      setNdviData(response.data);
      console.log('Quick Test NDVI:', response.data);
    } catch (err) {
      setError('Quick test failed: ' + err.message);
      console.error(err);
    }
    setLoading(false);
  };

  const clearResults = () => {
    setNdviData(null);
    setNdwiData(null);
    setError(null);
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4">🛰️ Satellite Analysis - Northern Cape</h2>

      <div className="flex flex-wrap gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Start Date</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">End Date</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>
        <div className="flex items-end gap-2 flex-wrap">
          <button
            onClick={fetchNDVI}
            disabled={loading}
            className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50 text-sm"
          >
            🌿 Get NDVI
          </button>
          <button
            onClick={fetchNDWI}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            💧 Get NDWI
          </button>
          <button
            onClick={quickTest}
            disabled={loading}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50 text-sm"
          >
            ⚡ Quick Test
          </button>
          <button
            onClick={clearResults}
            disabled={loading}
            className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 disabled:opacity-50 text-sm"
          >
            ✕ Clear
          </button>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-700">
        <p>📍 <span className="font-semibold">Province:</span> Northern Cape, South Africa</p>
        <p>📍 <span className="font-semibold">Area:</span> Sishen/Kathu mining region</p>
        <p>📍 <span className="font-semibold">Coordinates:</span> 27.45°E, 23.45°S</p>
        <p>⏱️ <span className="font-semibold">Processing Time:</span> ~5-15 seconds</p>
        <p className="text-xs text-blue-500 mt-1">📊 Data from Copernicus Sentinel-2 satellites</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          ❌ {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Fetching satellite data...</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {ndviData && ndviData.status === 'success' && (
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <div className="flex justify-between items-start">
              <h3 className="text-lg font-semibold text-green-800">🌿 NDVI Results</h3>
              <span className="text-xs bg-green-200 text-green-800 px-2 py-1 rounded">✅ REAL Data</span>
            </div>
            <div className="mt-2 space-y-1 text-sm">
              <p><span className="font-medium">Mean:</span> {ndviData.statistics?.mean?.toFixed(3) || ndviData.data?.statistics?.mean?.toFixed(3) || 'N/A'}</p>
              <p><span className="font-medium">Min:</span> {ndviData.statistics?.min?.toFixed(3) || ndviData.data?.statistics?.min?.toFixed(3) || 'N/A'}</p>
              <p><span className="font-medium">Max:</span> {ndviData.statistics?.max?.toFixed(3) || ndviData.data?.statistics?.max?.toFixed(3) || 'N/A'}</p>
              <p><span className="font-medium">Resolution:</span> {ndviData.statistics?.shape?.[0]} x {ndviData.statistics?.shape?.[1]}</p>
              <p className="text-xs text-gray-500 mt-2">📅 {ndviData.period?.start} → {ndviData.period?.end}</p>
              <p className="text-xs text-gray-500 mt-2">🛰️ Copernicus Sentinel-2</p>
              <p className="text-xs text-gray-500">📍 Sishen/Kathu - Northern Cape</p>
            </div>
          </div>
        )}

        {ndwiData && ndwiData.status === 'success' && (
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <div className="flex justify-between items-start">
              <h3 className="text-lg font-semibold text-blue-800">💧 NDWI Results</h3>
              <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded">✅ REAL Data</span>
            </div>
            <div className="mt-2 space-y-1 text-sm">
              <p><span className="font-medium">Mean:</span> {ndwiData.statistics?.mean?.toFixed(3) || ndwiData.data?.statistics?.mean?.toFixed(3) || 'N/A'}</p>
              <p><span className="font-medium">Min:</span> {ndwiData.statistics?.min?.toFixed(3) || ndwiData.data?.statistics?.min?.toFixed(3) || 'N/A'}</p>
              <p><span className="font-medium">Max:</span> {ndwiData.statistics?.max?.toFixed(3) || ndwiData.data?.statistics?.max?.toFixed(3) || 'N/A'}</p>
              <p><span className="font-medium">Resolution:</span> {ndwiData.statistics?.shape?.[0]} x {ndwiData.statistics?.shape?.[1]}</p>
              <p className="text-xs text-gray-500 mt-2">📅 {ndwiData.period?.start} → {ndwiData.period?.end}</p>
              <p className="text-xs text-gray-500 mt-2">🛰️ Copernicus Sentinel-2</p>
              <p className="text-xs text-gray-500">📍 Sishen/Kathu - Northern Cape</p>
            </div>
          </div>
        )}

        {!ndviData && !ndwiData && !loading && !error && (
          <div className="col-span-2 text-center py-8 text-gray-500">
            <p className="text-lg">📡 Click a button above to fetch satellite data</p>
            <p className="text-sm mt-2">Data will appear here once fetched</p>
          </div>
        )}
      </div>

      <div className="mt-6 bg-gray-50 rounded-lg p-4 border border-gray-200">
        <h4 className="font-semibold text-gray-700">📖 Interpretation Guide</h4>
        <div className="mt-2 text-sm text-gray-600 grid grid-cols-1 md:grid-cols-2 gap-2">
          <div>
            <p><span className="font-medium text-green-600">🌿 NDVI (Vegetation Health):</span></p>
            <p>• 0.6 - 1.0: Dense healthy vegetation</p>
            <p>• 0.2 - 0.6: Moderate vegetation</p>
            <p>• 0.0 - 0.2: Bare soil, urban areas</p>
            <p>• -1.0 - 0.0: Water, rocks, mining areas</p>
          </div>
          <div>
            <p><span className="font-medium text-blue-600">💧 NDWI (Water Presence):</span></p>
            <p>• 0.4 - 1.0: Water bodies</p>
            <p>• 0.0 - 0.4: Moist soil, vegetation</p>
            <p>• -0.5 - 0.0: Dry soil, urban areas</p>
            <p>• -1.0 - -0.5: Very dry, mining areas</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SatelliteDashboard;
