import React from 'react';

interface BadgeProps {
  status: string;
  type?: 'status' | 'emergency';
}

export const Badge: React.FC<BadgeProps> = ({ status }) => {
  let className = 'badge badge-info';

  if (status === 'ACTIVE' || status === 'NORMAL' || status === 'COMPLETED') {
    className = 'badge badge-success';
  } else if (status === 'PLANNED' || status === 'AT_RISK') {
    className = 'badge badge-warning';
  } else if (status === 'CANCELLED' || status === 'SOS') {
    className = 'badge badge-danger';
  }

  return <span className={className}>{status}</span>;
};
