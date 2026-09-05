import React, { useState, useEffect } from 'react';
import { Incident, IncidentEvent, IncidentStatus } from '../types';
import { api } from '../services/api';
import { LoadingSpinner } from './LoadingSpinner';
import {
  X,
  Clock,
  MapPin,
  Camera,
  AlertTriangle,
  UserCheck,
} from 'lucide-react';

interface IncidentDetailModalProps {
  incident: Incident;
  currentUserRole?: string;
  onClose: () => void;
  onIncidentUpdated: (updated: Incident) => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  currentUserRole: _currentUserRole = 'AUTHORITY',
  onClose,
  onIncidentUpdated,
}) => {
  const [timeline, setTimeline] = useState<IncidentEvent[]>([]);
  const [loadingTimeline, setLoadingTimeline] = useState(true);
  const [availableResponders, setAvailableResponders] = useState<any[]>([]);
  const [selectedResponderId, setSelectedResponderId] = useState('');
  const [actionNotes, setActionNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [cctvLoading, setCctvLoading] = useState(false);
  const [cctvResult, setCctvResult] = useState<any | null>(null);

  useEffect(() => {
    fetchTimeline();
    fetchResponders();
  }, [incident.id]);

  const fetchTimeline = async () => {
    try {
      setLoadingTimeline(true);
      const events = await api.getIncidentTimeline(incident.id);
      setTimeline(events);
    } catch (err: any) {
      console.error('Failed to fetch timeline:', err);
    } finally {
      setLoadingTimeline(false);
    }
  };

  const fetchResponders = async () => {
    try {
      const responders = await api.listAvailableResponders();
      setAvailableResponders(responders);
      if (responders.length > 0) {
        setSelectedResponderId(responders[0].id);
      }
    } catch (err) {
      console.error('Failed to fetch responders:', err);
    }
  };

  const handleInvestigateCCTV = async () => {
    try {
      setCctvLoading(true);
      setErrorMsg(null);
      const res = await api.investigateIncidentCCTV(incident.id, 300, 5, 5);
      setCctvResult(res);
      await fetchTimeline();
    } catch (err: any) {
      setErrorMsg(err.message || 'CCTV investigation failed.');
    } finally {
      setCctvLoading(false);
    }
  };

  const handleTransition = async (toStatus: IncidentStatus, promptReason = false) => {
    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      let notes = actionNotes;
      if (promptReason && !notes) {
        const input = window.prompt(`Reason for transitioning to ${toStatus}:`);
        if (input === null) {
          setIsSubmitting(false);
          return;
        }
        notes = input;
      }
      const updated = await api.transitionIncident(
        incident.id,
        toStatus,
        notes || undefined,
        toStatus === 'RESOLVED' ? notes : undefined
      );
      setActionNotes('');
      onIncidentUpdated(updated);
      fetchTimeline();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update incident state');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAssign = async () => {
    if (!selectedResponderId) return;
    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      const updated = await api.assignIncident(
        incident.id,
        selectedResponderId,
        actionNotes || 'Authority dispatch from Operations Console'
      );
      setActionNotes('');
      onIncidentUpdated(updated);
      fetchTimeline();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to assign responder');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityBadge = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/40';
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-dialog max-w-4xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/80">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
              <AlertTriangle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-wide">
                  Emergency Incident #{incident.id.slice(0, 8)}
                </h2>
                <span className={`px-2.5 py-0.5 text-xs font-bold rounded-full border ${getSeverityBadge(incident.severity)}`}>
                  {incident.severity}
                </span>
                <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-slate-800 text-slate-300 border border-slate-700">
                  {incident.status}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Source: {incident.source} • Created: {new Date(incident.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-lg bg-slate-800/80 hover:bg-slate-700 text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body space-y-6">
          {errorMsg && (
            <div className="p-3.5 bg-red-500/15 border border-red-500/30 rounded-xl text-red-300 text-xs font-medium flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Top Info Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tourist Profile Card */}
            <div className="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs uppercase tracking-wider">
                <UserCheck className="w-4 h-4" />
                Tourist Details
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">Name:</span>
                  <span className="text-white font-medium">{incident.tourist_name || 'Vangala Sreeram Yaswanth'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Expedition / Route:</span>
                  <span className="text-slate-200">{incident.trip_title || 'Active Journey'}</span>
                </div>
              </div>
            </div>

            {/* Spatial Location Context */}
            <div className="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center gap-2 text-indigo-400 font-semibold text-xs uppercase tracking-wider">
                <MapPin className="w-4 h-4" />
                Spatial Telemetry & Risk
              </div>
              <div className="space-y-1.5 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-400">GPS Coordinates:</span>
                  <span className="text-slate-200 font-mono">
                    {incident.latitude != null && incident.longitude != null
                      ? `${incident.latitude.toFixed(5)}, ${incident.longitude.toFixed(5)}`
                      : 'Real-time Fixed via Mobile Client'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Assigned Responder:</span>
                  <span className="text-emerald-400 font-medium">
                    {incident.assigned_responder_name || 'Unassigned'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* CCTV Camera & ML Hazard Inspection */}
          <div className="bg-slate-900/90 p-4 rounded-xl border border-slate-800 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-cyan-400 font-semibold text-xs uppercase tracking-wider">
                <Camera className="w-4 h-4" />
                CCTV Camera Feeds & AI Fall Detection (v0.6 ML)
              </div>
              <button
                type="button"
                disabled={cctvLoading}
                onClick={handleInvestigateCCTV}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md transition-all flex items-center gap-1.5"
              >
                {cctvLoading ? 'Scanning Cameras...' : '📹 Run CCTV Investigation'}
              </button>
            </div>

            {cctvResult && (
              <div className="mt-3 p-3 bg-slate-950 rounded-xl border border-indigo-500/30 text-xs space-y-2">
                <div className="flex justify-between font-semibold">
                  <span className="text-indigo-400">Status: {cctvResult.status}</span>
                  <span className="text-slate-400">{cctvResult.cameras_queried_count} Camera(s) Active</span>
                </div>
                <p className="text-slate-300">{cctvResult.summary}</p>
                {cctvResult.detection_results?.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    {cctvResult.detection_results.map((det: any, idx: number) => (
                      <div key={idx} className="p-2 bg-slate-900 rounded-lg border border-slate-800 text-xs">
                        <span className="font-bold text-cyan-400">[{det.camera_name || 'Camera'}]</span>: {det.detection_type} (conf: {((det.confidence || 0) * 100).toFixed(0)}%)
                        {det.explanation && <p className="text-slate-400 italic text-[11px] mt-0.5">"{det.explanation}"</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Operational Timeline */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-slate-400 font-semibold text-xs uppercase tracking-wider">
              <Clock className="w-4 h-4" />
              Incident Lifecycle Timeline
            </div>
            {loadingTimeline ? (
              <div className="py-6 flex justify-center">
                <LoadingSpinner />
              </div>
            ) : timeline.length === 0 ? (
              <p className="text-xs text-slate-500 italic">No events in timeline yet.</p>
            ) : (
              <div className="space-y-2">
                {timeline.map((evt, idx) => (
                  <div key={evt.id || idx} className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-xs flex items-center justify-between">
                    <div>
                      <span className="font-semibold text-slate-200">{evt.event_type.replace(/_/g, ' ')}</span>
                      <p className="text-slate-400 text-[11px]">Actor: {evt.actor_name || 'Authority'} ({evt.actor_role})</p>
                      {evt.reason && <p className="text-slate-300 italic text-[11px] mt-0.5">"{evt.reason}"</p>}
                    </div>
                    <span className="text-slate-500 font-mono text-[11px]">
                      {new Date(evt.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Action Controls Footer */}
        <div className="p-5 border-t border-slate-800 bg-slate-950 flex flex-wrap items-center justify-between gap-3">
          <input
            type="text"
            value={actionNotes}
            onChange={(e) => setActionNotes(e.target.value)}
            placeholder="Operational notes / rationale for action..."
            className="flex-1 min-w-[250px] px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
          />

          <div className="flex items-center gap-2">
            {incident.status === 'DETECTED' && (
              <button
                disabled={isSubmitting}
                onClick={() => handleTransition('VERIFYING')}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition-all shadow-md"
              >
                🔍 Begin Verification
              </button>
            )}

            {incident.status === 'VERIFYING' && (
              <button
                disabled={isSubmitting}
                onClick={() => handleTransition('VERIFIED')}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-orange-600 hover:bg-orange-500 text-white transition-all shadow-md"
              >
                ✅ Confirm Incident
              </button>
            )}

            {(incident.status === 'VERIFIED' || incident.status === 'ESCALATED') && (
              <div className="flex items-center gap-2">
                <select
                  value={selectedResponderId}
                  onChange={(e) => setSelectedResponderId(e.target.value)}
                  className="px-3 py-2 text-xs bg-slate-900 border border-slate-700 rounded-lg text-slate-200"
                >
                  {availableResponders.map((r) => (
                    <option key={r.id} value={r.id}>
                      👮 {r.full_name}
                    </option>
                  ))}
                </select>
                <button
                  disabled={isSubmitting || !selectedResponderId}
                  onClick={handleAssign}
                  className="px-4 py-2 text-xs font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md"
                >
                  👤 Assign Responder
                </button>
              </div>
            )}

            {incident.status === 'ASSIGNED' && (
              <button
                disabled={isSubmitting}
                onClick={() => handleTransition('RESPONDING')}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md"
              >
                🚑 Field Response Active
              </button>
            )}

            {incident.status === 'RESPONDING' && (
              <button
                disabled={isSubmitting}
                onClick={() => handleTransition('RESOLVED')}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md"
              >
                🏁 Mark Resolved
              </button>
            )}

            <button
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
