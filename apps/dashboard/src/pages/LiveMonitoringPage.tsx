import React, { useState, useEffect } from 'react';
import { useLiveStream } from '../services/useLiveStream';
import { api } from '../services/api';
import { GeoZone, GeoZoneType, LiveTouristPosition } from '../types';
import { LiveMonitoringMap } from '../components/LiveMonitoringMap';
import { RiskInspectorModal } from '../components/RiskInspectorModal';
import { Radio, Shield, AlertTriangle, Clock, Activity, Plus, RefreshCw, X, CheckCircle2, ShieldAlert, ChevronRight } from 'lucide-react';

export const LiveMonitoringPage: React.FC = () => {
  const { connected, tourists, recentEvents } = useLiveStream();
  const [zones, setZones] = useState<GeoZone[]>([]);
  const [, setLoadingZones] = useState(true);
  const [selectedTouristId, setSelectedTouristId] = useState<string | null>(null);
  const [inspectingTourist, setInspectingTourist] = useState<LiveTouristPosition | null>(null);
  const [tripHistory, setTripHistory] = useState<{ latitude: number; longitude: number }[]>([]);
  const [activeTab, setActiveTab] = useState<'tourists' | 'zones' | 'alerts'>('tourists');
  const [showZoneModal, setShowZoneModal] = useState(false);

  // New zone form state
  const [newZoneName, setNewZoneName] = useState('');
  const [newZoneDesc, setNewZoneDesc] = useState('');
  const [newZoneType, setNewZoneType] = useState<GeoZoneType>('SAFE');
  const [newZoneCoords, setNewZoneCoords] = useState('[[135.0, 35.0], [135.2, 35.0], [135.2, 35.2], [135.0, 35.2], [135.0, 35.0]]');
  const [zoneError, setZoneError] = useState<string | null>(null);
  const [submittingZone, setSubmittingZone] = useState(false);

  const fetchZones = async () => {
    try {
      setLoadingZones(true);
      const data = await api.listZones();
      setZones(data);
    } catch (err) {
      console.error('Failed to load geozones:', err);
    } finally {
      setLoadingZones(false);
    }
  };

  useEffect(() => {
    fetchZones();
  }, []);

  // Fetch route breadcrumb history when a tourist is selected
  useEffect(() => {
    if (!selectedTouristId) {
      setTripHistory([]);
      return;
    }
    const tourist = tourists.find((t) => t.tourist_id === selectedTouristId);
    if (!tourist) return;

    api.getTripHistory(tourist.trip_id)
      .then((history) => {
        setTripHistory(history.map((h) => ({ latitude: h.latitude, longitude: h.longitude })));
      })
      .catch((err) => console.error('Failed to load trip history:', err));
  }, [selectedTouristId, tourists]);

  const handleCreateZone = async (e: React.FormEvent) => {
    e.preventDefault();
    setZoneError(null);
    setSubmittingZone(true);

    try {
      let parsedCoords: [number, number][];
      try {
        parsedCoords = JSON.parse(newZoneCoords);
      } catch {
        throw new Error('Coordinates must be valid JSON array of [lng, lat] pairs.');
      }

      await api.createZone({
        name: newZoneName,
        description: newZoneDesc || undefined,
        zone_type: newZoneType,
        coordinates: parsedCoords,
      });

      setShowZoneModal(false);
      setNewZoneName('');
      setNewZoneDesc('');
      await fetchZones();
    } catch (err: any) {
      setZoneError(err.message || 'Failed to create GeoZone');
    } finally {
      setSubmittingZone(false);
    }
  };

  const handleDeleteZone = async (id: string) => {
    if (!window.confirm('Are you sure you want to deactivate this GeoZone?')) return;
    try {
      await api.deleteZone(id);
      await fetchZones();
    } catch (err: any) {
      alert(err.message || 'Failed to delete zone');
    }
  };

  const liveCount = tourists.filter((t) => t.freshness === 'LIVE').length;
  const recentCount = tourists.filter((t) => t.freshness === 'RECENT').length;
  const staleCount = tourists.filter((t) => t.freshness === 'STALE').length;

  return (
    <div className="space-y-6">
      {/* Real-time Header & Status Ribbon */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900/60 p-4 rounded-2xl border border-slate-800">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2.5">
            <Radio className="w-5 h-5 text-cyan-400" />
            Live Geospatial Command & Observation
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time PostGIS observation stream, autonomous geofence state-transition detection, and telemetry tracking.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-mono font-medium ${
              connected
                ? 'bg-emerald-950/60 text-emerald-400 border-emerald-800/80 shadow-[0_0_12px_rgba(16,185,129,0.2)]'
                : 'bg-rose-950/60 text-rose-400 border-rose-800/80 shadow-[0_0_12px_rgba(239,68,68,0.2)]'
            }`}
          >
            <span className={`w-2.5 h-2.5 rounded-full ${connected ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span>{connected ? 'WEBSOCKET STREAM ACTIVE' : 'RECONNECTING STREAM...'}</span>
          </div>

          <button
            onClick={fetchZones}
            className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition-colors"
            title="Refresh GeoZones"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Freshness & Metric Badges */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-medium">LIVE TRANSMITTERS</span>
            <div className="text-xl font-bold text-emerald-400 font-mono mt-0.5">{liveCount}</div>
          </div>
          <span className="w-3 h-3 rounded-full bg-emerald-500/80 animate-ping" />
        </div>

        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-medium">RECENT TRANSMITTERS</span>
            <div className="text-xl font-bold text-amber-400 font-mono mt-0.5">{recentCount}</div>
          </div>
          <Clock className="w-4 h-4 text-amber-500" />
        </div>

        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-medium">STALE TRANSMITTERS</span>
            <div className="text-xl font-bold text-slate-400 font-mono mt-0.5">{staleCount}</div>
          </div>
          <Activity className="w-4 h-4 text-slate-500" />
        </div>

        <div className="bg-slate-900/80 p-3 rounded-xl border border-slate-800 flex items-center justify-between">
          <div>
            <span className="text-slate-400 text-xs font-medium">MONITORED GEOZONES</span>
            <div className="text-xl font-bold text-cyan-400 font-mono mt-0.5">{zones.length}</div>
          </div>
          <Shield className="w-4 h-4 text-cyan-400" />
        </div>
      </div>

      {/* Main Grid: Live GIS Map (Left) & Telemetry Sidebar (Right) */}
      <div className="monitoring-grid">
        {/* Map Center Area */}
        <div>
          <LiveMonitoringMap
            tourists={tourists}
            zones={zones}
            selectedTouristId={selectedTouristId}
            onSelectTourist={setSelectedTouristId}
            tripHistory={tripHistory}
            onInspectRisk={(t) => setInspectingTourist(t)}
          />
        </div>

        {/* Telemetry & Events Right Panel */}
        <div className="bg-slate-900/80 rounded-2xl border border-slate-800 flex flex-col h-[620px] overflow-hidden">
          {/* Panel Tabs */}
          <div className="flex border-b border-slate-800 bg-slate-950/40 p-1">
            <button
              onClick={() => setActiveTab('tourists')}
              className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors ${
                activeTab === 'tourists'
                  ? 'bg-slate-800 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Travelers ({tourists.length})
            </button>
            <button
              onClick={() => setActiveTab('zones')}
              className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors ${
                activeTab === 'zones'
                  ? 'bg-slate-800 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Safety Zones ({zones.length})
            </button>
            <button
              onClick={() => setActiveTab('alerts')}
              className={`flex-1 py-2 text-xs font-medium rounded-lg transition-colors flex items-center justify-center gap-1 ${
                activeTab === 'alerts'
                  ? 'bg-slate-800 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Alerts
              {recentEvents.length > 0 && (
                <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
              )}
            </button>
          </div>

          {/* Tab Content Container */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* Tab 1: Active Tourists */}
            {activeTab === 'tourists' && (
              <div className="space-y-2.5">
                {tourists.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-sm">
                    No active tourist telemetry received yet.
                  </div>
                ) : (
                  tourists.map((t) => {
                    const isSelected = t.tourist_id === selectedTouristId;
                    const getRiskBadge = (lvl?: string) => {
                      switch (lvl) {
                        case 'CRITICAL':
                          return 'bg-red-950 text-red-400 border-red-800 animate-pulse';
                        case 'HIGH':
                          return 'bg-amber-950 text-amber-400 border-amber-800';
                        case 'MEDIUM':
                          return 'bg-yellow-950 text-yellow-400 border-yellow-800';
                        case 'LOW':
                          return 'bg-blue-950 text-blue-400 border-blue-800';
                        case 'SAFE':
                        default:
                          return 'bg-emerald-950 text-emerald-400 border-emerald-800';
                      }
                    };

                    return (
                      <div
                        key={t.tourist_id}
                        onClick={() => setSelectedTouristId(isSelected ? null : t.tourist_id)}
                        className={`p-3 rounded-xl border transition-all cursor-pointer ${
                          isSelected
                            ? 'bg-cyan-950/30 border-cyan-500/80 shadow-[0_0_12px_rgba(6,182,212,0.15)]'
                            : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="font-semibold text-white text-sm">{t.tourist_name}</span>
                          <span
                            className={`text-[10px] font-mono px-2 py-0.5 rounded-full border ${
                              t.freshness === 'LIVE'
                                ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                                : t.freshness === 'RECENT'
                                ? 'bg-amber-950 text-amber-400 border-amber-800'
                                : 'bg-slate-800 text-slate-400 border-slate-700'
                            }`}
                          >
                            {t.freshness}
                          </span>
                        </div>
                        <div className="text-xs text-slate-400 truncate mb-2">{t.trip_title}</div>

                        <div className="flex items-center justify-between text-[11px] font-mono text-slate-400 bg-slate-900/90 px-2.5 py-1.5 rounded-lg border border-slate-800/80">
                          <span>{t.latitude.toFixed(4)}, {t.longitude.toFixed(4)}</span>
                          <span>{t.speed != null ? `${t.speed.toFixed(1)} m/s` : '0 m/s'}</span>
                        </div>

                        {t.active_zones.length > 0 && (
                          <div className="mt-2 flex items-center gap-1.5 text-xs text-rose-400 font-medium">
                            <AlertTriangle className="w-3.5 h-3.5" />
                            <span>In: {t.active_zones.join(', ')}</span>
                          </div>
                        )}

                        {/* Risk Engine Assessment Ribbon */}
                        <div className="mt-2.5 pt-2 border-t border-slate-800/80 flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <ShieldAlert className="w-3.5 h-3.5 text-slate-400" />
                            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-semibold ${getRiskBadge(t.risk_level)}`}>
                              {t.risk_level || 'SAFE'} {t.risk_score != null ? `(${(t.risk_score * 100).toFixed(0)}%)` : ''}
                            </span>
                          </div>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setInspectingTourist(t);
                            }}
                            className="text-[11px] text-cyan-400 hover:text-cyan-300 flex items-center gap-0.5 transition-colors font-medium hover:underline"
                          >
                            Explain Risk <ChevronRight className="w-3 h-3" />
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            {/* Tab 2: Safety Zones */}
            {activeTab === 'zones' && (
              <div className="space-y-3">
                <button
                  onClick={() => setShowZoneModal(true)}
                  className="w-full py-2 px-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-semibold flex items-center justify-center gap-2 transition-colors shadow-lg shadow-cyan-950"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Configure New GeoZone
                </button>

                {zones.map((zone) => (
                  <div
                    key={zone.id}
                    className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-semibold text-white text-sm">{zone.name}</span>
                      <span
                        className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
                          zone.zone_type === 'SAFE'
                            ? 'bg-emerald-950 text-emerald-400 border-emerald-800'
                            : zone.zone_type === 'RESTRICTED'
                            ? 'bg-amber-950 text-amber-400 border-amber-800'
                            : zone.zone_type === 'HIGH_RISK'
                            ? 'bg-rose-950 text-rose-400 border-rose-800'
                            : 'bg-purple-950 text-purple-400 border-purple-800'
                        }`}
                      >
                        {zone.zone_type}
                      </span>
                    </div>
                    {zone.description && (
                      <p className="text-xs text-slate-400 mb-2">{zone.description}</p>
                    )}
                    <div className="flex items-center justify-between pt-2 border-t border-slate-900 text-xs">
                      <span className="text-[11px] font-mono text-slate-500">
                        {zone.coordinates.length} Vertices
                      </span>
                      <button
                        onClick={() => handleDeleteZone(zone.id)}
                        className="text-rose-400 hover:text-rose-300 font-medium text-xs transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Tab 3: Real-time Alerts */}
            {activeTab === 'alerts' && (
              <div className="space-y-2">
                {recentEvents.length === 0 ? (
                  <div className="text-center py-12 text-slate-500 text-sm">
                    No GeoZone transition alerts detected.
                  </div>
                ) : (
                  recentEvents.map((ev) => (
                    <div
                      key={ev.id}
                      className={`p-3 rounded-xl border ${
                        ev.event_type === 'ENTER'
                          ? 'bg-rose-950/20 border-rose-800/60 text-rose-300'
                          : 'bg-slate-950/80 border-slate-800 text-slate-300'
                      }`}
                    >
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="font-bold flex items-center gap-1.5">
                          {ev.event_type === 'ENTER' ? (
                            <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
                          ) : (
                            <CheckCircle2 className="w-3.5 h-3.5 text-slate-400" />
                          )}
                          ZONE {ev.event_type}
                        </span>
                        <span className="font-mono text-[10px] text-slate-500">
                          {new Date(ev.occurred_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-xs font-semibold text-white">{ev.zone_name}</p>
                      <p className="text-[11px] text-slate-400 mt-0.5">Traveler: {ev.tourist_id.slice(0, 8)}...</p>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* New GeoZone Configuration Modal */}
      {showZoneModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <Shield className="w-5 h-5 text-cyan-400" />
                Configure GeoZone Polygon
              </h3>
              <button
                onClick={() => setShowZoneModal(false)}
                className="p-1 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {zoneError && (
              <div className="p-3 bg-rose-950/60 border border-rose-800 rounded-xl text-xs text-rose-300">
                {zoneError}
              </div>
            )}

            <form onSubmit={handleCreateZone} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Zone Name</label>
                <input
                  type="text"
                  required
                  value={newZoneName}
                  onChange={(e) => setNewZoneName(e.target.value)}
                  placeholder="e.g. Kyoto Historic Quarter"
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Zone Classification</label>
                <select
                  value={newZoneType}
                  onChange={(e) => setNewZoneType(e.target.value as GeoZoneType)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="SAFE">SAFE (Safe Tourist Haven)</option>
                  <option value="RESTRICTED">RESTRICTED (Permit or Curfew Required)</option>
                  <option value="HIGH_RISK">HIGH_RISK (Natural / Terrain Hazard)</option>
                  <option value="CUSTOM">CUSTOM (Special Event / Monitored)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Description (Optional)</label>
                <textarea
                  value={newZoneDesc}
                  onChange={(e) => setNewZoneDesc(e.target.value)}
                  placeholder="Notes about hazards, emergency contacts, or special guidance..."
                  rows={2}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">
                  Linear Ring Coordinates JSON: <code className="text-cyan-400">[[lng, lat], ...]</code>
                </label>
                <textarea
                  value={newZoneCoords}
                  onChange={(e) => setNewZoneCoords(e.target.value)}
                  rows={3}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-cyan-300 focus:outline-none focus:border-cyan-500"
                />
                <span className="text-[11px] text-slate-500 block mt-1">
                  Must be closed polygon (first point matches last point) in WGS 84 [longitude, latitude].
                </span>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowZoneModal(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-medium transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingZone}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-sm font-semibold transition-colors disabled:opacity-50"
                >
                  {submittingZone ? 'Saving...' : 'Deploy Zone'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Risk Assessment & Model Explainability Modal */}
      {inspectingTourist && (
        <RiskInspectorModal
          tourist={inspectingTourist}
          onClose={() => setInspectingTourist(null)}
        />
      )}
    </div>
  );
};
