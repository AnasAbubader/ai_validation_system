// src/components/Settings/ProofSettings.jsx
import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { updateProofSettings } from '../../services/api';

function ProofSettings() {
  const [proofThreshold, setProofThreshold] = useState(5);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await updateProofSettings(proofThreshold);
      toast.success('Settings updated successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update settings');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg p-6 rounded-xl shadow-xl border border-white/10">
      <h2 className="text-xl font-semibold mb-4 text-white">Proof Generation Settings</h2>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-purple-200 mb-2">
            Proof Generation Threshold
          </label>
          <input
            type="number"
            min="1"
            value={proofThreshold}
            onChange={(e) => setProofThreshold(parseInt(e.target.value))}
            className="mt-1 block w-full px-3 py-2 text-white bg-white/10 border border-purple-300/20 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        <button
          type="submit"
          disabled={isLoading}
          className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-all duration-200"
        >
          {isLoading ? 'Updating...' : 'Update Settings'}
        </button>
      </form>
    </div>
  );
}

export default ProofSettings;