// src/services/api.js
import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create axios instance with auth header
const axiosInstance = axios.create({
  baseURL: API_URL,
});

// Add auth token to requests if it exists
axiosInstance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth APIs
export const loginUser = async (credentials) => {
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const response = await axiosInstance.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

export const registerUser = async (userData) => {
  try {
    const response = await axiosInstance.post('/auth/register', {
      username: userData.username,
      email: userData.email,
      password: userData.password
    }, {
      headers: {
        'Content-Type': 'application/json'
      },
    });
    return response.data;
  } catch (error) {
    console.error('Registration error:', {
      status: error.response?.status,
      data: error.response?.data,
      details: error.response?.data?.detail
    });
    throw error;
  }
};

// Image Processing API
export const processImage = async (image, modelType) => {
  const formData = new FormData();
  formData.append('image', image);
  formData.append('model_type', modelType);

  const response = await axiosInstance.post('/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

// Settings API
export const updateProofSettings = async (proofThreshold) => {
  const response = await axiosInstance.post(`/settings?proof_threshold=${proofThreshold}`);
  return response.data;
};

// Stats API
export const getProofStats = async () => {
  const response = await axiosInstance.get('/stats');
  return response.data;
};