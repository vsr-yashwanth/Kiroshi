import React from 'react';
import { ChevronRight, Home } from 'lucide-react';

interface BreadcrumbsProps {
  items: { label: string; tabId?: string }[];
  onNavigate?: (tabId: string) => void;
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items, onNavigate }) => {
  return (
    <nav aria-label="Breadcrumb" style={{ marginBottom: '0.5rem' }}>
      <ol style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', listStyle: 'none', padding: 0, margin: 0, fontSize: '0.8125rem' }}>
        <li style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <button
            onClick={() => onNavigate && onNavigate('overview')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-muted)',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
              padding: 0,
              fontSize: 'inherit',
              transition: 'color 0.15s ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
          >
            <Home size={13} />
            <span>HQ</span>
          </button>
        </li>

        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <React.Fragment key={idx}>
              <li style={{ color: 'var(--text-muted)', display: 'flex', alignItems: 'center' }}>
                <ChevronRight size={13} />
              </li>
              <li style={{ display: 'flex', alignItems: 'center' }}>
                {isLast || !item.tabId ? (
                  <span
                    aria-current={isLast ? 'page' : undefined}
                    style={{
                      color: isLast ? 'var(--text-primary)' : 'var(--text-secondary)',
                      fontWeight: isLast ? 600 : 400,
                    }}
                  >
                    {item.label}
                  </span>
                ) : (
                  <button
                    onClick={() => onNavigate && item.tabId && onNavigate(item.tabId)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: 'var(--text-secondary)',
                      cursor: 'pointer',
                      padding: 0,
                      fontSize: 'inherit',
                    }}
                    onMouseEnter={(e) => (e.currentTarget.style.color = '#ef4444')}
                    onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-secondary)')}
                  >
                    {item.label}
                  </button>
                )}
              </li>
            </React.Fragment>
          );
        })}
      </ol>
    </nav>
  );
};
