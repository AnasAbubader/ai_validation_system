// src/components/Dashboard/Dashboard.jsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import ImageUpload from '../ImageUpload/ImageUpload';
import ProofSettings from '../Settings/ProofSettings';
import ProofStats from '../Stats/ProofStats';

function Dashboard() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-indigo-900 to-purple-900">
      <nav className="bg-black/30 backdrop-blur-lg border-b border-white/10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-xl font-semibold text-white">AI Validation Dashboard</h1>
          <button
            onClick={handleLogout}
            className="px-4 py-2 text-sm text-red-400 hover:text-red-300 transition-colors duration-200"
          >
            Logout
          </button>
        </div>
      </nav>
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
          <div className="space-y-8">
            <ImageUpload />
            <ProofSettings />
          </div>
          <div>
            <ProofStats />
          </div>
        </div>
      </main>
    </div>
  );
}

export default Dashboard;