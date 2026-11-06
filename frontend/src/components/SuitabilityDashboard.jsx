import React, { useState } from 'react';
import { BarChart3, Battery, Beef, Building2, CalendarDays, ChartNoAxesColumn, CircleAlert, Database, HardHat, Leaf, Lightbulb, MapPin, Rocket, Sun, Target, Trophy, Wheat, X } from 'lucide-react';
import { getSuitability, getRecommendation, getComprehensiveRecommendation } from '../services/api';
import { REFERENCE_MINE } from '../data/mineSite';

function SuitabilityDashboard() {
  const [loading, setLoading] = useState(false);
  const [suitabilityData, setSuitabilityData] = useState(null);
  const [recommendationData, setRecommendationData] = useState(null);
  const [error, setError] = useState(null);


  const fetchSuitability = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getSuitability();
      setSuitabilityData(response.data);
      console.log('Suitability Data:', response.data);
    } catch (err) {
      setError('Failed to fetch suitability: ' + err.message);
    }
    setLoading(false);
  };

  const fetchRecommendation = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getComprehensiveRecommendation(5);
      setRecommendationData(response.data);
      console.log('Recommendation Data:', response.data);
    } catch (err) {
      setError('Failed to fetch recommendation: ' + err.message);
    }
    setLoading(false);
  };

  const fetchAll = async () => {
    setLoading(true);
    setError(null);
    try {
      const [suitRes, recRes] = await Promise.all([
        getSuitability(),
        getComprehensiveRecommendation(5)
      ]);
      setSuitabilityData(suitRes.data);
      setRecommendationData(recRes.data);
      console.log('All data fetched');
    } catch (err) {
      setError('Failed to fetch data: ' + err.message);
    }
    setLoading(false);
  };

  const clearResults = () => {
    setSuitabilityData(null);
    setRecommendationData(null);
    setError(null);
  };

  const getScoreColor = (score) => {
    if (score >= 70) return 'bg-green-500';
    if (score >= 50) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getRatingLabel = (score) => {
    if (score >= 70) return 'High';
    if (score >= 50) return 'Medium';
    return 'Low';
  };

  const getLandUseIcon = (key) => {
    const icons = {
      'solar_energy': Sun,
      'solar': Sun,
      'agriculture': Wheat,
      'grazing': Beef,
      'conservation': Leaf,
      'battery_storage': Battery,
      'mining_rehabilitation': HardHat,
      'community_development': Building2
    };
    return icons[key] || BarChart3;
  };

  const LandUseIcon = ({ name, size = 18 }) => {
    const Icon = getLandUseIcon(name);
    return <Icon size={size} aria-hidden="true" />;
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-5 mt-6">
      <h2 className="text-xl font-bold mb-4 flex items-center"><BrainIcon /> Land Suitability & Recommendations</h2>

      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
        <div className="flex items-start gap-3">
          <MapPin className="text-green-700 mt-0.5" size={20} aria-hidden="true" />
          <div>
            <p className="text-xs uppercase tracking-wide text-green-700 font-semibold">Selected reference site</p>
            <p className="font-bold text-gray-900">{REFERENCE_MINE.name}</p>
            <p className="text-sm text-gray-600">{REFERENCE_MINE.description}</p>
            <p className="text-xs text-gray-500 mt-1">{REFERENCE_MINE.coordinates.lat}, {REFERENCE_MINE.coordinates.lon}</p>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-4">
        <button
          onClick={fetchAll}
          disabled={loading}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 disabled:opacity-50 text-sm"
        >
          <Rocket size={16} aria-hidden="true" /> Full Analysis
        </button>
        <button
          onClick={fetchSuitability}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50 text-sm"
        >
          <BarChart3 size={16} aria-hidden="true" /> Suitability Scores
        </button>
        <button
          onClick={fetchRecommendation}
          disabled={loading}
          className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 disabled:opacity-50 text-sm"
        >
          <Target size={16} aria-hidden="true" /> Get Recommendation
        </button>
        <button
          onClick={clearResults}
          disabled={loading}
          className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 disabled:opacity-50 text-sm"
        >
          <X size={16} aria-hidden="true" /> Clear
        </button>
      </div>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3 mb-4 text-xs text-purple-700">
        <p><Database size={15} className="inline mr-1" aria-hidden="true" /><span className="font-semibold">Analysis:</span> 9 Northern Cape data sources combined</p>
        <p><ChartNoAxesColumn size={15} className="inline mr-1" aria-hidden="true" /><span className="font-semibold">Sources:</span> Satellite, Solar, Mining, Community, Infrastructure, DEM, Land Cover, Protected Areas, Climate</p>
        <p className="text-purple-500 mt-1"><Lightbulb size={15} className="inline mr-1" aria-hidden="true" />Values below are calculated from the returned evidence inputs.</p>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          <CircleAlert size={16} className="inline mr-1" aria-hidden="true" />{error}
        </div>
      )}

      {loading && (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
          <span className="ml-3 text-gray-600">Analyzing all data sources...</span>
        </div>
      )}

      {/* Recommendation Card */}
      {recommendationData && recommendationData.status === 'success' && (
        <div className="mb-5 bg-green-50 rounded-lg p-4 border border-green-400">
          <div className="flex items-center justify-between flex-wrap">
            <div>
              <h3 className="text-lg font-bold text-green-800 flex items-center"><Trophy size={18} className="mr-2" aria-hidden="true" />Best Recommendation</h3>
              <p className="text-base font-semibold text-green-700 mt-1 flex items-center gap-2">
                <LandUseIcon name={recommendationData.recommendation?.toLowerCase().replaceAll(' ', '_')} size={16} />
                {recommendationData.recommendation}
              </p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600">{recommendationData.recommendation_score}%</div>
              <div className="text-xs text-gray-500">Calculated suitability</div>
            </div>
          </div>
          <div className="mt-3 p-3 bg-white/60 rounded-lg text-sm">
            <p className="text-gray-700"><Lightbulb size={16} className="inline mr-1" aria-hidden="true" /><span className="font-semibold">Why:</span> {recommendationData.reason}</p>
          </div>
          <div className="mt-3 text-xs text-gray-500 grid grid-cols-2 md:grid-cols-4 gap-2">
            <div><MapPin size={14} className="inline mr-1" aria-hidden="true" />Source region: {recommendationData.location}</div>
            <div><CalendarDays size={14} className="inline mr-1" aria-hidden="true" />{new Date(recommendationData.timestamp).toLocaleString()}</div>
            <div><Database size={14} className="inline mr-1" aria-hidden="true" />{recommendationData.data_sources_used?.length || 0} sources used</div>
          </div>
          {recommendationData.evidence && (
            <div className="mt-3 text-xs text-gray-600 grid grid-cols-2 md:grid-cols-4 gap-1">
              {Object.entries(recommendationData.evidence).map(([key, value]) => (
                <div key={key} className="bg-white/50 p-1 rounded text-center">
                  <span className="capitalize">{key.replace('_', ' ')}</span>: {typeof value === 'number' ? value.toFixed(2) : value}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Suitability Scores */}
      {suitabilityData && suitabilityData.status === 'success' && (
        <div>
          <h4 className="text-lg font-semibold mb-3"><BarChart3 size={19} className="inline mr-2" aria-hidden="true" />All Suitability Scores</h4>
          <div className="space-y-2">
            {suitabilityData.all_scores_sorted?.map(([key, value]) => (
              <div key={key} className="flex items-center gap-2">
                {(() => {
                  const score = typeof value === 'number' ? value : value?.score;
                  return (
                    <>
                <span className="w-40 text-xs capitalize flex items-center gap-2">
                  <LandUseIcon name={key} size={16} /> {key.replaceAll('_', ' ')}
                </span>
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${getScoreColor(score)} transition-all`}
                    style={{ width: `${Math.min(100, Math.max(0, score || 0))}%` }}
                  ></div>
                </div>
                <span className="text-xs font-medium w-12 text-right">{score ?? 'N/A'}%</span>
                <span className={`text-xs w-16 ${score >= 70 ? 'text-green-600' : score >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>{score == null ? 'N/A' : getRatingLabel(score)}</span>
                    </>
                  );
                })()}
              </div>
            ))}
          </div>
          <div className="mt-4 text-xs text-gray-400 border-t pt-2">
            <MapPin size={14} className="inline mr-1" aria-hidden="true" />Source region: {suitabilityData.location} | <CalendarDays size={14} className="inline mx-1" aria-hidden="true" />{new Date(suitabilityData.timestamp).toLocaleString()}
          </div>
        </div>
      )}

      {!suitabilityData && !recommendationData && !loading && !error && (
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg"><BrainIcon /> Run Full Analysis to get land suitability recommendations</p>
          <p className="text-sm mt-2">The system will analyze 9 data sources for Northern Cape</p>
        </div>
      )}
    </div>
  );
}

function BrainIcon() {
  return <ChartNoAxesColumn size={22} className="inline mr-2" aria-hidden="true" />;
}

export default SuitabilityDashboard;
