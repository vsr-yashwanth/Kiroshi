import React, { useState } from 'react';
import { LiveTouristPosition, GeoZone } from '../types';
import { GoogleMapView } from './GoogleMapView';
import { AlertTriangle, Radio } from 'lucide-react';

interface LiveMonitoringMapProps {
  tourists: LiveTouristPosition[];
  zones: GeoZone[];
  selectedTouristId: string | null;
  onSelectTourist: (touristId: string | null) => void;
  tripHistory?: { latitude: number; longitude: number }[];
  onInspectRisk?: (tourist: LiveTouristPosition) => void;
}

export const LiveMonitoringMap: React.FC<LiveMonitoringMapProps> = ({
  tourists,
  zones,
  selectedTouristId,
  onSelectTourist,
  tripHistory = [],
  onInspectRisk,
}) => {
  const [mapMode, setMapMode] = useState<'google' | 'tactical'>('google');

  return (
    <div className="relative w-full h-[620px] rounded-2xl overflow-hidden flex flex-col shadow-2xl">
      {/* Top Map Bar with View Toggle */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700/60 shadow-lg text-xs font-mono text-slate-300">
        <div className="flex items-center gap-1.5 text-cyan-400 font-semibold">
          <Radio className="w-3.5 h-3.5" />
          <span>GIS Telemetry</span>
        </div>
        <span className="text-slate-600">|</span>
        <button
          onClick={() => setMapMode((m) => (m === 'google' ? 'tactical' : 'google'))}
          className="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 transition-colors"
        >
          {mapMode === 'google' ? 'Google Maps Mode' : 'Tactical Vector Mode'}
        </button>
      </div>

      {/* Top Right Legend */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-3 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700/60 shadow-lg text-xs text-slate-300">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Live</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>Recent</span>
        </div>
        <span className="text-slate-600">|</span>
        <div className="flex items-center gap-1.5 text-rose-400">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Danger Zone</span>
        </div>
      </div>

      {/* Main Map View */}
      <GoogleMapView
        tourists={tourists}
        zones={zones}
        selectedTouristId={selectedTouristId}
        onSelectTourist={onSelectTourist}
        tripHistory={tripHistory}
        onInspectRisk={onInspectRisk}
      />
    </div>
  );
};
