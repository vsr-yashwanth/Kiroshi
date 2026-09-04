import React from 'react';
import { Shield, Users, Compass, Activity, LogOut, Radio, AlertTriangle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

interface SidebarProps {
  currentTab: string;
  onTabChange: (tab: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentTab, onTabChange }) => {
  const { logout, user } = useAuth();

  const navItems = [
    { id: 'overview', label: 'Command Overview', icon: Activity },
    { id: 'incidents', label: 'Emergency Incidents', icon: AlertTriangle },
    { id: 'monitoring', label: 'Live Geospatial Map', icon: Radio },
    { id: 'tourists', label: 'Registered Tourists', icon: Users },
    { id: 'trips', label: 'Active Trips Fleet', icon: Compass },
  ];

  return (
    <aside className="sidebar">
      {/* Brand Header */}
      <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(239, 68, 68, 0.4)'
        }}>
          <Shield size={20} color="#ffffff" />
        </div>
        <div>
          <h2 style={{ fontSize: '1.125rem', fontWeight: 700, letterSpacing: '0.05em', color: '#ffffff' }}>KIROSHI</h2>
          <span style={{ fontSize: '0.7rem', color: '#f87171', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>Authority v0.4</span>
        </div>
      </div>

      {/* Navigation Links */}
      <nav aria-label="Main Navigation" style={{ flex: 1, padding: '1.25rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = currentTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              aria-current={isActive ? 'page' : undefined}
              aria-label={`Navigate to ${item.label}`}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                width: '100%',
                padding: '0.75rem 1rem',
                borderRadius: '8px',
                border: 'none',
                background: isActive ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
                color: isActive ? '#ffffff' : 'var(--text-secondary)',
                fontWeight: isActive ? 600 : 500,
                fontSize: '0.875rem',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                textAlign: 'left',
              }}
            >
              <Icon size={18} color={isActive ? '#818cf8' : 'currentColor'} />
              <span>{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* User Session & Logout Footer */}
      <div style={{ padding: '1.25rem', borderTop: '1px solid var(--border-color)', background: 'rgba(0, 0, 0, 0.2)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ overflow: 'hidden' }}>
            <p style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-primary)', whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
              {user?.full_name}
            </p>
            <span style={{ fontSize: '0.75rem', color: '#10b981', display: 'inline-flex', alignItems: 'center', gap: '0.25rem' }}>
              ● {user?.role}
            </span>
          </div>
          <button
            onClick={logout}
            title="Logout"
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              padding: '0.5rem',
              borderRadius: '6px',
            }}
          >
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </aside>
  );
};
