import React, { useState } from 'react';
import { getHistoricalTrend, getFutureTrend, getFullTrend } from '../services/api';

function FutureTrends() {
  const [loading, setLoading] = useState(false);
  const [trendData, setTrendData] = useState(null);
  const [error, setError] = useState(null);
  const [yearsAhead, setYearsAhead] = useState(5);


  const fetchHistorical = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getHistoricalTrend();
      setTrendData({ type: 'historical', data: response.data });
      console.log('Historical Data:', response.data);
    } catch (err) {
      setError('Failed to fetch historical data: ' + err.message);
    }
    setLoading(false);
  };

  const fetchFuture = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getFutureTrend(yearsAhead);
      setTrendData({ type: 'future', data: response.data });
      console.log('Future Data:', response.data);
    } catch (err) {
      setError('Failed to fetch future data: ' + err.message);
    }
    setLoading(false);
  };

  const fetchFull = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getFullTrend(yearsAhead);
      setTrendData({ type: 'full', data: response.data });
      console.log('Full Timeline Data:', response.data);
    } catch (err) {
      setError('Failed to fetch full timeline: ' + err.message);
    }
    setLoading(false);
  };

  const clearResults = () => {
    setTrendData(null);
    setError(null);
  };

  // Helper to get trend icon
  const getTrendIcon = (value) => {
    if (value > 0) return '📈';
    if (value < 0) return '📉';
    return '➡️';
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4">🔮 Future Land Use Prediction</h2>

      <div className="flex flex-wrap gap-3 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Years Ahead</label>
          <input
            type="number"
            value={yearsAhead}
            onChange={(e) => setYearsAhead(parseInt(e.target.value) || 5)}
            min="1"
            max="20"
            className="mt-1 block w-24 rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
          />
        </div>
        <div className="flex items-end gap-2 flex-wrap">
          <button
            onClick={fetchHistorical}
            disabled={loading}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
          >
            📅 Historical
          </button>
          <button
            onClick={fetchFuture}
            disabled={loading}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50 text-sm"
          >
            🔮 Future
          </button>
          <button
            onClick={fetchFull}
            disabled={loading}
            className="bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700 disabled:opacity-50 text-sm"
          >
            📊 Full Timeline
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

      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 mb-4 text-sm text-indigo-700">
        <p>🔮 <span className="font-semibold">Vision:</span> Analyze past trends and predict future land use</p>
        <p>📊 <span className="font-semibold">Sources:</span> Historical NDVI, Mining extent, Climate projections</p>
        <p className="text-xs text-indigo-500 mt-1">💡 Enter years ahead and click "Future" to predict</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          ❌ {error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <span className="ml-3 text-gray-600">Analyzing trends...</span>
        </div>
      )}

      {trendData && trendData.data && trendData.data.status === 'success' && (
        <div className="space-y-4">

          {/* Historical Data Display */}
          {trendData.type === 'historical' && trendData.data.historical_data && (
            <div className="bg-gray-50 rounded-lg p-4 border">
              <h4 className="font-semibold text-gray-700">📊 Historical Data (2020-2026)</h4>
              <div className="mt-2 grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
                {trendData.data.historical_data.years?.map((year, idx) => (
                  <div key={year} className="bg-white p-2 rounded border text-center">
                    <div className="font-bold">{year}</div>
                    <div className="text-green-600">NDVI: {trendData.data.historical_data.ndvi?.[idx]?.toFixed(3)}</div>
                    <div className="text-orange-600">Mining: {trendData.data.historical_data.mining_extent?.[idx]}%</div>
                  </div>
                ))}
              </div>
              <div className="mt-2 text-xs text-gray-500">
                {getTrendIcon(trendData.data.trends?.ndvi?.slope)} NDVI trend: {trendData.data.trends?.ndvi?.trend}
                ({trendData.data.trends?.ndvi?.annual_change?.toFixed(4)} per year)
              </div>
            </div>
          )}

          {/* Future Prediction Display */}
          {trendData.type === 'future' && trendData.data.future_recommendation && (
            <>
              <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-lg p-4 border-2 border-purple-400">
                <h4 className="font-bold text-purple-800">🔮 Future Recommendation</h4>
                <p className="text-lg font-semibold text-purple-700">
                  {trendData.data.future_recommendation.best_use}
                </p>
                <p className="text-sm text-gray-700 mt-1">{trendData.data.future_recommendation.reason}</p>
                <div className="mt-2 flex gap-2 text-xs flex-wrap">
                  <span className="bg-purple-200 px-2 py-1 rounded">Score: {trendData.data.future_recommendation.score}%</span>
                  <span className="bg-green-200 px-2 py-1 rounded">Mining persists: {trendData.data.future_recommendation.mining_will_persist ? 'Yes' : 'No'}</span>
                  <span className="bg-blue-200 px-2 py-1 rounded">Vegetation: {trendData.data.future_recommendation.predicted_vegetation}</span>
                </div>
              </div>

              {/* Predictions */}
              {trendData.data.predictions && (
                <div className="bg-gray-50 rounded-lg p-4 border">
                  <h4 className="font-semibold text-gray-700">📈 Predicted Trends ({trendData.data.analysis_period})</h4>
                  <div className="mt-2 space-y-1 text-sm">
                    {trendData.data.predictions.years?.map((year, idx) => (
                      <div key={year} className="flex items-center gap-4 p-1 hover:bg-gray-100 rounded">
                        <span className="w-16 font-medium">{year}</span>
                        <span className="text-green-600">NDVI: {trendData.data.predictions.predicted_ndvi?.[idx]?.toFixed(3)}</span>
                        <span className="text-orange-600">Mining: {trendData.data.predictions.predicted_mining?.[idx]}%</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-2 text-xs text-gray-500 border-t pt-2">
                    📍 {yearsAhead}-year prediction: NDVI {trendData.data.predictions.ndvi_in_5_years?.toFixed(3)},
                    Mining {trendData.data.predictions.mining_extent_in_5_years}%
                  </div>
                </div>
              )}

              {/* Climate Impact */}
              {trendData.data.climate_impact && (
                <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
                  <h4 className="font-semibold text-yellow-800">🌡️ Climate Impact</h4>
                  <div className="mt-2 text-sm grid grid-cols-2 md:grid-cols-3 gap-2">
                    <div className="bg-white p-2 rounded text-center">Temp increase: +{trendData.data.climate_impact.temperature_increase}°C</div>
                    <div className="bg-white p-2 rounded text-center">Rainfall decrease: -{trendData.data.climate_impact.rainfall_decrease}%</div>
                    <div className="bg-white p-2 rounded text-center">Years ahead: {trendData.data.climate_impact.years_ahead}</div>
                  </div>
                </div>
              )}
            </>
          )}

          {/* Full Timeline Display */}
          {trendData.type === 'full' && (
            <div className="space-y-4">
              {/* Comparison Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-gray-50 rounded-lg p-3 border">
                  <h5 className="font-semibold text-gray-700">📅 Past (2020)</h5>
                  <p className="text-sm mt-1">NDVI: {trendData.data.past?.vegetation?.past || 'N/A'}</p>
                  <p className="text-sm">Mining: {trendData.data.past?.mining_extent?.past || 'N/A'}%</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-3 border border-blue-200">
                  <h5 className="font-semibold text-blue-700">📅 Present (2026)</h5>
                  <p className="text-sm mt-1">NDVI: {trendData.data.future?.historical_data?.ndvi?.slice(-1)[0]?.toFixed(3) || 'N/A'}</p>
                  <p className="text-sm">Mining: {trendData.data.future?.historical_data?.mining_extent?.slice(-1)[0] || 'N/A'}%</p>
                </div>
                <div className="bg-purple-50 rounded-lg p-3 border border-purple-200">
                  <h5 className="font-semibold text-purple-700">📅 Future ({yearsAhead} years)</h5>
                  <p className="text-sm mt-1">NDVI: {trendData.data.future?.predictions?.ndvi_in_5_years?.toFixed(3) || 'N/A'}</p>
                  <p className="text-sm">Mining: {trendData.data.future?.predictions?.mining_extent_in_5_years || 'N/A'}%</p>
                </div>
              </div>

              {/* Future Recommendation */}
              {trendData.data.future?.future_recommendation && (
                <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 border-2 border-green-400">
                  <h4 className="font-bold text-green-800">🏆 Future Recommendation</h4>
                  <p className="text-lg font-semibold text-green-700">
                    {trendData.data.future.future_recommendation.best_use}
                  </p>
                  <p className="text-sm text-gray-700 mt-1">{trendData.data.future.future_recommendation.reason}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {!trendData && !loading && !error && (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg">🔮 Click "Future" to predict land use</p>
          <p className="text-sm mt-2">Analyze past trends and future projections</p>
        </div>
      )}
    </div>
  );
}

export default FutureTrends;
