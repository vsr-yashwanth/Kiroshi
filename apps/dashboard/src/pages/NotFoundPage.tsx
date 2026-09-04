import React from 'react';
import { AlertOctagon, ArrowLeft, ShieldAlert } from 'lucide-react';

interface NotFoundPageProps {
  onReturnHome: () => void;
}

export const NotFoundPage: React.FC<NotFoundPageProps> = ({ onReturnHome }) => {
  return (
    <main
      role="main"
      style={{
        minHeight: '70vh',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        padding: '2rem',
      }}
    >
      <div
        style={{
          width: '80px',
          height: '80px',
          borderRadius: '24px',
          background: 'rgba(239, 68, 68, 0.12)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: '1.5rem',
          boxShadow: '0 0 30px rgba(239, 68, 68, 0.25)',
        }}
      >
        <ShieldAlert size={42} color="#ef4444" />
      </div>

      <h1
        style={{
          fontSize: '2.5rem',
          fontWeight: 800,
          color: 'var(--text-primary)',
          letterSpacing: '-0.02em',
          marginBottom: '0.5rem',
        }}
      >
        404 — Sector Coordinates Out of Range
      </h1>

      <p
        style={{
          maxWidth: '520px',
          fontSize: '1rem',
          color: 'var(--text-secondary)',
          lineHeight: 1.6,
          marginBottom: '2rem',
        }}
      >
        The requested tactical view, sector telemetry stream, or incident perimeter is unmapped or unavailable in the KIROSHI command registry.
      </p>

      <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <button
          onClick={onReturnHome}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.75rem 1.5rem',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
            color: '#ffffff',
            border: 'none',
            fontWeight: 600,
            fontSize: '0.9375rem',
            cursor: 'pointer',
            boxShadow: '0 4px 14px rgba(239, 68, 68, 0.3)',
            transition: 'transform 0.15s ease, box-shadow 0.15s ease',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.transform = 'translateY(-1px)')}
          onMouseLeave={(e) => (e.currentTarget.style.transform = 'translateY(0)')}
        >
          <ArrowLeft size={16} />
          <span>Return to Command Center</span>
        </button>
      </div>

      <div
        style={{
          marginTop: '3rem',
          padding: '0.75rem 1.25rem',
          borderRadius: '8px',
          background: 'rgba(255, 255, 255, 0.03)',
          border: '1px solid var(--border-color)',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
          fontSize: '0.8125rem',
          color: 'var(--text-muted)',
        }}
      >
        <AlertOctagon size={14} color="#f59e0b" />
        <span>Incident dispatch and live risk streams remain operational on active channels.</span>
      </div>
    </main>
  );
};
