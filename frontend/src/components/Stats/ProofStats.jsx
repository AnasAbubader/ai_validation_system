// src/components/Stats/ProofStats.jsx
import React, { useState, useEffect } from 'react';
import { getProofStats } from '../../services/api';

function ProofStats() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await getProofStats();
        setStats(response);
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="bg-white/10 backdrop-blur-lg p-6 rounded-xl shadow-xl border border-white/10">
        <h2 className="text-xl font-semibold mb-4 text-white">Proof Statistics</h2>
        <div className="text-purple-200">Loading...</div>
      </div>
    );
  }

  return (
    <div className="bg-white/10 backdrop-blur-lg p-6 rounded-xl shadow-xl border border-white/10">
      <h2 className="text-xl font-semibold mb-6 text-white">Proof Statistics</h2>
      {stats && (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          <div className="bg-black/30 p-4 rounded-lg">
            <p className="text-sm text-purple-200">Total Proofs</p>
            <p className="text-2xl font-semibold text-white mt-1">{stats.total_proofs}</p>
          </div>
          <div className="bg-black/30 p-4 rounded-lg">
            <p className="text-sm text-purple-200">Successful Proofs</p>
            <p className="text-2xl font-semibold text-white mt-1">{stats.successful_proofs}</p>
          </div>
          <div className="bg-black/30 p-4 rounded-lg">
            <p className="text-sm text-purple-200">Failed Proofs</p>
            <p className="text-2xl font-semibold text-white mt-1">{stats.failed_proofs}</p>
          </div>
          <div className="bg-black/30 p-4 rounded-lg">
            <p className="text-sm text-purple-200">Proof Threshold</p>
            <p className="text-2xl font-semibold text-white mt-1">{stats.threshold}</p>
          </div>
          {stats.success_percentage !== undefined && (
            <div className="bg-black/30 p-4 rounded-lg sm:col-span-2">
              <p className="text-sm text-purple-200">Success Rate</p>
              <div className="mt-2 relative">
                <div className="h-4 bg-gray-700 rounded-full">
                  <div 
                    className="h-4 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-full transition-all duration-500"
                    style={{ width: `${stats.success_percentage}%` }}
                  />
                </div>
                <p className="absolute right-0 top-6 text-white font-semibold">
                  {stats.success_percentage.toFixed(1)}%
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ProofStats;