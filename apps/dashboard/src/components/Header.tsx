import React, { useEffect, useState } from 'react';
import { Server } from 'lucide-react';
import { api } from '../services/api';
import { SystemHealth } from '../types';

import { Breadcrumbs } from './Breadcrumbs';

interface HeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: { label: string; tabId?: string }[];
  onNavigate?: (tabId: string) => void;
}

export const Header: React.FC<HeaderProps> = ({ title, subtitle, breadcrumbs, onNavigate }) => {
  const [health, setHealth] = useState<SystemHealth | null>(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => null);
    const interval = setInterval(() => {
      api.getHealth().then(setHealth).catch(() => null);
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const isHealthy = health?.status === 'healthy';

  return (
    <header
      style={{
        padding: '1.25rem 2rem',
        borderBottom: '1px solid var(--border-color)',
        background: 'rgba(11, 15, 25, 0.7)',
        backdropFilter: 'blur(8px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}
    >
      <div>
        {breadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumbs items={breadcrumbs} onNavigate={onNavigate} />
        )}
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>{title}</h1>
        {subtitle && <p style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>{subtitle}</p>}
      </div>

      {/* Backend Health Badge */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.6rem',
          padding: '0.4rem 0.85rem',
          borderRadius: '9999px',
          background: isHealthy ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)',
          border: `1px solid ${isHealthy ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.25)'}`,
        }}
      >
        <Server size={14} color={isHealthy ? '#10b981' : '#ef4444'} />
        <span style={{ fontSize: '0.8125rem', fontWeight: 500, color: isHealthy ? '#10b981' : '#ef4444' }}>
          Backend: {health ? `${health.status} (v${health.version})` : 'connecting...'}
        </span>
        <span
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isHealthy ? '#10b981' : '#ef4444',
            boxShadow: isHealthy ? '0 0 8px #10b981' : '0 0 8px #ef4444',
          }}
        />
      </div>
    </header>
  );
};
