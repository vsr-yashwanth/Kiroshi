import React, { useState, useEffect } from 'react';
import {
  Incident,
  IncidentEvent,
  IncidentStatus,
} from '../types';
import { api } from '../services/api';
import { LoadingSpinner } from './LoadingSpinner';

interface IncidentDetailModalProps {
  incident: Incident;
  currentUserRole?: string;
  onClose: () => void;
  onIncidentUpdated: (updated: Incident) => void;
}

export const IncidentDetailModal: React.FC<IncidentDetailModalProps> = ({
  incident,
  currentUserRole = 'AUTHORITY',
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
        toStatus === 'RESOLVED' ? notes : undefined,
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
      const updated = await api.assignIncident(incident.id, selectedResponderId, actionNotes || undefined);
      setActionNotes('');
      onIncidentUpdated(updated);
      fetchTimeline();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to assign responder');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityBadgeColor = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'HIGH':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default:
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
    }
  };

  const getStatusBadgeColor = (st: string) => {
    switch (st) {
      case 'DETECTED':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'VERIFYING':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'VERIFIED':
        return 'bg-orange-500/20 text-orange-300 border-orange-500/40';
      case 'ESCALATED':
        return 'bg-red-600/20 text-red-300 border-red-600/40';
      case 'ASSIGNED':
        return 'bg-indigo-500/20 text-indigo-300 border-indigo-500/40';
      case 'RESPONDING':
        return 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40';
      case 'RESOLVED':
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
      case 'CLOSED':
        return 'bg-slate-700/50 text-slate-400 border-slate-600';
      case 'DISMISSED':
        return 'bg-slate-700/30 text-slate-500 border-slate-700';
      default:
        return 'bg-slate-700 text-slate-300 border-slate-600';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="relative w-full max-w-4xl max-h-[90vh] flex flex-col bg-slate-900 border border-slate-700/80 rounded-2xl shadow-2xl overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <span className="text-xl">🚨</span>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white tracking-wide">
                  Incident #{incident.id.slice(0, 8)}
                </h2>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-md border ${getSeverityBadgeColor(incident.severity)}`}>
                  {incident.severity}
                </span>
                <span className={`px-2 py-0.5 text-xs font-semibold rounded-md border ${getStatusBadgeColor(incident.status)}`}>
                  {incident.status}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Source: <span className="font-medium text-slate-200">{incident.source}</span> • Role: <span className="text-slate-300 font-mono">{currentUserRole}</span> • Created at{' '}
                {new Date(incident.created_at).toLocaleString()}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors p-2 rounded-lg hover:bg-slate-800"
          >
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {errorMsg && (
            <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm">
              ⚠️ {errorMsg}
            </div>
          )}

          {/* Context Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tourist & Location Card */}
            <div className="p-4 bg-slate-950/40 rounded-xl border border-slate-800 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <span>👤</span> Tourist Information
              </h3>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Tourist:</span>
                  <span className="text-slate-200 font-medium">{incident.tourist_name || 'Anonymous Tourist'}</span>
                </div>
                {incident.tourist_phone && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Phone:</span>
                    <span className="text-slate-200 font-mono">{incident.tourist_phone}</span>
                  </div>
                )}
                {incident.emergency_contact_name && (
                  <div className="flex justify-between">
                    <span className="text-slate-400">Emergency Contact:</span>
                    <span className="text-slate-200">
                      {incident.emergency_contact_name} ({incident.emergency_contact_phone})
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-slate-400">Trip:</span>
                  <span className="text-slate-200">{incident.trip_title || 'Active Trek / Route'}</span>
                </div>
              </div>
            </div>

            {/* Coordinates & Risk Assessment Card */}
            <div className="p-4 bg-slate-950/40 rounded-xl border border-slate-800 space-y-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                <span>📍</span> Location & Risk Context
              </h3>
              <div className="space-y-1.5 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-400">Coordinates:</span>
                  <span className="text-slate-200 font-mono">
                    {incident.latitude != null && incident.longitude != null
                      ? `${incident.latitude.toFixed(5)}, ${incident.longitude.toFixed(5)}`
                      : 'UNKNOWN / UNAVAILABLE'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Location Freshness:</span>
                  <span className="text-slate-200 font-medium">{incident.location_freshness}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Risk Level / Score:</span>
                  <span className="text-slate-200">
                    {incident.risk_level || 'N/A'} ({incident.risk_score != null ? (incident.risk_score * 100).toFixed(0) + '%' : 'N/A'})
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Assigned Responder:</span>
                  <span className="text-indigo-400 font-semibold">
                    {incident.assigned_responder_name || 'Unassigned'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Notes / Description if present */}
          {incident.notes && (
            <div className="p-4 bg-amber-500/10 border border-amber-500/20 rounded-xl">
              <span className="text-xs font-bold uppercase tracking-wider text-amber-400 block mb-1">
                Incident Notes / Distress Dispatch:
              </span>
              <p className="text-sm text-slate-200">{incident.notes}</p>
            </div>
          )}

          {/* Chronological Incident Timeline */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <span>⏱️</span> Operational Timeline (Append-Only Audit Log)
            </h3>
            {loadingTimeline ? (
              <div className="py-6 flex justify-center">
                <LoadingSpinner />
              </div>
            ) : timeline.length === 0 ? (
              <p className="text-sm text-slate-500 italic">No events recorded in timeline.</p>
            ) : (
              <div className="relative pl-6 space-y-4 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
                {timeline.map((evt, idx) => (
                  <div key={evt.id || idx} className="relative group">
                    <div className="absolute -left-6 top-1 w-2.5 h-2.5 rounded-full bg-cyan-400 ring-4 ring-slate-900" />
                    <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800 text-xs space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="font-semibold text-slate-200">
                          {evt.event_type.replace(/_/g, ' ')}
                        </span>
                        <span className="text-slate-500 font-mono">
                          {new Date(evt.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                      <p className="text-slate-400">
                        Actor: <span className="text-slate-300 font-medium">{evt.actor_name || 'System'}</span> ({evt.actor_role})
                      </p>
                      {evt.reason && <p className="text-slate-300 italic">"{evt.reason}"</p>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Action Controls Footer (State Machine Powered) */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 space-y-3">
          {/* Action note input */}
          {incident.status !== 'CLOSED' && incident.status !== 'DISMISSED' && (
            <div className="flex gap-2">
              <input
                type="text"
                value={actionNotes}
                onChange={(e) => setActionNotes(e.target.value)}
                placeholder="Operational notes / rationale for action..."
                className="flex-1 px-3 py-2 text-sm bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
              />
            </div>
          )}

          {/* State transition buttons */}
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              {/* DETECTED state actions */}
              {incident.status === 'DETECTED' && (
                <>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleTransition('VERIFYING')}
                    className="px-4 py-2 text-sm font-semibold rounded-lg bg-amber-600 hover:bg-amber-500 text-white transition-all shadow-md"
                  >
                    🔍 Begin Verification
                  </button>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleTransition('DISMISSED', true)}
                    className="px-3 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
                  >
                    Dismiss
                  </button>
                </>
              )}

              {/* VERIFYING state actions */}
              {incident.status === 'VERIFYING' && (
                <>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleTransition('VERIFIED')}
                    className="px-4 py-2 text-sm font-semibold rounded-lg bg-orange-600 hover:bg-orange-500 text-white transition-all shadow-md"
                  >
                    ✅ Confirm & Verify Incident
                  </button>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleTransition('DISMISSED', true)}
                    className="px-3 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
                  >
                    Dismiss
                  </button>
                </>
              )}

              {/* VERIFIED state actions */}
              {incident.status === 'VERIFIED' && (
                <>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleTransition('ESCALATED')}
                    className="px-4 py-2 text-sm font-semibold rounded-lg bg-red-600 hover:bg-red-500 text-white transition-all shadow-md"
                  >
                    ⚠️ Escalate Incident
                  </button>
                  <button
                    disabled={isSubmitting}
                    onClick={() => handleTransition('DISMISSED', true)}
                    className="px-3 py-2 text-sm font-medium rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
                  >
                    Dismiss
                  </button>
                </>
              )}

              {/* ESCALATED / VERIFIED -> Assign responder */}
              {(incident.status === 'ESCALATED' || incident.status === 'VERIFIED' || incident.status === 'ASSIGNED') && (
                <div className="flex items-center gap-2">
                  <select
                    value={selectedResponderId}
                    onChange={(e) => setSelectedResponderId(e.target.value)}
                    className="px-3 py-2 text-sm bg-slate-900 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    {availableResponders.map((r) => (
                      <option key={r.id} value={r.id}>
                        👮 {r.full_name} ({r.email})
                      </option>
                    ))}
                  </select>
                  <button
                    disabled={isSubmitting || !selectedResponderId}
                    onClick={handleAssign}
                    className="px-4 py-2 text-sm font-semibold rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-md"
                  >
                    {incident.status === 'ASSIGNED' ? '🔄 Reassign' : '👤 Assign Responder'}
                  </button>
                </div>
              )}

              {/* ASSIGNED -> Begin response */}
              {incident.status === 'ASSIGNED' && (
                <button
                  disabled={isSubmitting}
                  onClick={() => handleTransition('RESPONDING')}
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white transition-all shadow-md"
                >
                  🚑 Begin Response
                </button>
              )}

              {/* RESPONDING -> Resolve */}
              {incident.status === 'RESPONDING' && (
                <button
                  disabled={isSubmitting}
                  onClick={() => handleTransition('RESOLVED', true)}
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md"
                >
                  🏁 Mark Resolved
                </button>
              )}

              {/* RESOLVED -> Close */}
              {incident.status === 'RESOLVED' && (
                <button
                  disabled={isSubmitting}
                  onClick={() => handleTransition('CLOSED', true)}
                  className="px-4 py-2 text-sm font-semibold rounded-lg bg-slate-700 hover:bg-slate-600 text-white transition-all shadow-md"
                >
                  🔒 Close Incident
                </button>
              )}

              {/* Terminal States */}
              {(incident.status === 'CLOSED' || incident.status === 'DISMISSED') && (
                <span className="text-xs text-slate-500 italic">
                  Incident is in terminal state ({incident.status}). No further state transitions allowed.
                </span>
              )}
            </div>

            <button
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-slate-400 hover:text-white transition-colors"
            >
              Close Window
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
