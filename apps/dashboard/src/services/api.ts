import { User, TouristProfile, Trip, SystemHealth, GeoZone, ZoneEvent, LiveTouristPosition } from '../types';

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

  // Geospatial & Real-time (Authority)
  getActiveTourists: async (): Promise<LiveTouristPosition[]> => {
    const res = await fetch(`${API_BASE}/location/active`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  getTripHistory: async (tripId: string): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/location/history/${tripId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  listZones: async (): Promise<GeoZone[]> => {
    const res = await fetch(`${API_BASE}/zones`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  createZone: async (data: { name: string; description?: string; zone_type: string; coordinates: [number, number][] }): Promise<GeoZone> => {
    const res = await fetch(`${API_BASE}/zones`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  deleteZone: async (id: string): Promise<void> => {
    const res = await fetch(`${API_BASE}/zones/${id}`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    if (!res.ok) {
      throw new Error(`Failed to delete zone with status ${res.status}`);
    }
  },

  listZoneEvents: async (limit = 50): Promise<ZoneEvent[]> => {
    const res = await fetch(`${API_BASE}/zones/events?limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  // Risk Engine (v0.3)
  getCurrentRisk: async (touristId: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/risk/current/${touristId}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  getTripRiskHistory: async (tripId: string, limit = 50): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/risk/history/${tripId}?limit=${limit}`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },

  getActiveRiskSnapshot: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/risk/active`, {
      headers: getAuthHeaders(),
    });
    return handleResponse(res);
  },
};


