// src/components/Auth/Register.jsx
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'react-toastify';
import { registerUser } from '../../services/api';

function Register() {
  const navigate = useNavigate();
  const [userData, setUserData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    try {
      await registerUser(userData);
      toast.success('Registration successful! Please login.');
      navigate('/login');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-900 via-purple-900 to-blue-900">
      {/* AI Circuit Background Pattern */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <svg width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="circuit-pattern" x="0" y="0" width="100" height="100" patternUnits="userSpaceOnUse">
              <circle cx="50" cy="50" r="1" fill="rgba(255,255,255,0.3)"/>
              <path d="M50 0 L50 100 M0 50 L100 50" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5"/>
              <path d="M50 50 L75 75 M50 50 L25 75" stroke="rgba(255,255,255,0.1)" strokeWidth="0.5"/>
              <circle cx="75" cy="75" r="1" fill="rgba(255,255,255,0.2)"/>
              <circle cx="25" cy="75" r="1" fill="rgba(255,255,255,0.2)"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#circuit-pattern)"/>
          
          {/* Animated Circuit Nodes */}
          <circle cx="30%" cy="20%" r="120" fill="rgba(79,70,229,0.1)">
            <animate attributeName="r" from="120" to="150" dur="5s" repeatCount="indefinite"/>
          </circle>
          <circle cx="70%" cy="80%" r="180" fill="rgba(147,51,234,0.1)">
            <animate attributeName="r" from="180" to="220" dur="7s" repeatCount="indefinite"/>
          </circle>
        </svg>
      </div>

      <div className="max-w-md w-full space-y-8 p-8 bg-white/10 backdrop-blur-lg rounded-xl shadow-2xl relative z-10">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-white mb-2">Create Account</h2>
          <p className="text-purple-200">Join our AI validation platform</p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <input
              type="text"
              required
              className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-purple-300/20 bg-white/10 placeholder-purple-200 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Username"
              value={userData.username}
              onChange={(e) => setUserData({...userData, username: e.target.value})}
            />
          </div>
          <div>
            <input
              type="email"
              required
              className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-purple-300/20 bg-white/10 placeholder-purple-200 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Email address"
              value={userData.email}
              onChange={(e) => setUserData({...userData, email: e.target.value})}
            />
          </div>
          <div>
            <input
              type="password"
              required
              className="appearance-none rounded-lg relative block w-full px-3 py-2 border border-purple-300/20 bg-white/10 placeholder-purple-200 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
              placeholder="Password"
              value={userData.password}
              onChange={(e) => setUserData({...userData, password: e.target.value})}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading}
            className="w-full flex justify-center py-2 px-4 border border-transparent rounded-lg shadow-sm text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 transition-all duration-200"
          >
            {isLoading ? 'Creating Account...' : 'Register'}
          </button>
        </form>
        <div className="text-center mt-4">
          <p className="text-purple-200">Already have an account? <Link to="/login" className="text-white hover:text-purple-300 font-semibold">Login here</Link></p>
        </div>
      </div>
    </div>
  );
}

export default Register;