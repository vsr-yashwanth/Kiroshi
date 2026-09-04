import React, { useEffect, useState } from 'react';
import { Users, Compass, ShieldAlert, CheckCircle, ArrowUpRight } from 'lucide-react';
import { StatCard } from '../components/StatCard';
import { Badge } from '../components/Badge';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { api } from '../services/api';
import { User, Trip } from '../types';

interface DashboardOverviewProps {
  onNavigate: (tab: string) => void;
  onSelectTourist: (userId: string) => void;
  onSelectTrip: (tripId: string) => void;
}

export const DashboardOverview: React.FC<DashboardOverviewProps> = ({
  onNavigate,
  onSelectTourist,
  onSelectTrip,
}) => {
  const [tourists, setTourists] = useState<User[]>([]);
  const [trips, setTrips] = useState<Trip[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [touristsData, tripsData] = await Promise.all([
          api.listTourists().catch(() => []),
          api.listTrips().catch(() => []),
        ]);
        setTourists(touristsData);
        setTrips(tripsData);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <LoadingSpinner message="Aggregating operational metrics..." />;
  }

  const activeTrips = trips.filter((t) => t.status === 'ACTIVE');
  const plannedTrips = trips.filter((t) => t.status === 'PLANNED');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
      {/* Metric Cards Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.25rem' }}>
        <StatCard
          title="Active Journeys"
          value={activeTrips.length}
          change="Real-time monitoring active"
          icon={Compass}
          accentColor="#10b981"
        />
        <StatCard
          title="Registered Travelers"
          value={tourists.length}
          change="Verified digital profiles"
          icon={Users}
          accentColor="#6366f1"
        />
        <StatCard
          title="Planned Expeditions"
          value={plannedTrips.length}
          change="Scheduled departures"
          icon={CheckCircle}
          accentColor="#3b82f6"
        />
        <StatCard
          title="Safety Posture"
          value="NOMINAL"
          change="Zero active SOS signals"
          icon={ShieldAlert}
          accentColor="#8b5cf6"
        />
      </div>

      {/* Two Column Grid for Live Lists */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '1.5rem' }}>
        {/* Active Trips Monitor */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Active Trips Fleet</h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Currently traversing field waypoints</p>
            </div>
            <button
              className="btn-secondary"
              onClick={() => onNavigate('trips')}
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem' }}
            >
              View Fleet <ArrowUpRight size={14} />
            </button>
          </div>

          {activeTrips.length === 0 ? (
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>
              No trips currently in ACTIVE status.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {activeTrips.slice(0, 5).map((trip) => (
                <div
                  key={trip.id}
                  onClick={() => onSelectTrip(trip.id)}
                  style={{
                    padding: '0.875rem 1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    transition: 'border-color 0.15s ease',
                  }}
                >
                  <div>
                    <h4 style={{ fontSize: '0.9375rem', fontWeight: 600 }}>{trip.title}</h4>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      {trip.itineraries.length} waypoints registered
                    </p>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Badge status={trip.status} />
                    <Badge status={trip.emergency_status} type="emergency" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recently Registered Tourists */}
        <div className="glass-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
            <div>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 700 }}>Verified Tourists</h3>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>Registered travelers requiring oversight</p>
            </div>
            <button
              className="btn-secondary"
              onClick={() => onNavigate('tourists')}
              style={{ fontSize: '0.75rem', padding: '0.4rem 0.75rem' }}
            >
              View All <ArrowUpRight size={14} />
            </button>
          </div>

          {tourists.length === 0 ? (
            <p style={{ fontSize: '0.875rem', color: 'var(--text-muted)', textAlign: 'center', padding: '2rem 0' }}>
              No tourists registered yet.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {tourists.slice(0, 5).map((tourist) => (
                <div
                  key={tourist.id}
                  onClick={() => onSelectTourist(tourist.id)}
                  style={{
                    padding: '0.875rem 1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                  }}
                >
                  <div>
                    <h4 style={{ fontSize: '0.9375rem', fontWeight: 600 }}>{tourist.full_name}</h4>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '0.2rem' }}>
                      {tourist.email} {tourist.phone_number ? `• ${tourist.phone_number}` : ''}
                    </p>
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--primary)', fontWeight: 600 }}>
                    Inspect Profile →
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
