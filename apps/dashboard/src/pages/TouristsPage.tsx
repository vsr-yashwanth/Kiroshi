import React, { useEffect, useState } from 'react';
import { Search, Eye, Users, RefreshCw } from 'lucide-react';
import { api } from '../services/api';
import { User } from '../types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

interface TouristsPageProps {
  onSelectTourist: (userId: string) => void;
}

export const TouristsPage: React.FC<TouristsPageProps> = ({ onSelectTourist }) => {
  const [tourists, setTourists] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const loadTourists = () => {
    setLoading(true);
    api.listTourists()
      .then(setTourists)
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTourists();
  }, []);

  const filtered = tourists.filter(
    (t) =>
      t.full_name.toLowerCase().includes(search.toLowerCase()) ||
      t.email.toLowerCase().includes(search.toLowerCase()) ||
      (t.phone_number && t.phone_number.includes(search))
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Search & Actions Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
        <div style={{ position: 'relative', width: '100%', maxWidth: '400px' }}>
          <input
            type="text"
            className="input-field"
            placeholder="Search travelers by name, email, or phone..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ paddingLeft: '2.5rem' }}
          />
          <Search size={16} color="var(--text-muted)" style={{ position: 'absolute', left: '0.875rem', top: '50%', transform: 'translateY(-50%)' }} />
        </div>
        <button className="btn-secondary" onClick={loadTourists} title="Refresh records">
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Table Content */}
      {loading ? (
        <LoadingSpinner message="Querying verified tourist database..." />
      ) : filtered.length === 0 ? (
        <EmptyState
          title="No Tourists Found"
          description={search ? `No travelers match the query "${search}".` : "No tourist records found in the database."}
          icon={Users}
        />
      ) : (
        <div className="data-table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Traveler Name</th>
                <th>Email Address</th>
                <th>Phone Number</th>
                <th>Account Status</th>
                <th>Registered Date</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((t) => (
                <tr key={t.id}>
                  <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{t.full_name}</td>
                  <td>{t.email}</td>
                  <td>{t.phone_number || '—'}</td>
                  <td>
                    <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: t.is_active ? '#10b981' : '#94a3b8', fontSize: '0.8125rem' }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: t.is_active ? '#10b981' : '#94a3b8' }} />
                      {t.is_active ? 'Active' : 'Suspended'}
                    </span>
                  </td>
                  <td>{new Date(t.created_at).toLocaleDateString()}</td>
                  <td style={{ textAlign: 'right' }}>
                    <button
                      className="btn-secondary"
                      onClick={() => onSelectTourist(t.id)}
                      style={{ padding: '0.35rem 0.75rem', fontSize: '0.8125rem' }}
                    >
                      <Eye size={14} /> Inspect
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
