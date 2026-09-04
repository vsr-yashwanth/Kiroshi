import React, { useEffect, useState } from 'react';
import { Compass, Eye, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { Trip } from '../types';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

interface TripsPageProps {
  onSelectTrip: (tripId: string) => void;
}

export const TripsPage: React.FC<TripsPageProps> = ({ onSelectTrip }) => {
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('ALL');

  const loadTrips = () => {
    setLoading(true);
    const filter = statusFilter === 'ALL' ? undefined : statusFilter;
    api.listTrips(filter)
      .then(setTrips)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTrips();
  }, [statusFilter]);

  const filterOptions = ['ALL', 'ACTIVE', 'PLANNED', 'COMPLETED'];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Filter Tabs & Refresh */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: '0.5rem', background: 'rgba(15, 20, 34, 0.6)', padding: '0.25rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
          {filterOptions.map((opt) => (
            <button
              key={opt}
              onClick={() => setStatusFilter(opt)}
              style={{
                background: statusFilter === opt ? 'var(--primary)' : 'transparent',
                color: statusFilter === opt ? '#ffffff' : 'var(--text-secondary)',
                border: 'none',
                borderRadius: '6px',
                padding: '0.45rem 1rem',
                fontSize: '0.8125rem',
                fontWeight: 600,
                cursor: 'pointer',
                transition: 'all 0.15s ease',
              }}
            >
              {opt}
            </button>
          ))}
        </div>

        <button className="btn-secondary" onClick={loadTrips} title="Refresh trips">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Trips Table */}
      {loading ? (
        <LoadingSpinner message="Polling trip registry..." />
      ) : trips.length === 0 ? (
        <EmptyState
          title="No Trips Found"
          description={`No trips match the status filter "${statusFilter}".`}
          icon={Compass}
        />
      ) : (
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Trip Expedition</th>
                <th>Trip Status</th>
                <th>Safety Status</th>
                <th>Waypoints</th>
                <th>Scheduled Dates</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {trips.map((trip) => (
                <tr key={trip.id}>
                  <td>
                    <p style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{trip.title}</p>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      {trip.description ? trip.description.slice(0, 50) + (trip.description.length > 50 ? '...' : '') : 'No description'}
                    </p>
                  </td>
                  <td>
                    <Badge status={trip.status} />
                  </td>
                  <td>
                    <Badge status={trip.emergency_status} type="emergency" />
                  </td>
                  <td>
                    <span style={{ fontSize: '0.8125rem', fontWeight: 600 }}>{trip.itineraries.length} waypoints</span>
                  </td>
                  <td>
                    <div style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                      {new Date(trip.start_date).toLocaleDateString()} — {new Date(trip.end_date).toLocaleDateString()}
                    </div>
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn-secondary"
                      onClick={() => onSelectTrip(trip.id)}
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.8125rem' }}
                    >
                      <Eye size={14} /> View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
