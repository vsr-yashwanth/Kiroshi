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
