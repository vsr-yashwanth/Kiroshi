export type UserRole = 'TOURIST' | 'AUTHORITY' | 'RESPONDER' | 'ADMIN';
export type TripStatus = 'PLANNED' | 'ACTIVE' | 'COMPLETED' | 'CANCELLED';
export type EmergencyStatus = 'NORMAL' | 'AT_RISK' | 'SOS';

export interface User {
  id: string;
  email: string;
  full_name: string;
  phone_number?: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TouristProfile {
  id: string;
  user_id: string;
  nationality?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  medical_notes?: string;
  consent_given: boolean;
  created_at: string;
  updated_at: string;
  user?: User;
}

export interface Itinerary {
  id: string;
  trip_id: string;
  destination_name: string;
  planned_arrival?: string;
  planned_departure?: string;
  latitude: number;
  longitude: number;
  sequence_order: number;
}

export interface Trip {
  id: string;
  tourist_id: string;
  title: string;
  description?: string;
  start_date: string;
  end_date: string;
  status: TripStatus;
  emergency_status: EmergencyStatus;
  created_at: string;
  updated_at: string;
  tourist?: User;
  itineraries: Itinerary[];
}

export interface SystemHealth {
  status: string;
  environment: string;
  database: string;
  version: string;
}

export type GeoZoneType = 'SAFE' | 'RESTRICTED' | 'HIGH_RISK' | 'CUSTOM';
export type ZoneEventType = 'ENTER' | 'EXIT';
export type LocationFreshness = 'LIVE' | 'RECENT' | 'STALE' | 'UNKNOWN';

export interface GeoZone {
  id: string;
  name: string;
  description?: string;
  zone_type: GeoZoneType;
  coordinates: [number, number][];
  is_active: boolean;
  created_at: string;
}

export interface ZoneEvent {
  id: string;
  tourist_id: string;
  trip_id: string;
  zone_id: string;
  zone_name?: string;
  zone_type?: GeoZoneType;
  event_type: ZoneEventType;
  occurred_at: string;
}

export interface LiveTouristPosition {
  tourist_id: string;
  tourist_name: string;
  trip_id: string;
  trip_title: string;
  latitude: number;
  longitude: number;
  accuracy: number;
  altitude?: number;
  speed?: number;
  heading?: number;
  freshness: LocationFreshness;
  recorded_at: string;
  received_at: string;
  active_zones: string[];
}

