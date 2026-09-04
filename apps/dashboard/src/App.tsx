import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { LoginPage } from './pages/LoginPage';
import { DashboardOverview } from './pages/DashboardOverview';
import { TouristsPage } from './pages/TouristsPage';
import { TripsPage } from './pages/TripsPage';
import { TouristDetailModal } from './components/TouristDetailModal';
import { TripDetailModal } from './components/TripDetailModal';
import { LoadingSpinner } from './components/LoadingSpinner';

const DashboardContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [currentTab, setCurrentTab] = useState<string>('overview');
  const [selectedTouristId, setSelectedTouristId] = useState<string | null>(null);
  const [selectedTripId, setSelectedTripId] = useState<string | null>(null);

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

  const getPageTitle = () => {
    switch (currentTab) {
      case 'overview':
        return { title: 'Operational Command Overview', subtitle: 'Real-time tourist safety monitoring and incident posture' };
      case 'tourists':
        return { title: 'Registered Tourist Directory', subtitle: 'Verified traveler safety profiles and emergency contacts' };
      case 'trips':
        return { title: 'Active Trips & Expeditions Fleet', subtitle: 'Track ongoing routes and itinerary waypoint compliance' };
      default:
        return { title: 'Command Center', subtitle: '' };
    }
  };

  const { title, subtitle } = getPageTitle();

  return (
    <div className="dashboard-layout">
      <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} />

      <main className="main-content">
        <Header title={title} subtitle={subtitle} />

        <div className="page-container">
          {currentTab === 'overview' && (
            <DashboardOverview
              onNavigate={setCurrentTab}
              onSelectTourist={setSelectedTouristId}
              onSelectTrip={setSelectedTripId}
            />
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
