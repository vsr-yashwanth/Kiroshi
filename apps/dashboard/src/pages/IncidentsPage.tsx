import React, { useState, useEffect } from 'react';
import { Incident } from '../types';
import { api } from '../services/api';
import { IncidentDetailModal } from '../components/IncidentDetailModal';
import { LoadingSpinner } from '../components/LoadingSpinner';

export const IncidentsPage: React.FC = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('ACTIVE');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');

  useEffect(() => {
    fetchIncidents();
    const interval = setInterval(fetchIncidents, 10000);
    return () => clearInterval(interval);
  }, [statusFilter, severityFilter]);

  const fetchIncidents = async () => {
    try {
      const statusParam = statusFilter === 'ACTIVE' || statusFilter === 'ALL' ? undefined : statusFilter;
      const sevParam = severityFilter === 'ALL' ? undefined : severityFilter;
      const data = await api.listIncidents(statusParam, sevParam);

      // If filter is ACTIVE, filter out terminal states locally if not already filtered
      let filtered = data;
      if (statusFilter === 'ACTIVE') {
        filtered = data.filter((i) => i.status !== 'CLOSED' && i.status !== 'DISMISSED');
      }
      setIncidents(filtered);
    } catch (err) {
      console.error('Failed to fetch incidents:', err);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityBadgeColor = (sev: string) => {
    switch (sev) {
      case 'CRITICAL':
        return 'bg-red-500/20 text-red-400 border-red-500/30 animate-pulse';
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

  // Quick stats
  const activeCount = incidents.filter((i) => i.status !== 'CLOSED' && i.status !== 'DISMISSED').length;
  const criticalCount = incidents.filter((i) => i.severity === 'CRITICAL').length;
  const respondingCount = incidents.filter((i) => i.status === 'RESPONDING').length;
  const verifyingCount = incidents.filter((i) => i.status === 'DETECTED' || i.status === 'VERIFYING').length;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-wide flex items-center gap-2">
            <span>🚨</span> Emergency & Incident Operations Console
          </h1>
          <p className="text-sm text-slate-400">
            Real-time triage, verification, responder assignment, and incident lifecycle management.
          </p>
        </div>
        <button
          onClick={fetchIncidents}
          className="px-4 py-2 text-xs font-semibold rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-all flex items-center gap-2"
        >
          <span>🔄</span> Refresh Queue
        </button>
      </div>

      {/* KPI Stats Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Active Queue</span>
          <span className="text-2xl font-bold text-white mt-2">{activeCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-red-950/20 border border-red-800/40 flex flex-col justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-red-400">Critical Emergencies</span>
          <span className="text-2xl font-bold text-red-300 mt-2">{criticalCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40 flex flex-col justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-amber-400">Awaiting Verification</span>
          <span className="text-2xl font-bold text-amber-300 mt-2">{verifyingCount}</span>
        </div>
        <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-800/40 flex flex-col justify-between">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400">Responders In Field</span>
          <span className="text-2xl font-bold text-cyan-300 mt-2">{respondingCount}</span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-900/50 border border-slate-800">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ACTIVE">⚡ Active Only</option>
            <option value="ALL">All States</option>
            <option value="DETECTED">Detected</option>
            <option value="VERIFYING">Verifying</option>
            <option value="VERIFIED">Verified</option>
            <option value="ESCALATED">Escalated</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="RESPONDING">Responding</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
            <option value="DISMISSED">Dismissed</option>
          </select>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-1.5 text-xs bg-slate-950 border border-slate-700 rounded-lg text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="ALL">All Severities</option>
            <option value="CRITICAL">🔴 Critical</option>
            <option value="HIGH">🟠 High</option>
            <option value="MEDIUM">🟡 Medium</option>
            <option value="LOW">🔵 Low</option>
          </select>
        </div>
      </div>

      {/* Incidents Table / Queue */}
      <div className="bg-slate-900/40 rounded-xl border border-slate-800 overflow-hidden shadow-lg">
        {loading ? (
          <div className="p-12 flex justify-center">
            <LoadingSpinner />
          </div>
        ) : incidents.length === 0 ? (
          <div className="p-12 text-center text-slate-400">
            <p className="text-3xl mb-2">🛡️</p>
            <p className="text-base font-medium">No safety incidents found matching the selected filters.</p>
            <p className="text-xs text-slate-500 mt-1">All monitored tourist zones are currently nominal.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-800 bg-slate-950/60 text-xs uppercase text-slate-400 font-semibold tracking-wider">
                  <th className="px-6 py-3.5">Incident ID / Source</th>
                  <th className="px-6 py-3.5">Severity</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Tourist</th>
                  <th className="px-6 py-3.5">Location Coordinates</th>
                  <th className="px-6 py-3.5">Assigned Responder</th>
                  <th className="px-6 py-3.5">Time Logged</th>
                  <th className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {incidents.map((incident) => (
                  <tr
                    key={incident.id}
                    className="hover:bg-slate-800/30 transition-colors group cursor-pointer"
                    onClick={() => setSelectedIncident(incident)}
                  >
                    <td className="px-6 py-4">
                      <div className="font-mono font-medium text-slate-200">
                        #{incident.id.slice(0, 8)}
                      </div>
                      <div className="text-xs text-slate-400 flex items-center gap-1.5 mt-0.5">
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                        {incident.source}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-md border ${getSeverityBadgeColor(incident.severity)}`}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2.5 py-0.5 text-xs font-semibold rounded-md border ${getStatusBadgeColor(incident.status)}`}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <div className="font-medium text-slate-200">{incident.tourist_name || 'Anonymous Tourist'}</div>
                      <div className="text-xs text-slate-500">{incident.trip_title || 'Active Trip'}</div>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-300">
                      {incident.latitude != null && incident.longitude != null ? (
                        <div>
                          {incident.latitude.toFixed(4)}, {incident.longitude.toFixed(4)}
                          <div className="text-[10px] text-slate-500 uppercase">{incident.location_freshness}</div>
                        </div>
                      ) : (
                        <span className="text-slate-500 italic">UNKNOWN GPS</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      {incident.assigned_responder_name ? (
                        <span className="text-indigo-300 font-medium text-xs flex items-center gap-1">
                          <span>👮</span> {incident.assigned_responder_name}
                        </span>
                      ) : (
                        <span className="text-slate-500 text-xs italic">Unassigned</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400">
                      {new Date(incident.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      <div className="text-[10px] text-slate-500">
                        {new Date(incident.created_at).toLocaleDateString()}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setSelectedIncident(incident);
                        }}
                        className="px-3 py-1.5 text-xs font-semibold rounded-lg bg-cyan-600/20 hover:bg-cyan-600 text-cyan-300 hover:text-white border border-cyan-500/30 transition-all shadow"
                      >
                        Manage Dispatch
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Incident Detail Modal */}
      {selectedIncident && (
        <IncidentDetailModal
          incident={selectedIncident}
          onClose={() => setSelectedIncident(null)}
          onIncidentUpdated={(updated) => {
            setSelectedIncident(updated);
            setIncidents((prev) => prev.map((i) => (i.id === updated.id ? updated : i)));
          }}
        />
      )}
    </div>
  );
};
export default IncidentsPage;
