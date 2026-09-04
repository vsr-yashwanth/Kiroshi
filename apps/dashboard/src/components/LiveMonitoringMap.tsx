import React, { useState, useMemo } from 'react';
import { LiveTouristPosition, GeoZone, LocationFreshness } from '../types';
import { AlertTriangle, Layers, ZoomIn, ZoomOut, RotateCcw } from 'lucide-react';

interface LiveMonitoringMapProps {
  tourists: LiveTouristPosition[];
  zones: GeoZone[];
  selectedTouristId: string | null;
  onSelectTourist: (touristId: string | null) => void;
  tripHistory?: { latitude: number; longitude: number }[];
}

export const LiveMonitoringMap: React.FC<LiveMonitoringMapProps> = ({
  tourists,
  zones,
  selectedTouristId,
  onSelectTourist,
  tripHistory = [],
}) => {
  const [zoom, setZoom] = useState(1);
  const [centerOffset, setCenterOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Calculate bounding box of all points and zones to frame the map projection
  const bounds = useMemo(() => {
    let minLat = 90, maxLat = -90, minLng = 180, maxLng = -180;
    let hasPoints = false;

    tourists.forEach((t) => {
      minLat = Math.min(minLat, t.latitude);
      maxLat = Math.max(maxLat, t.latitude);
      minLng = Math.min(minLng, t.longitude);
      maxLng = Math.max(maxLng, t.longitude);
      hasPoints = true;
    });

    zones.forEach((z) => {
      z.coordinates.forEach(([lng, lat]) => {
        minLat = Math.min(minLat, lat);
        maxLat = Math.max(maxLat, lat);
        minLng = Math.min(minLng, lng);
        maxLng = Math.max(maxLng, lng);
        hasPoints = true;
      });
    });

    if (!hasPoints) {
      // Default to Kyoto / Tokyo region if empty
      return { minLat: 34.5, maxLat: 35.5, minLng: 135.0, maxLng: 136.0 };
    }

    const paddingLat = Math.max((maxLat - minLat) * 0.15, 0.02);
    const paddingLng = Math.max((maxLng - minLng) * 0.15, 0.02);

    return {
      minLat: minLat - paddingLat,
      maxLat: maxLat + paddingLat,
      minLng: minLng - paddingLng,
      maxLng: maxLng + paddingLng,
    };
  }, [tourists, zones]);

  // Coordinate projection from (lat, lng) to SVG viewBox [0, 1000] x [0, 700]
  const project = (lat: number, lng: number) => {
    const width = 1000;
    const height = 700;
    const x = ((lng - bounds.minLng) / (bounds.maxLng - bounds.minLng || 1)) * width;
    const y = ((bounds.maxLat - lat) / (bounds.maxLat - bounds.minLat || 1)) * height;
    return { x, y };
  };

  const getZoneColor = (type: string) => {
    switch (type) {
      case 'SAFE':
        return { fill: 'rgba(16, 185, 129, 0.18)', stroke: '#10b981' };
      case 'RESTRICTED':
        return { fill: 'rgba(245, 158, 11, 0.22)', stroke: '#f59e0b' };
      case 'HIGH_RISK':
        return { fill: 'rgba(239, 68, 68, 0.28)', stroke: '#ef4444' };
      case 'CUSTOM':
      default:
        return { fill: 'rgba(139, 92, 246, 0.2)', stroke: '#8b5cf6' };
    }
  };

  const getFreshnessColor = (freshness: LocationFreshness) => {
    switch (freshness) {
      case 'LIVE':
        return '#10b981';
      case 'RECENT':
        return '#f59e0b';
      case 'STALE':
      default:
        return '#64748b';
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - centerOffset.x, y: e.clientY - centerOffset.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setCenterOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  return (
    <div className="relative w-full h-[620px] bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden shadow-2xl flex flex-col select-none">
      {/* Map Control Toolbar */}
      <div className="absolute top-4 left-4 z-20 flex items-center gap-2 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700/60 shadow-lg text-xs font-mono text-slate-300">
        <div className="flex items-center gap-1.5">
          <Layers className="w-3.5 h-3.5 text-cyan-400" />
          <span>WGS 84 Projection</span>
        </div>
        <span className="text-slate-600">|</span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.3, 4))}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.3, 0.6))}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setCenterOffset({ x: 0, y: 0 });
            }}
            className="p-1 hover:bg-slate-800 rounded transition-colors"
            title="Reset View"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 z-20 flex items-center gap-3 bg-slate-900/90 backdrop-blur-md px-3 py-1.5 rounded-xl border border-slate-700/60 shadow-lg text-xs text-slate-300">
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>Live (≤30s)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
          <span>Recent (≤3m)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-slate-500" />
          <span>Stale</span>
        </div>
        <span className="text-slate-600">|</span>
        <div className="flex items-center gap-1.5 text-rose-400">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>Restricted / Hazard</span>
        </div>
      </div>

      {/* Interactive Map Canvas */}
      <div
        className="w-full h-full cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        <svg
          viewBox="0 0 1000 700"
          className="w-full h-full"
          style={{
            transform: `translate(${centerOffset.x}px, ${centerOffset.y}px) scale(${zoom})`,
            transformOrigin: 'center center',
            transition: isDragging ? 'none' : 'transform 0.15s ease-out',
          }}
        >
          <defs>
            {/* Dark GIS Grid Pattern */}
            <pattern id="gis-grid" width="50" height="50" patternUnits="userSpaceOnUse">
              <path d="M 50 0 L 0 0 0 50" fill="none" stroke="rgba(255, 255, 255, 0.04)" strokeWidth="1" />
              <circle cx="0" cy="0" r="1.5" fill="rgba(255, 255, 255, 0.08)" />
            </pattern>
            {/* Pulse Filter */}
            <radialGradient id="pulse-grad">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* Background Grid */}
          <rect width="1000" height="700" fill="#020617" />
          <rect width="1000" height="700" fill="url(#gis-grid)" />

          {/* GeoZone Polygons */}
          {zones.map((zone) => {
            const points = zone.coordinates
              .map(([lng, lat]) => {
                const pt = project(lat, lng);
                return `${pt.x},${pt.y}`;
              })
              .join(' ');
            const { fill, stroke } = getZoneColor(zone.zone_type);

            // Compute centroid for label
            let cx = 0, cy = 0;
            zone.coordinates.forEach(([lng, lat]) => {
              const pt = project(lat, lng);
              cx += pt.x;
              cy += pt.y;
            });
            cx /= zone.coordinates.length;
            cy /= zone.coordinates.length;

            return (
              <g key={zone.id} className="cursor-pointer group">
                <polygon
                  points={points}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth="2"
                  strokeDasharray={zone.zone_type === 'RESTRICTED' ? '6 3' : undefined}
                  className="transition-all duration-300 group-hover:opacity-80"
                />
                <text
                  x={cx}
                  y={cy}
                  textAnchor="middle"
                  fill={stroke}
                  fontSize="10"
                  fontWeight="600"
                  className="pointer-events-none drop-shadow-md select-none tracking-wider uppercase font-mono"
                >
                  {zone.name}
                </text>
              </g>
            );
          })}

          {/* Selected Tourist Breadcrumb Route History */}
          {selectedTouristId && tripHistory.length > 1 && (
            <polyline
              points={tripHistory
                .map((pt) => {
                  const p = project(pt.latitude, pt.longitude);
                  return `${p.x},${p.y}`;
                })
                .join(' ')}
              fill="none"
              stroke="#38bdf8"
              strokeWidth="2.5"
              strokeDasharray="4 4"
              className="drop-shadow-[0_0_8px_rgba(56,189,248,0.6)]"
            />
          )}

          {/* Active Tourist Markers */}
          {tourists.map((t) => {
            const pos = project(t.latitude, t.longitude);
            const isSelected = t.tourist_id === selectedTouristId;
            const freshnessColor = getFreshnessColor(t.freshness);

            return (
              <g
                key={t.tourist_id}
                transform={`translate(${pos.x}, ${pos.y})`}
                onClick={() => onSelectTourist(isSelected ? null : t.tourist_id)}
                className="cursor-pointer group"
              >
                {/* Accuracy Radius Indicator */}
                <circle
                  r={Math.max(t.accuracy * 0.4, 14)}
                  fill="rgba(56, 189, 248, 0.08)"
                  stroke="rgba(56, 189, 248, 0.25)"
                  strokeWidth="1"
                />

                {/* Pulsing Live Halo */}
                {t.freshness === 'LIVE' && (
                  <circle r="18" fill="none" stroke={freshnessColor} strokeWidth="1.5" className="animate-ping opacity-60" />
                )}

                {/* Selection Highlight */}
                {isSelected && (
                  <circle r="22" fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray="3 3" />
                )}

                {/* Marker Body */}
                <circle r="12" fill="#0f172a" stroke={freshnessColor} strokeWidth="2.5" className="drop-shadow-lg" />

                {/* Direction Heading Arrow (if available) */}
                {t.heading !== null && t.heading !== undefined && (
                  <g transform={`rotate(${t.heading})`}>
                    <polygon points="0,-16 -4,-11 4,-11" fill={freshnessColor} />
                  </g>
                )}

                {/* Initial Badge */}
                <text
                  x="0"
                  y="3.5"
                  textAnchor="middle"
                  fill="#f8fafc"
                  fontSize="10"
                  fontWeight="bold"
                  className="pointer-events-none select-none"
                >
                  {t.tourist_name.charAt(0)}
                </text>

                {/* Label Box */}
                <g transform="translate(0, -26)">
                  <rect
                    x="-45"
                    y="-14"
                    width="90"
                    height="18"
                    rx="4"
                    fill="rgba(15, 23, 42, 0.9)"
                    stroke={isSelected ? '#38bdf8' : 'rgba(255, 255, 255, 0.15)'}
                    strokeWidth="1"
                  />
                  <text
                    x="0"
                    y="-2"
                    textAnchor="middle"
                    fill="#f1f5f9"
                    fontSize="9"
                    fontWeight="500"
                    className="pointer-events-none select-none font-sans"
                  >
                    {t.tourist_name.split(' ')[0]}
                  </text>
                </g>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Selected Tourist Inspector Card Overlay */}
      {selectedTouristId && (
        <div className="absolute bottom-4 left-4 z-20 w-80 bg-slate-900/95 backdrop-blur-md rounded-xl p-4 border border-cyan-500/40 shadow-2xl animate-in fade-in slide-in-from-bottom-2 duration-200">
          {(() => {
            const t = tourists.find((item) => item.tourist_id === selectedTouristId);
            if (!t) return null;
            return (
              <div>
                <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-2">
                  <div className="flex items-center gap-2">
                    <div className="w-7 h-7 rounded-full bg-cyan-950 border border-cyan-500 flex items-center justify-center font-bold text-cyan-400 text-xs">
                      {t.tourist_name.charAt(0)}
                    </div>
                    <div>
                      <h4 className="font-semibold text-white text-sm">{t.tourist_name}</h4>
                      <p className="text-xs text-slate-400">{t.trip_title}</p>
                    </div>
                  </div>
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

                <div className="grid grid-cols-2 gap-2 text-xs font-mono text-slate-300">
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">COORDINATES</span>
                    {t.latitude.toFixed(4)}, {t.longitude.toFixed(4)}
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">SPEED / HEADING</span>
                    {t.speed != null ? `${t.speed.toFixed(1)} m/s` : 'Static'}{' '}
                    {t.heading != null ? `(${t.heading.toFixed(0)}°)` : ''}
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">GPS ACCURACY</span>
                    ±{t.accuracy.toFixed(1)} m
                  </div>
                  <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                    <span className="text-slate-500 block text-[10px]">ACTIVE ZONES</span>
                    {t.active_zones.length > 0 ? (
                      <span className="text-rose-400 font-semibold">{t.active_zones.join(', ')}</span>
                    ) : (
                      <span className="text-slate-400">Open Zone</span>
                    )}
                  </div>
                </div>

                <button
                  onClick={() => onSelectTourist(null)}
                  className="mt-3 w-full py-1 text-xs text-slate-400 hover:text-white bg-slate-800 hover:bg-slate-700 rounded transition-colors font-medium"
                >
                  Deselect & Clear Breadcrumbs
                </button>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};
