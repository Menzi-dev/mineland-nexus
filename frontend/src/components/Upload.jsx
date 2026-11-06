import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { CalendarDays, Camera, CheckCircle2, CircleAlert, FileImage, FolderOpen, MapPin, Trash2, UploadCloud, X } from 'lucide-react';
import { REFERENCE_MINE } from '../data/mineSite';

function Upload() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const fileInputRef = useRef(null);

  const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

  useEffect(() => {
    fetchUploadedFiles();
  }, []);

  const fetchUploadedFiles = async () => {
    try {
      const response = await axios.get(`${API_BASE}/api/uploads/files`);
      setUploadedFiles(response.data.files || []);
    } catch (err) {
      console.error('Failed to fetch uploads:', err);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
      setResult(null);
      setError(null);
      setSuccess(null);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setError(null);
    setSuccess(null);

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('site_id', REFERENCE_MINE.id);

    try {
      const response = await axios.post(`${API_BASE}/api/uploads/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      });
      setResult(response.data);
      setSuccess('Photo uploaded and analysed for the selected mine.');
      fetchUploadedFiles();
      console.log('Upload result:', response.data);
    } catch (err) {
      setError('Failed to upload file: ' + err.message);
      console.error(err);
    }
    setUploading(false);
  };

  const handleDelete = async (filename) => {
    try {
      await axios.delete(`${API_BASE}/api/uploads/files/${filename}`);
      setSuccess(`File '${filename}' deleted successfully`);
      fetchUploadedFiles();
    } catch (err) {
      setError('Failed to delete file: ' + err.message);
    }
  };

  const clearUpload = () => {
    setSelectedFile(null);
    setPreview(null);
    setResult(null);
    setError(null);
    setSuccess(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
  };

  return (
    <div className="space-y-6">
      {/* Upload Section */}
      <div className="bg-white rounded-lg shadow-lg p-5">
        <h2 className="text-xl font-bold mb-4 flex items-center gap-2"><UploadCloud size={20} aria-hidden="true" />Upload & Analyze Mining Images</h2>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
          <p className="text-xs uppercase tracking-wide text-green-700 font-semibold">Selected assessment site</p>
          <h3 className="text-lg font-bold text-gray-900 mt-1">{REFERENCE_MINE.name}</h3>
          <p className="text-sm text-gray-600">{REFERENCE_MINE.description}</p>
          <p className="text-xs text-gray-500 mt-2 flex items-center gap-1"><MapPin size={13} aria-hidden="true" />{REFERENCE_MINE.coordinates.lat}, {REFERENCE_MINE.coordinates.lon}</p>
          <a
            href={`https://www.openstreetmap.org/?mlat=${REFERENCE_MINE.coordinates.lat}&mlon=${REFERENCE_MINE.coordinates.lon}#map=13/${REFERENCE_MINE.coordinates.lat}/${REFERENCE_MINE.coordinates.lon}`}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-green-700 underline"
          >
            Open site in map
          </a>
          <p className="text-xs text-gray-500 mt-2">{REFERENCE_MINE.source}</p>
        </div>

        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4 text-sm text-blue-700">
          <p className="flex items-center gap-1"><Camera size={15} aria-hidden="true" />Upload a photo of the mining landscape for image analysis</p>
          <p className="text-xs text-blue-500 mt-1">Supports JPG, PNG, JPEG, WebP - Max 10MB</p>
          <p className="text-xs text-blue-500 flex items-center gap-1"><FolderOpen size={13} aria-hidden="true" />Files saved to: uploads/ folder</p>
        </div>

        {/* File Input */}
        <div className="mb-4">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
        </div>

        {/* Preview */}
        {preview && (
          <div className="mb-4">
            <div className="relative border rounded-lg overflow-hidden max-h-64 bg-gray-100">
              <img src={preview} alt="Selected" className="w-full object-contain max-h-64" />
            </div>
            <div className="flex flex-wrap gap-2 mt-2">
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
              >
                <UploadCloud size={16} aria-hidden="true" />{uploading ? 'Uploading...' : 'Upload & Analyze'}
              </button>
              <button
                onClick={clearUpload}
                disabled={uploading}
                className="bg-gray-500 text-white px-4 py-2 rounded hover:bg-gray-600 disabled:opacity-50"
              >
                <X size={16} aria-hidden="true" />Clear
              </button>
            </div>
          </div>
        )}

        {/* Uploading */}
        {uploading && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Uploading and analyzing...</span>
          </div>
        )}

        {/* Success */}
        {success && (
          <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-4">
            <CheckCircle2 size={16} className="inline mr-1" aria-hidden="true" />{success}
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <CircleAlert size={16} className="inline mr-1" aria-hidden="true" />{error}
          </div>
        )}

        {/* Result */}
        {result && result.status === 'success' && (
          <div className="bg-green-50 rounded-lg p-4 border border-green-200">
            <h4 className="text-lg font-semibold text-green-800 flex items-center gap-2"><CheckCircle2 size={18} aria-hidden="true" />Analysis Complete</h4>
            <div className="mt-2 space-y-1 text-sm">
              <p><span className="font-medium">Filename:</span> {result.filename}</p>
              <p><span className="font-medium">Size:</span> {formatFileSize(result.size)}</p>
              <p><span className="font-medium">Detected Features:</span></p>
              <ul className="list-disc pl-5 space-y-1">
                {result.features?.map((feature, idx) => (
                  <li key={idx}>{feature}</li>
                ))}
              </ul>
              {result.analysis?.dimensions && (
                <p><span className="font-medium">Image:</span> {result.analysis.dimensions.width} × {result.analysis.dimensions.height}px, brightness {Math.round(result.analysis.brightness * 100)}%</p>
              )}
              <p className="text-xs text-gray-500 mt-2">{result.analysis?.note}</p>
              <p className="text-xs text-gray-500 mt-2 flex items-center gap-1"><CalendarDays size={13} aria-hidden="true" />{new Date(result.timestamp).toLocaleString()}</p>
            </div>
          </div>
        )}

        {!preview && !uploading && !result && !success && !error && (
          <div className="text-center py-8 text-gray-500 border-2 border-dashed rounded-lg">
            <p className="text-lg flex items-center justify-center gap-2"><FileImage size={20} aria-hidden="true" />Drop an image here or click to browse</p>
            <p className="text-sm mt-2">Upload a photo of the mining landscape for AI analysis</p>
            <p className="text-xs text-gray-400 mt-1">Images will be saved to uploads/ folder</p>
          </div>
        )}
      </div>

      {/* Uploaded Files List */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><FolderOpen size={18} aria-hidden="true" />Uploaded Files ({uploadedFiles.length})</h3>

        {uploadedFiles.length === 0 ? (
          <div className="text-center py-4 text-gray-500">
            <p>No files uploaded yet</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50">
                <tr>
                  <th className="text-left p-2">Filename</th>
                  <th className="text-left p-2">Size</th>
                  <th className="text-left p-2">Modified</th>
                  <th className="text-left p-2">Action</th>
                </tr>
              </thead>
              <tbody>
                {uploadedFiles.map((file, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="p-2"><FileImage size={15} className="inline mr-1" aria-hidden="true" />{file.name}</td>
                    <td className="p-2">{formatFileSize(file.size)}</td>
                    <td className="p-2">{new Date(file.modified).toLocaleDateString()}</td>
                    <td className="p-2">
                      <button
                        onClick={() => handleDelete(file.name)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <Trash2 size={15} className="inline mr-1" aria-hidden="true" />Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default Upload;
