// src/components/ImageUpload/ImageUpload.jsx
import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { processImage } from '../../services/api';

function ImageUpload() {
  const [file, setFile] = useState(null);
  const [modelType, setModelType] = useState('resnet18');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) {
      toast.error('Please select an image');
      return;
    }

    setLoading(true);
    try {
      const response = await processImage(file, modelType);
      setResult(response);
      toast.success('Image processed successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to process image');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg p-6 rounded-xl shadow-xl border border-white/10">
      <h2 className="text-xl font-semibold mb-4 text-white">Process Image</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-purple-200 mb-2">
            Select Model
          </label>
          <select
            value={modelType}
            onChange={(e) => setModelType(e.target.value)}
            className="mt-1 block w-full pl-3 pr-10 py-2 text-white bg-white/10 border border-purple-300/20 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value="resnet18">ResNet-18</option>
            <option value="resnet34">ResNet-34</option>
          </select>
        </div>
        
        <div>
          <label className="block text-sm font-medium text-purple-200 mb-2">
            Upload Image
          </label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files[0])}
            className="mt-1 block w-full text-purple-200 
                       file:mr-4 file:py-2 file:px-4
                       file:rounded-lg file:border-0
                       file:text-sm file:font-semibold
                       file:bg-purple-600 file:text-white
                       hover:file:bg-purple-700
                       file:cursor-pointer file:transition-colors"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-all duration-200"
        >
          {loading ? 'Processing...' : 'Process Image'}
        </button>
      </form>

      {result && (
        <div className="mt-4">
          <h3 className="text-lg font-medium text-white mb-2">Result:</h3>
          <pre className="mt-2 bg-black/30 p-4 rounded-lg overflow-auto text-purple-200">
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default ImageUpload;