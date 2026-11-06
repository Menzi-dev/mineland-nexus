import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { BarChart3, Circle, Database, MapPin, Pickaxe, RotateCcw, Satellite, Search, Zap } from 'lucide-react';
import { REFERENCE_MINE } from '../data/mineSite';

function Map() {
  const mapContainer = useRef(null);
  const map = useRef(null);
  const mapReady = useRef(false);
  const [loading, setLoading] = useState(true);
  const [mapStats, setMapStats] = useState({
    miningFeatures: 0,
    substations: 0
  });
  const [dataLayers, setDataLayers] = useState({
    mining: true,
    substations: true,
    studyArea: true
  });
  const [layerInfo, setLayerInfo] = useState({
    mining: 'Showing',
    substations: 'Showing',
    studyArea: 'Showing'
  });
  const [error, setError] = useState(null);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

  useEffect(() => {
    if (map.current) return;

    console.log('🗺️ Initializing map...');

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          satellite: {
            type: 'raster',
            tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
            tileSize: 256,
            attribution: 'Tiles © Esri'
          }
        },
        layers: [{ id: 'satellite', type: 'raster', source: 'satellite' }]
      },
      center: [REFERENCE_MINE.coordinates.lon, REFERENCE_MINE.coordinates.lat],
      zoom: 12
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');

    map.current.on('load', () => {
      console.log('✅ Map loaded!');
      mapReady.current = true;
      setLoading(false);
      addStudyArea();
      addReferenceMine();
      loadAllData();
    });

    map.current.on('error', (e) => {
      console.error('Map error:', e);
      if (!mapReady.current) {
        setError('Satellite imagery could not be loaded');
        setLoading(false);
      }
    });

    return () => {
      if (map.current) {
        map.current.remove();
        map.current = null;
      }
      mapReady.current = false;
    };
  }, []);

  const addStudyArea = () => {
    try {
      map.current.addSource('study-area', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [17.68, -29.88],
              [17.96, -29.88],
              [17.96, -29.66],
              [17.68, -29.66],
              [17.68, -29.88]
            ]]
          },
          properties: { name: 'Nababeep Northern Cape Study Area' }
        }
      });

      map.current.addLayer({
        id: 'study-area-fill',
        type: 'fill',
        source: 'study-area',
        paint: {
          'fill-color': '#3B82F6',
          'fill-opacity': 0.1,
          'fill-outline-color': '#3B82F6'
        }
      });

      map.current.addLayer({
        id: 'study-area-line',
        type: 'line',
        source: 'study-area',
        paint: {
          'line-color': '#3B82F6',
          'line-width': 2,
          'line-dasharray': [5, 5]
        }
      });

      console.log('✅ Study area added');
    } catch (e) {
      console.error('Error adding study area:', e);
    }
  };

  const addReferenceMine = () => {
    new maplibregl.Marker({ color: '#15803d' })
      .setLngLat([REFERENCE_MINE.coordinates.lon, REFERENCE_MINE.coordinates.lat])
      .setPopup(new maplibregl.Popup().setHTML(`<strong>${REFERENCE_MINE.name}</strong><br />Selected assessment site`))
      .addTo(map.current);
  };

  const loadAllData = async () => {
    await loadMiningData();
    await loadSubstationData();
  };

  const loadMiningData = async () => {
    try {
      console.log('⛏️ Fetching mining data...');
      const response = await axios.get(`${API_BASE}/api/mining-areas`);
      console.log('Mining response:', response.data);

      const data = response.data;

      // Handle different response formats
      let features = [];
      if (data.status === 'success') {
        if (data.data && data.data.features) {
          features = data.data.features;
        } else if (data.features) {
          features = data.features;
        }
      }

      if (features.length > 0) {
        setMapStats(prev => ({ ...prev, miningFeatures: features.length }));
        console.log(`✅ Found ${features.length} mining features`);

        const geojson = {
          type: 'FeatureCollection',
          features: features
        };

        map.current.addSource('mining', {
          type: 'geojson',
          data: geojson
        });

        map.current.addLayer({
          id: 'mining-fill',
          type: 'fill',
          source: 'mining',
          paint: {
            'fill-color': '#FF6B35',
            'fill-opacity': 0.4,
            'fill-outline-color': '#FF4500'
          }
        });

        map.current.addLayer({
          id: 'mining-line',
          type: 'line',
          source: 'mining',
          paint: {
            'line-color': '#FF4500',
            'line-width': 2
          }
        });

        setLayerInfo(prev => ({ ...prev, mining: 'Showing' }));
      } else {
        setLayerInfo(prev => ({ ...prev, mining: 'No data' }));
      }

    } catch (error) {
      console.error('Error loading mining data:', error);
      setLayerInfo(prev => ({ ...prev, mining: 'Unavailable' }));
    }
  };

  const addSampleMiningData = () => {
    try {
      const sampleFeatures = [
        {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [27.42, -23.48],
              [27.52, -23.48],
              [27.52, -23.42],
              [27.42, -23.42],
              [27.42, -23.48]
            ]]
          },
          properties: { name: 'Sishen Mine', type: 'mining' }
        },
        {
          type: 'Feature',
          geometry: {
            type: 'Polygon',
            coordinates: [[
              [27.35, -23.45],
              [27.40, -23.45],
              [27.40, -23.40],
              [27.35, -23.40],
              [27.35, -23.45]
            ]]
          },
          properties: { name: 'Kathu Mine', type: 'mining' }
        }
      ];

      setMapStats(prev => ({ ...prev, miningFeatures: sampleFeatures.length }));
      console.log(`✅ Added ${sampleFeatures.length} sample mining features`);

      map.current.addSource('mining', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: sampleFeatures
        }
      });

      map.current.addLayer({
        id: 'mining-fill',
        type: 'fill',
        source: 'mining',
        paint: {
          'fill-color': '#FF6B35',
          'fill-opacity': 0.4,
          'fill-outline-color': '#FF4500'
        }
      });

      map.current.addLayer({
        id: 'mining-line',
        type: 'line',
        source: 'mining',
        paint: {
          'line-color': '#FF4500',
          'line-width': 2
        }
      });

      setLayerInfo(prev => ({ ...prev, mining: 'Showing' }));

    } catch (e) {
      console.error('Error adding sample mining data:', e);
    }
  };

  const loadSubstationData = async () => {
    try {
      console.log('⚡ Fetching substation data...');
      const response = await axios.get(`${API_BASE}/api/substations`);
      console.log('Substation response:', response.data);

      const data = response.data;
      let substations = [];

      if (data.status === 'success' && data.substations) {
        substations = data.substations;
      }

      if (substations.length > 0) {
        setMapStats(prev => ({ ...prev, substations: substations.length }));
        console.log(`✅ Found ${substations.length} substations`);

        const features = substations.map((sub) => ({
          type: 'Feature',
          geometry: {
            type: 'Point',
            coordinates: [sub.coordinates?.lon || 27.45, sub.coordinates?.lat || -23.45]
          },
          properties: {
            name: sub.name || 'Substation',
            type: sub.type || 'Unknown'
          }
        }));

        const geojson = {
          type: 'FeatureCollection',
          features: features
        };

        map.current.addSource('substations', {
          type: 'geojson',
          data: geojson
        });

        map.current.addLayer({
          id: 'substations',
          type: 'circle',
          source: 'substations',
          paint: {
            'circle-radius': 10,
            'circle-color': '#FFD700',
            'circle-stroke-color': '#FF6B00',
            'circle-stroke-width': 2
          }
        });

        map.current.addLayer({
          id: 'substation-labels',
          type: 'symbol',
          source: 'substations',
          layout: {
            'text-field': ['get', 'name'],
            'text-size': 10,
            'text-offset': [0, 1.5]
          },
          paint: {
            'text-color': '#333'
          }
        });

        setLayerInfo(prev => ({ ...prev, substations: 'Showing' }));
      } else {
        setLayerInfo(prev => ({ ...prev, substations: 'No data' }));
      }

    } catch (error) {
      console.error('Error loading substation data:', error);
      setLayerInfo(prev => ({ ...prev, substations: 'Unavailable' }));
    }
  };

  const addSampleSubstationData = () => {
    try {
      const sampleSubstations = [
        { name: 'Sishen Substation', coordinates: { lat: -23.45, lon: 27.48 }, type: '132kV' },
        { name: 'Kathu Substation', coordinates: { lat: -23.43, lon: 27.52 }, type: '66kV' }
      ];

      setMapStats(prev => ({ ...prev, substations: sampleSubstations.length }));
      console.log(`✅ Added ${sampleSubstations.length} sample substations`);

      const features = sampleSubstations.map((sub) => ({
        type: 'Feature',
        geometry: {
          type: 'Point',
          coordinates: [sub.coordinates.lon, sub.coordinates.lat]
        },
        properties: {
          name: sub.name,
          type: sub.type
        }
      }));

      map.current.addSource('substations', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: features
        }
      });

      map.current.addLayer({
        id: 'substations',
        type: 'circle',
        source: 'substations',
        paint: {
          'circle-radius': 10,
          'circle-color': '#FFD700',
          'circle-stroke-color': '#FF6B00',
          'circle-stroke-width': 2
        }
      });

      map.current.addLayer({
        id: 'substation-labels',
        type: 'symbol',
        source: 'substations',
        layout: {
          'text-field': ['get', 'name'],
          'text-size': 10,
          'text-offset': [0, 1.5]
        },
        paint: {
          'text-color': '#333'
        }
      });

      setLayerInfo(prev => ({ ...prev, substations: 'Showing' }));

    } catch (e) {
      console.error('Error adding sample substations:', e);
    }
  };

  const toggleLayer = (layer) => {
    const newState = !dataLayers[layer];
    setDataLayers(prev => ({
      ...prev,
      [layer]: newState
    }));

    const layerMap = {
      mining: ['mining-fill', 'mining-line'],
      substations: ['substations', 'substation-labels'],
      studyArea: ['study-area-fill', 'study-area-line']
    };

    const layerIds = layerMap[layer] || [];
    layerIds.forEach(id => {
      if (map.current.getLayer(id)) {
        map.current.setLayoutProperty(
          id,
          'visibility',
          newState ? 'visible' : 'none'
        );
      }
    });

    setLayerInfo(prev => ({
      ...prev,
      [layer]: newState ? 'Showing' : 'Hidden'
    }));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-4">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><Satellite size={20} aria-hidden="true" />Satellite Map - Nababeep</h2>

        {/* Layer Controls */}
        <div className="flex flex-wrap items-center gap-2 mb-3">
          <button
            onClick={() => toggleLayer('mining')}
            className={`inline-flex items-center justify-center gap-2 px-3 py-2 rounded text-xs font-medium whitespace-nowrap ${
              dataLayers.mining
                ? 'bg-orange-600 text-white hover:bg-orange-700'
                : 'bg-gray-300 text-gray-600'
            }`}
          >
            <Pickaxe size={16} aria-hidden="true" />Mining Areas ({layerInfo.mining})
          </button>
          <button
            onClick={() => toggleLayer('substations')}
            className={`inline-flex items-center justify-center gap-2 px-3 py-2 rounded text-xs font-medium whitespace-nowrap ${
              dataLayers.substations
                ? 'bg-yellow-600 text-white hover:bg-yellow-700'
                : 'bg-gray-300 text-gray-600'
            }`}
          >
            <Zap size={16} aria-hidden="true" />Substations ({layerInfo.substations})
          </button>
          <button
            onClick={() => toggleLayer('studyArea')}
            className={`inline-flex items-center justify-center gap-2 px-3 py-2 rounded text-xs font-medium whitespace-nowrap ${
              dataLayers.studyArea
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-600'
            }`}
          >
            <Circle size={16} aria-hidden="true" />Study Area ({layerInfo.studyArea})
          </button>
          <button
            onClick={() => {
              map.current.flyTo({
                center: [REFERENCE_MINE.coordinates.lon, REFERENCE_MINE.coordinates.lat],
                zoom: 12,
                duration: 2000
              });
            }}
            className="inline-flex items-center justify-center gap-2 bg-gray-600 text-white px-3 py-2 rounded text-xs font-medium whitespace-nowrap hover:bg-gray-700"
          >
            <RotateCcw size={16} aria-hidden="true" />Reset View
          </button>
          <button
            onClick={() => {
              map.current.flyTo({
                center: [REFERENCE_MINE.coordinates.lon, REFERENCE_MINE.coordinates.lat],
                zoom: 15,
                duration: 2000
              });
            }}
            className="inline-flex items-center justify-center gap-2 bg-green-600 text-white px-3 py-2 rounded text-xs font-medium whitespace-nowrap hover:bg-green-700"
          >
            <Search size={16} aria-hidden="true" />Zoom to Mining Area
          </button>
          <button
            onClick={() => {
              map.current.flyTo({
                center: [REFERENCE_MINE.coordinates.lon, REFERENCE_MINE.coordinates.lat],
                zoom: 12,
                duration: 2000
              });
            }}
            className="inline-flex items-center justify-center gap-2 bg-green-700 text-white px-3 py-2 rounded text-xs font-medium whitespace-nowrap hover:bg-green-800"
          >
            <MapPin size={16} aria-hidden="true" />View Selected Mine
          </button>
        </div>

        {/* Info Banner */}
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-2.5 mb-3 text-xs text-gray-600">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <span className="inline-flex items-center gap-1"><MapPin size={14} aria-hidden="true" /><span className="font-semibold">Nababeep - Northern Cape</span></span>
            <span className="inline-flex items-center gap-1"><Circle size={14} className="text-green-500" aria-hidden="true" /><span className="font-semibold">{REFERENCE_MINE.name}</span></span>
            <span className="inline-flex items-center gap-1"><Pickaxe size={14} className="text-orange-500" aria-hidden="true" />{mapStats.miningFeatures} Mining Areas</span>
            <span className="inline-flex items-center gap-1"><Zap size={14} className="text-yellow-500" aria-hidden="true" />{mapStats.substations} Substations</span>
            <span className="text-xs text-gray-400">Satellite imagery · Click layer buttons to toggle visibility</span>
          </div>
          {error && (
            <div className="text-red-500 text-xs mt-1">{error}</div>
          )}
        </div>

        {/* Map */}
        <div className="relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-white z-10 rounded-lg">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
              <span className="ml-3 text-gray-600">Loading map...</span>
            </div>
          )}
          <div ref={mapContainer} className="w-full h-[420px] rounded-lg border" />
        </div>

        {/* Legend */}
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
          <div className="inline-flex items-center gap-2">
            <span className="w-4 h-4 bg-orange-500 rounded"></span>
            <span>Mining Areas</span>
          </div>
          <div className="inline-flex items-center gap-2">
            <span className="w-4 h-4 bg-yellow-500 rounded-full"></span>
            <span>Substations</span>
          </div>
          <div className="inline-flex items-center gap-2">
            <span className="w-4 h-4 bg-blue-500 rounded border border-blue-700 border-dashed"></span>
            <span>Study Area</span>
          </div>
          <div className="inline-flex items-center gap-2 text-xs text-gray-500">
            <span className="inline-flex items-center gap-1"><Satellite size={14} aria-hidden="true" />Satellite imagery: Esri World Imagery · Data: Northern Cape assessment sources</span>
          </div>
        </div>
      </div>

      {/* Map Data Summary */}
      <div className="bg-white rounded-lg shadow-lg p-4">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><BarChart3 size={18} aria-hidden="true" />Map Data Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-orange-50 p-4 rounded-lg border border-orange-200 text-center">
            <div className="text-2xl font-bold text-orange-600">{mapStats.miningFeatures}</div>
            <div className="text-sm text-gray-600">Mining Areas</div>
          </div>
          <div className="bg-yellow-50 p-4 rounded-lg border border-yellow-200 text-center">
            <div className="text-2xl font-bold text-yellow-600">{mapStats.substations}</div>
            <div className="text-sm text-gray-600">Substations</div>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200 text-center">
            <div className="text-2xl font-bold text-blue-600">1</div>
            <div className="text-sm text-gray-600">Study Area</div>
          </div>
          <div className="bg-green-50 p-4 rounded-lg border border-green-200 text-center">
            <div className="text-2xl font-bold text-green-600">9</div>
            <div className="text-sm text-gray-600">Data Sources</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Map;
