import React, { useEffect, useState } from 'react';
import { X, MapPin, Calendar } from 'lucide-react';
import { api } from '../services/api';
import { Trip } from '../types';
import { Badge } from './Badge';
import { LoadingSpinner } from './LoadingSpinner';

interface TripDetailModalProps {
  tripId: string;
  onClose: () => void;
  onTripUpdated?: () => void;
}

export const TripDetailModal: React.FC<TripDetailModalProps> = ({ tripId, onClose, onTripUpdated }) => {
  const [trip, setTrip] = useState<Trip | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [stopping, setStopping] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const loadTrip = () => {
    setLoading(true);
    api.getTrip(tripId)
      .then(setTrip)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTrip();
  }, [tripId]);

  const handleStopTrip = async () => {
    if (!confirm('Are you sure you want to mark this active trip as concluded?')) return;
    setStopping(true);
    try {
      await api.stopTrip(tripId);
      loadTrip();
      if (onTripUpdated) onTripUpdated();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setStopping(false);
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
        backdropFilter: 'blur(6px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 50,
        padding: '1rem',
      }}
      onClick={onClose}
    >
      <div
        className="glass-card"
        style={{
          width: '100%',
          maxWidth: '650px',
          background: '#0f1422',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          padding: '2rem',
          maxHeight: '90vh',
          overflowY: 'auto',
          position: 'relative',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '1.25rem',
            right: '1.25rem',
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
          }}
        >
          <X size={20} />
        </button>

        {loading ? (
          <LoadingSpinner message="Loading trip trajectory..." />
        ) : error ? (
          <div style={{ padding: '1.5rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px' }}>
            {error}
          </div>
        ) : trip ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', paddingRight: '2rem', marginBottom: '1rem' }}>
              <div>
                <h3 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#ffffff' }}>{trip.title}</h3>
                <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  {trip.description || 'No journey notes provided'}
                </p>
              </div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <Badge status={trip.status} />
                <Badge status={trip.emergency_status} type="emergency" />
              </div>
            </div>

            <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '1.5rem', padding: '0.75rem 1rem', background: 'rgba(255, 255, 255, 0.02)', borderRadius: '8px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                <Calendar size={14} /> Start: {new Date(trip.start_date).toLocaleDateString()}
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
                <Calendar size={14} /> End: {new Date(trip.end_date).toLocaleDateString()}
              </div>
            </div>

            <h4 style={{ fontSize: '0.9375rem', fontWeight: 600, color: '#ffffff', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <MapPin size={16} color="var(--primary)" /> Planned Waypoints ({trip.itineraries.length})
            </h4>

            {trip.itineraries.length === 0 ? (
              <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '1rem 0' }}>
                No itinerary waypoints registered for this trip.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1.5rem' }}>
                {trip.itineraries.map((waypoint) => (
                  <div
                    key={waypoint.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '0.75rem 1rem',
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderRadius: '6px',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span style={{ width: '24px', height: '24px', borderRadius: '50%', background: 'var(--primary-glow)', color: 'var(--primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 700 }}>
                        {waypoint.sequence_order}
                      </span>
                      <span style={{ fontWeight: 600, fontSize: '0.875rem' }}>{waypoint.destination_name}</span>
                    </div>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
                      {waypoint.latitude.toFixed(4)}°, {waypoint.longitude.toFixed(4)}°
                    </span>
                  </div>
                ))}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
              {trip.status === 'ACTIVE' ? (
                <button
                  className="btn-secondary"
                  style={{ color: '#ef4444', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                  onClick={handleStopTrip}
                  disabled={stopping}
                >
                  {stopping ? 'Concluding...' : 'Conclude Trip'}
                </button>
              ) : <div />}
              <button className="btn-secondary" onClick={onClose}>Close</button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
