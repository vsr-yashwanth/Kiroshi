import React, { useEffect, useState } from 'react';
import { X, Phone, User as UserIcon, Heart } from 'lucide-react';
import { api } from '../services/api';
import { TouristProfile } from '../types';
import { LoadingSpinner } from './LoadingSpinner';

interface TouristDetailModalProps {
  userId: string;
  onClose: () => void;
}

export const TouristDetailModal: React.FC<TouristDetailModalProps> = ({ userId, onClose }) => {
  const [profile, setProfile] = useState<TouristProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    api.getTouristProfile(userId)
      .then(setProfile)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [userId]);

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
          maxWidth: '560px',
          background: '#0f1422',
          border: '1px solid rgba(255, 255, 255, 0.12)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
          padding: '2rem',
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

        <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#ffffff', display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
          <UserIcon size={20} color="var(--primary)" />
          Tourist Profile Details
        </h3>

        {loading ? (
          <LoadingSpinner message="Fetching verified profile records..." />
        ) : error ? (
          <div style={{ padding: '1.5rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '8px' }}>
            {error}
          </div>
        ) : profile ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.875rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Nationality</span>
                <p style={{ fontWeight: 600, marginTop: '0.25rem' }}>{profile.nationality || 'Unspecified'}</p>
              </div>

              <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '0.875rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Consent Status</span>
                <p style={{ fontWeight: 600, marginTop: '0.25rem', color: profile.consent_given ? '#10b981' : '#f59e0b' }}>
                  {profile.consent_given ? 'Verified Consent' : 'Pending Consent'}
                </p>
              </div>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <h4 style={{ fontSize: '0.875rem', color: '#818cf8', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                <Phone size={16} /> Next of Kin / Emergency Contact
              </h4>
              <p style={{ fontWeight: 600, fontSize: '0.9375rem' }}>{profile.emergency_contact_name || 'None listed'}</p>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-secondary)', marginTop: '0.2rem' }}>
                {profile.emergency_contact_phone || 'No telephone number provided'}
              </p>
            </div>

            <div style={{ background: 'rgba(255, 255, 255, 0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
              <h4 style={{ fontSize: '0.875rem', color: '#f59e0b', display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.5rem' }}>
                <Heart size={16} /> Critical Medical Notes
              </h4>
              <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                {profile.medical_notes || 'No critical allergies, medical conditions, or medications specified.'}
              </p>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
              <button className="btn-secondary" onClick={onClose}>Close</button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
};
