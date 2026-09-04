import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { LoginPage } from './pages/LoginPage';
import { DashboardOverview } from './pages/DashboardOverview';
import { TouristsPage } from './pages/TouristsPage';
import { TripsPage } from './pages/TripsPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { TouristDetailModal } from './components/TouristDetailModal';
import { TripDetailModal } from './components/TripDetailModal';
import { LoadingSpinner } from './components/LoadingSpinner';

import { NotFoundPage } from './pages/NotFoundPage';

const DashboardContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>(() => {
    const hash = window.location.hash.replace('#', '');
    return ['overview', 'incidents', 'monitoring', 'tourists', 'trips'].includes(hash) ? hash : 'overview';
  });
  const [selectedTouristId, setSelectedTouristId] = useState<string | null>(null);
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null);

  // Sync hash routing
  React.useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (['overview', 'incidents', 'monitoring', 'tourists', 'trips'].includes(hash)) {
        setCurrentTab(hash);
      }
    };
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleTabChange = (tab: string) => {
    setCurrentTab(tab);
    window.location.hash = tab;
  };

  // Dynamic document title update per view
  React.useEffect(() => {
    const tabTitles: Record<string, string> = {
      overview: 'Command Overview | KIROSHI Authority',
      incidents: 'Emergency Incidents & Response | KIROSHI Authority',
      monitoring: 'Live Geospatial Telemetry & GIS | KIROSHI Authority',
      tourists: 'Tourist Registry Directory | KIROSHI Authority',
      trips: 'Expedition Trips Fleet | KIROSHI Authority',
    };
    document.title = tabTitles[currentTab] || 'Command Center | KIROSHI Authority';
  }, [currentTab]);

  if (isLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingSpinner message="Validating secure authority session..." />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LoginPage />;
  }

  const getPageConfig = () => {
    switch (currentTab) {
      case 'overview':
        return {
          title: 'Operational Command Overview',
          subtitle: 'Real-time tourist safety monitoring and incident posture',
          breadcrumbs: [{ label: 'Command Center' }],
        };
      case 'incidents':
        return {
          title: 'Emergency Incidents & Response Operations',
          subtitle: 'Active emergency triage, verification, and responder dispatch queue',
          breadcrumbs: [{ label: 'Command', tabId: 'overview' }, { label: 'Emergency Incidents' }],
        };
      case 'monitoring':
        return {
          title: 'Live Geospatial Telemetry & GeoZones',
          subtitle: 'Real-time WebSocket observation, GIS containment tracking, and incident alerts',
          breadcrumbs: [{ label: 'Command', tabId: 'overview' }, { label: 'Live Telemetry' }],
        };
      case 'tourists':
        return {
          title: 'Registered Tourist Directory',
          subtitle: 'Verified traveler safety profiles and emergency contacts',
          breadcrumbs: [{ label: 'Registry', tabId: 'overview' }, { label: 'Tourists' }],
        };
      case 'trips':
        return {
          title: 'Active Trips & Expeditions Fleet',
          subtitle: 'Track ongoing routes and itinerary waypoint compliance',
          breadcrumbs: [{ label: 'Fleet', tabId: 'overview' }, { label: 'Active Trips' }],
        };
      default:
        return {
          title: '404 Not Found',
          subtitle: 'Unrecognized navigation sector',
          breadcrumbs: [{ label: 'Command', tabId: 'overview' }, { label: 'Not Found' }],
        };
    }
  };

  const { title, subtitle, breadcrumbs } = getPageConfig();
  const isKnownTab = ['overview', 'incidents', 'monitoring', 'tourists', 'trips'].includes(currentTab);

  return (
    <div className="dashboard-layout">
      <Sidebar currentTab={currentTab} onTabChange={handleTabChange} />

      <main className="main-content">
        <Header
          title={title}
          subtitle={subtitle}
          breadcrumbs={breadcrumbs}
          onNavigate={handleTabChange}
        />

        <div className="page-container">
          {!isKnownTab && (
            <NotFoundPage onReturnHome={() => handleTabChange('overview')} />
          )}

          {currentTab === 'overview' && (
            <DashboardOverview
              onNavigate={handleTabChange}
              onSelectTourist={setSelectedTouristId}
              onSelectTrip={setSelectedTripId}
            />
          )}

          {currentTab === 'incidents' && (
            <IncidentsPage />
          )}

          {currentTab === 'monitoring' && (
            <LiveMonitoringPage />
          )}

          {currentTab === 'tourists' && (
            <TouristsPage onSelectTourist={setSelectedTouristId} />
          )}

          {currentTab === 'trips' && (
            <TripsPage onSelectTrip={setSelectedTripId} />
          )}
        </div>
      </main>

      {/* Modals */}
      {selectedTouristId && (
        <TouristDetailModal
          userId={selectedTouristId}
          onClose={() => setSelectedTouristId(null)}
        />
      )}

      {selectedTripId && (
        <TripDetailModal
          tripId={selectedTripId}
          onClose={() => setSelectedTripId(null)}
          onTripUpdated={() => {
            // refresh active tab
          }}
        />
      )}
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <DashboardContent />
    </AuthProvider>
  );
};

export default App;
