import { User, TouristProfile, Trip, SystemHealth } from '../types';

const API_BASE = '/api/v1';

function getAuthHeaders(): HeadersInit {
  const token = localStorage.getItem('kiroshi_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `Request failed with status ${response.status}`);
  }
  return response.json();
}

export const api = {
  // Auth
  login: async (username: string, password: string): Promise<{ access_token: string; user: User }> => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(res);
  },

  getMe: async (): Promise<User> => {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // Health
  getHealth: async (): Promise<SystemHealth> => {
    const res = await fetch(`${API_BASE}/health`);
    return handleResponse(res);
  },

  // Tourists (Authority)
  listTourists: async (): Promise<User[]> => {
    const res = await fetch(`${API_BASE}/tourists`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  getTouristProfile: async (id: string): Promise<TouristProfile> => {
    const res = await fetch(`${API_BASE}/tourists/${id}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // Trips (Authority)
  listTrips: async (status?: string): Promise<Trip[]> => {
    const url = status ? `${API_BASE}/trips?status=${status}` : `${API_BASE}/trips`;
    const res = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  getTrip: async (id: string): Promise<Trip> => {
    const res = await fetch(`${API_BASE}/trips/${id}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  stopTrip: async (id: string): Promise<Trip> => {
    const res = await fetch(`${API_BASE}/trips/${id}/stop`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },
};
