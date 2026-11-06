import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============ HEALTH ============
export const getHealth = () => api.get('/health');
export const getDashboardData = () => Promise.all([getHealth(), getCachedAll(), getSuitability(), getRecommendation()]);

// ============ CACHED REAL DATA (INSTANT) ============
export const getCachedNDVI = () => api.get('/api/cached/ndvi', { timeout: 5000 });
export const getCachedNDWI = () => api.get('/api/cached/ndwi', { timeout: 5000 });
export const getCachedSolar = () => api.get('/api/cached/solar', { timeout: 5000 });
export const getCachedMining = () => api.get('/api/cached/mining', { timeout: 5000 });
export const getCachedCommunity = () => api.get('/api/cached/community', { timeout: 5000 });
export const getCachedInfrastructure = () => api.get('/api/cached/infrastructure', { timeout: 5000 });
export const getCachedDEM = () => api.get('/api/cached/dem', { timeout: 5000 });
export const getCachedLandCover = () => api.get('/api/cached/landcover', { timeout: 5000 });
export const getCachedProtected = () => api.get('/api/cached/protected', { timeout: 5000 });
export const getCachedClimate = () => api.get('/api/cached/climate', { timeout: 5000 });
export const getCachedAll = () => api.get('/api/cached/all', { timeout: 5000 });

// ============ LEGACY ENDPOINTS (SLOW - FOR REFERENCE) ============
export const getNDVI = (start_date = '2026-08-15', end_date = '2026-08-20') =>
  api.get(`/api/ndvi?start_date=${start_date}&end_date=${end_date}`, { timeout: 60000 });
export const getNDWI = (start_date = '2026-08-15', end_date = '2026-08-20') =>
  api.get(`/api/ndwi?start_date=${start_date}&end_date=${end_date}`, { timeout: 60000 });

// ============ SOLAR ============
export const getSolar = () => api.get('/api/solar', { timeout: 15000 });
export const getSolarSuitability = () => api.get('/api/solar-suitability', { timeout: 15000 });

// ============ SUITABILITY ============
export const getSuitability = () => api.get('/api/suitability', { timeout: 60000 });
export const getRecommendation = () => api.get('/api/recommendation', { timeout: 60000 });

// ============ MINING ============
export const getMiningAreas = () => api.get('/api/mining-areas', { timeout: 15000 });
export const getDegradedLand = () => api.get('/api/degraded-land', { timeout: 15000 });
export const getGeology = () => api.get('/api/geology', { timeout: 15000 });

// ============ COMMUNITY ============
export const getCommunity = () => api.get('/api/community', { timeout: 15000 });
export const getRoads = () => api.get('/api/community/roads', { timeout: 15000 });

// ============ INFRASTRUCTURE ============
export const getSubstations = () => api.get('/api/substations', { timeout: 15000 });
export const getTransmissionLines = () => api.get('/api/transmission-lines', { timeout: 15000 });

// ============ TERRAIN ============
export const getDEM = () => api.get('/api/dem', { timeout: 15000 });

// ============ LAND COVER ============
export const getLandCover = () => api.get('/api/landcover', { timeout: 15000 });

// ============ PROTECTED AREAS ============
export const getProtectedAreas = () => api.get('/api/protected-areas', { timeout: 15000 });

// ============ CLIMATE ============
export const getClimateProjections = (years = 5) =>
  api.get(`/api/climate/projections?years=${years}`, { timeout: 15000 });
export const getClimateScenarios = () => api.get('/api/climate/scenarios', { timeout: 15000 });

// ============ TRENDS ============
export const getHistoricalTrend = () => api.get('/api/trend/historical', { timeout: 15000 });
export const getFutureTrend = (years = 5) =>
  api.get(`/api/trend/future?years=${years}`, { timeout: 15000 });
export const getFullTrend = (years = 5) =>
  api.get(`/api/trend/full?years=${years}`, { timeout: 15000 });

// ============ COMPREHENSIVE ============
export const getComprehensiveRecommendation = (years = 5) =>
  api.get(`/api/comprehensive-recommendation?years=${years}`, { timeout: 60000 });
export const getAllData = () => api.get('/api/all-data', { timeout: 60000 });

export default api;
