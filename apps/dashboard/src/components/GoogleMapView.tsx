import React, { useEffect, useRef, useState } from 'react';
import { LiveTouristPosition, GeoZone } from '../types';

interface GoogleMapViewProps {
  tourists: LiveTouristPosition[];
  zones: GeoZone[];
  selectedTouristId: string | null;
  onSelectTourist: (touristId: string | null) => void;
  tripHistory?: { latitude: number; longitude: number }[];
  onInspectRisk?: (tourist: LiveTouristPosition) => void;
}

// Dark tactical map styling for Google Maps
const darkMapStyle = [
  { elementType: 'geometry', stylers: [{ color: '#0b111e' }] },
  { elementType: 'labels.text.stroke', stylers: [{ color: '#07090e' }] },
  { elementType: 'labels.text.fill', stylers: [{ color: '#74829c' }] },
  {
    featureType: 'administrative.locality',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#cbd5e1' }],
  },
  {
    featureType: 'poi',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#64748b' }],
  },
  {
    featureType: 'poi.park',
    elementType: 'geometry',
    stylers: [{ color: '#0d1f2d' }],
  },
  {
    featureType: 'poi.park',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#475569' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry',
    stylers: [{ color: '#1e293b' }],
  },
  {
    featureType: 'road',
    elementType: 'geometry.stroke',
    stylers: [{ color: '#0f172a' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry',
    stylers: [{ color: '#334155' }],
  },
  {
    featureType: 'road.highway',
    elementType: 'geometry.stroke',
    stylers: [{ color: '#1e293b' }],
  },
  {
    featureType: 'transit',
    elementType: 'geometry',
    stylers: [{ color: '#172554' }],
  },
  {
    featureType: 'water',
    elementType: 'geometry',
    stylers: [{ color: '#020617' }],
  },
  {
    featureType: 'water',
    elementType: 'labels.text.fill',
    stylers: [{ color: '#38bdf8' }],
  },
];

export const GoogleMapView: React.FC<GoogleMapViewProps> = ({
  tourists,
  zones,
  selectedTouristId,
  onSelectTourist,
  tripHistory = [],
  onInspectRisk,
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const [mapInstance, setMapInstance] = useState<any>(null);
  const [googleLoaded, setGoogleLoaded] = useState<boolean>(false);
  const markersRef = useRef<{ [id: string]: any }>({});
  const polygonsRef = useRef<any[]>([]);
  const polylineRef = useRef<any>(null);

  const apiKey = (import.meta as any).env?.VITE_GOOGLE_MAPS_API_KEY || 'AIzaSyAr0_6DjIUCGhzaI0O3Q86To43wSb9CiTo';

  // Load Google Maps API script dynamically
  useEffect(() => {
    if ((window as any).google && (window as any).google.maps) {
      setGoogleLoaded(true);
      return;
    }

    const scriptId = 'google-maps-api-script';
    let script = document.getElementById(scriptId) as HTMLScriptElement;
    if (!script) {
      script = document.createElement('script');
      script.id = scriptId;
      script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&libraries=geometry`;
      script.async = true;
      script.defer = true;
      script.onload = () => setGoogleLoaded(true);
      script.onerror = () => {
        console.error('Failed to load Google Maps script');
      };
      document.head.appendChild(script);
    } else {
      script.addEventListener('load', () => setGoogleLoaded(true));
    }
  }, [apiKey]);

  // Initialize Map
  useEffect(() => {
    if (!googleLoaded || !mapContainerRef.current || mapInstance) return;

    try {
      const google = (window as any).google;
      const defaultLat = tourists.length > 0 ? tourists[0].latitude : 35.3606;
      const defaultLng = tourists.length > 0 ? tourists[0].longitude : 138.7274;

      const map = new google.maps.Map(mapContainerRef.current, {
        center: { lat: defaultLat, lng: defaultLng },
        zoom: 13,
        styles: darkMapStyle,
        disableDefaultUI: false,
        zoomControl: true,
        mapTypeControl: true,
        scaleControl: true,
        streetViewControl: false,
        rotateControl: false,
        fullscreenControl: true,
      });

      setMapInstance(map);
    } catch (err) {
      console.error('Error initializing Google Map:', err);
    }
  }, [googleLoaded, mapInstance, tourists]);

  // Update GeoZones (Polygons)
  useEffect(() => {
    if (!mapInstance || !googleLoaded) return;
    const google = (window as any).google;

    // Clear old polygons
    polygonsRef.current.forEach((p) => p.setMap(null));
    polygonsRef.current = [];

    zones.forEach((zone) => {
      const coords = zone.coordinates.map(([lng, lat]) => ({ lat, lng }));
      let fillColor = '#10b981';
      let strokeColor = '#059669';

      if (zone.zone_type === 'RESTRICTED') {
        fillColor = '#ef4444';
        strokeColor = '#dc2626';
      } else if (zone.zone_type === 'HIGH_RISK') {
        fillColor = '#f59e0b';
        strokeColor = '#d97706';
      }

      const polygon = new google.maps.Polygon({
        paths: coords,
        strokeColor: strokeColor,
        strokeOpacity: 0.85,
        strokeWeight: 2,
        fillColor: fillColor,
        fillOpacity: 0.25,
        map: mapInstance,
      });

      const infoWindow = new google.maps.InfoWindow({
        content: `
          <div style="font-family: inherit; padding: 6px; color: #0f172a;">
            <strong style="font-size: 13px;">${zone.name}</strong><br/>
            <span style="font-size: 11px; color: #475569;">Safety Type: ${zone.zone_type}</span>
          </div>
        `,
      });

      polygon.addListener('click', (e: any) => {
        infoWindow.setPosition(e.latLng);
        infoWindow.open(mapInstance);
      });

      polygonsRef.current.push(polygon);
    });
  }, [mapInstance, zones, googleLoaded]);

  // Update Tourist GPS Markers
  useEffect(() => {
    if (!mapInstance || !googleLoaded) return;
    const google = (window as any).google;

    // Remove stale markers
    const activeIds = new Set(tourists.map((t) => t.tourist_id));
    Object.keys(markersRef.current).forEach((id) => {
      if (!activeIds.has(id)) {
        markersRef.current[id].setMap(null);
        delete markersRef.current[id];
      }
    });

    tourists.forEach((tourist) => {
      const pos = { lat: tourist.latitude, lng: tourist.longitude };
      const isSelected = tourist.tourist_id === selectedTouristId;
      const markerColor = tourist.freshness === 'LIVE' ? '#10b981' : tourist.freshness === 'RECENT' ? '#f59e0b' : '#94a3b8';

      if (markersRef.current[tourist.tourist_id]) {
        markersRef.current[tourist.tourist_id].setPosition(pos);
      } else {
        const svgIcon = {
          path: google.maps.SymbolPath.CIRCLE,
          scale: isSelected ? 9 : 7,
          fillColor: markerColor,
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
        };

        const marker = new google.maps.Marker({
          position: pos,
          map: mapInstance,
          title: tourist.tourist_name || 'Tourist GPS Stream',
          icon: svgIcon,
        });

        const infoWindow = new google.maps.InfoWindow({
          content: `
            <div style="font-family: inherit; padding: 6px; color: #0f172a;">
              <strong style="font-size: 13px;">${tourist.tourist_name || 'Tourist'}</strong><br/>
              <span style="font-size: 11px; color: #475569;">Freshness: ${tourist.freshness}</span><br/>
              <span style="font-size: 11px; color: #475569;">Speed: ${(tourist.speed || 0).toFixed(1)} m/s</span>
            </div>
          `,
        });

        marker.addListener('click', () => {
          infoWindow.open(mapInstance, marker);
          onSelectTourist(tourist.tourist_id);
          if (onInspectRisk) onInspectRisk(tourist);
        });

        markersRef.current[tourist.tourist_id] = marker;
      }
    });

    // Auto-center on selected tourist
    if (selectedTouristId) {
      const target = tourists.find((t) => t.tourist_id === selectedTouristId);
      if (target) {
        mapInstance.panTo({ lat: target.latitude, lng: target.longitude });
      }
    }
  }, [mapInstance, tourists, selectedTouristId, googleLoaded, onInspectRisk, onSelectTourist]);

  // Update Breadcrumb Route History
  useEffect(() => {
    if (!mapInstance || !googleLoaded) return;
    const google = (window as any).google;

    if (polylineRef.current) {
      polylineRef.current.setMap(null);
      polylineRef.current = null;
    }

    if (tripHistory.length > 1) {
      const path = tripHistory.map((h) => ({ lat: h.latitude, lng: h.longitude }));
      polylineRef.current = new google.maps.Polyline({
        path: path,
        geodesic: true,
        strokeColor: '#06b6d4',
        strokeOpacity: 0.85,
        strokeWeight: 3,
        map: mapInstance,
      });
    }
  }, [mapInstance, tripHistory, googleLoaded]);

  return (
    <div className="relative w-full h-full min-h-[580px] bg-slate-950 rounded-2xl overflow-hidden flex flex-col shadow-2xl border border-slate-800">
      <div ref={mapContainerRef} className="w-full h-full min-h-[580px]" style={{ minHeight: '580px' }} />
    </div>
  );
};
