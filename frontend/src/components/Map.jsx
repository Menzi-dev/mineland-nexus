import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

function Map() {
  const mapContainer = useRef(null)
  const map = useRef(null)
  const [selectedDate, setSelectedDate] = useState('')
  const [ndviData, setNdviData] = useState(null)
  const [solarData, setSolarData] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (map.current) return

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [27.45, -23.45],
      zoom: 10
    })

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right')

    // Load mining areas after map loads
    map.current.on('load', () => {
      fetchMiningAreas()
    })

    return () => {
      map.current.remove()
    }
  }, [])

  const fetchMiningAreas = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/satellite/mining-areas')
      const data = response.data
      
      if (data.status === 'success' && data.data) {
        map.current.addSource('mining', {
          type: 'geojson',
          data: data.data
        })

        map.current.addLayer({
          id: 'mining-fill',
          type: 'fill',
          source: 'mining',
          paint: {
            'fill-color': '#FF6B35',
            'fill-opacity': 0.3,
            'fill-outline-color': '#FF4500'
          }
        })

        // Add labels
        map.current.addLayer({
          id: 'mining-line',
          type: 'line',
          source: 'mining',
          paint: {
            'line-color': '#FF4500',
            'line-width': 2
          }
        })
      }
    } catch (error) {
      console.error('Error fetching mining areas:', error)
    }
  }

  const fetchNDVI = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/satellite/ndvi')
      const data = response.data
      setNdviData(data)
      
      // Display NDVI data on map or as info
      if (data.status === 'success') {
        console.log('NDVI Data:', data)
      }
    } catch (error) {
      console.error('Error fetching NDVI:', error)
    }
    setLoading(false)
  }

  const fetchSolarData = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/satellite/solar')
      const data = response.data
      setSolarData(data)
      
      if (data.status === 'success') {
        console.log('Solar Data:', data)
      }
    } catch (error) {
      console.error('Error fetching solar data:', error)
    }
    setLoading(false)
  }

  const fetchCombinedAnalysis = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/satellite/combined-analysis')
      const data = response.data
      console.log('Combined Analysis:', data)
      
      if (data.status === 'success') {
        // Display analysis results
        alert(`Analysis Complete!\nNDVI Mean: ${data.ndvi?.ndvi_mean || 'N/A'}\nSolar Score: ${data.solar?.solar_suitability_score || 'N/A'}`)
      }
    } catch (error) {
      console.error('Error fetching combined analysis:', error)
    }
    setLoading(false)
  }

  return (
    <div className="w-full h-full relative">
      <div className="absolute top-4 left-4 z-10 bg-white rounded-lg shadow-md p-4">
        <h3 className="font-semibold mb-2">Sishen/Kathu Analysis</h3>
        <div className="space-y-2">
          <button 
            onClick={fetchNDVI}
            className="w-full bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Get NDVI'}
          </button>
          <button 
            onClick={fetchSolarData}
            className="w-full bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Get Solar Data'}
          </button>
          <button 
            onClick={fetchCombinedAnalysis}
            className="w-full bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Full Analysis'}
          </button>
        </div>
      </div>

      {ndviData && ndviData.status === 'success' && (
        <div className="absolute bottom-4 left-4 z-10 bg-white rounded-lg shadow-md p-4 max-w-sm">
          <h4 className="font-semibold">NDVI Analysis</h4>
          <p className="text-sm">Mean: {ndviData.ndvi_mean?.toFixed(3)}</p>
          <p className="text-sm">Min: {ndviData.ndvi_min?.toFixed(3)}</p>
          <p className="text-sm">Max: {ndviData.ndvi_max?.toFixed(3)}</p>
          <p className="text-xs text-gray-500">Date: {ndviData.date}</p>
        </div>
      )}

      {solarData && solarData.status === 'success' && (
        <div className="absolute bottom-4 right-4 z-10 bg-white rounded-lg shadow-md p-4 max-w-sm">
          <h4 className="font-semibold">Solar Assessment</h4>
          <p className="text-sm">Score: {solarData.solar_suitability_score}/100</p>
          <p className="text-sm">Mean Solar: {solarData.parameters?.ALLSKY_SFC_SW_DWN?.mean?.toFixed(2)} kWh/m²/day</p>
        </div>
      )}

      <div ref={mapContainer} className="w-full h-full" />
    </div>
  )
}

export default Map