import React, { useState, useEffect } from 'react'
import axios from 'axios'
import Map from './components/Map'

function App() {
  const [apiStatus, setApiStatus] = useState('Checking...')
  const [showMap, setShowMap] = useState(false)

  useEffect(() => {
    axios.get('http://localhost:8000/health')
      .then(response => {
        setApiStatus('Connected ✅')
      })
      .catch(error => {
        setApiStatus('Disconnected ❌')
      })
  }, [])

  return (
    <div className="min-h-screen bg-gray-100">
      <nav className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-3 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-800">
            🏔️ MineLand Nexus
          </h1>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-600">
              API: {apiStatus}
            </span>
            <button 
              onClick={() => setShowMap(!showMap)}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              {showMap ? 'Hide Map' : 'Show Map'}
            </button>
          </div>
        </div>
      </nav>

      <div className="container mx-auto p-4">
        <div className="bg-white rounded-lg shadow-md p-6 mb-4">
          <h2 className="text-xl font-semibold mb-2">
            🌍 Sishen/Kathu Analysis
          </h2>
          <p className="text-gray-600">
            AI and IoT Solutions for Rural Mining Landscapes and Renewable Energy
          </p>
          <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-green-50 p-4 rounded-lg">
              <h3 className="font-semibold">Satellite Data</h3>
              <p className="text-sm text-gray-600">Sentinel-2, Sentinel-1, Sentinel-5P</p>
              <p className="text-xs text-gray-500">Copernicus Data Space</p>
            </div>
            <div className="bg-yellow-50 p-4 rounded-lg">
              <h3 className="font-semibold">Solar Assessment</h3>
              <p className="text-sm text-gray-600">NASA POWER API</p>
              <p className="text-xs text-gray-500">Solar + Weather Data</p>
            </div>
            <div className="bg-red-50 p-4 rounded-lg">
              <h3 className="font-semibold">Mining Data</h3>
              <p className="text-sm text-gray-600">DPME GIS Service</p>
              <p className="text-xs text-gray-500">Mining Areas + Geology</p>
            </div>
          </div>
        </div>

        {showMap && (
          <div className="bg-white rounded-lg shadow-md overflow-hidden" style={{ height: '600px' }}>
            <Map />
          </div>
        )}
      </div>
    </div>
  )
}

export default App