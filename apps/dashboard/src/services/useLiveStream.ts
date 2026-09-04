import { useEffect, useRef, useState, useCallback } from 'react';
import { LiveTouristPosition, ZoneEvent } from '../types';

interface LiveStreamState {
  connected: boolean;
  tourists: LiveTouristPosition[];
  recentEvents: ZoneEvent[];
  lastUpdate: Date | null;
}

export function useLiveStream() {
  const [state, setState] = useState<LiveStreamState>({
    connected: false,
    tourists: [],
    recentEvents: [],
    lastUpdate: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const heartbeatIntervalRef = useRef<number | null>(null);
  const reconnectAttemptsRef = useRef(0);

  const connect = useCallback(() => {
    const token = localStorage.getItem('kiroshi_token');
    if (!token) {
      return;
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const wsUrl = `${protocol}//${host}/api/v1/ws/authority?token=${encodeURIComponent(token)}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setState((prev) => ({ ...prev, connected: true }));
        reconnectAttemptsRef.current = 0;

        // Start heartbeat ping every 25 seconds
        if (heartbeatIntervalRef.current) {
          window.clearInterval(heartbeatIntervalRef.current);
        }
        heartbeatIntervalRef.current = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'PING' }));
          }
        }, 25000);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          const now = new Date();

          if (message.type === 'INITIAL_SNAPSHOT') {
            setState((prev) => ({
              ...prev,
              tourists: message.data || [],
              lastUpdate: now,
            }));
          } else if (message.type === 'LOCATION_UPDATE') {
            const update: LiveTouristPosition = message.data;
            setState((prev) => {
              const idx = prev.tourists.findIndex((t) => t.tourist_id === update.tourist_id);
              let newTourists: LiveTouristPosition[];
              if (idx >= 0) {
                newTourists = [...prev.tourists];
                newTourists[idx] = update;
              } else {
                newTourists = [update, ...prev.tourists];
              }
              return {
                ...prev,
                tourists: newTourists,
                lastUpdate: now,
              };
            });
          } else if (message.type === 'ZONE_ENTER' || message.type === 'ZONE_EXIT') {
            const zEvent: ZoneEvent = {
              id: message.data.event_id || Math.random().toString(),
              tourist_id: message.data.tourist_id,
              trip_id: message.data.trip_id,
              zone_id: message.data.zone_id,
              zone_name: message.data.zone_name,
              zone_type: message.data.zone_type,
              event_type: message.data.event_type,
              occurred_at: message.data.occurred_at || now.toISOString(),
            };
            setState((prev) => ({
              ...prev,
              recentEvents: [zEvent, ...prev.recentEvents.slice(0, 49)],
              lastUpdate: now,
            }));
          }
        } catch (err) {
          console.error('Error parsing live WebSocket message:', err);
        }
      };

      ws.onclose = () => {
        setState((prev) => ({ ...prev, connected: false }));
        if (heartbeatIntervalRef.current) {
          window.clearInterval(heartbeatIntervalRef.current);
          heartbeatIntervalRef.current = null;
        }

        // Exponential backoff reconnect: 1s, 2s, 4s, max 10s
        const backoff = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 10000);
        reconnectAttemptsRef.current += 1;
        reconnectTimeoutRef.current = window.setTimeout(connect, backoff);
      };

      ws.onerror = (err) => {
        console.warn('WebSocket stream encountered error:', err);
        ws.close();
      };
    } catch (err) {
      console.error('Failed to instantiate WebSocket connection:', err);
    }
  }, []);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        window.clearTimeout(reconnectTimeoutRef.current);
      }
      if (heartbeatIntervalRef.current) {
        window.clearInterval(heartbeatIntervalRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  return state;
}
