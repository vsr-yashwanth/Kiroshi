import React, { useEffect, useState } from 'react';
import { RiskAssessment, LiveTouristPosition } from '../types';
import { api } from '../services/api';

interface RiskInspectorModalProps {
  tourist: LiveTouristPosition | null;
  onClose: () => void;
}

export const RiskInspectorModal: React.FC<RiskInspectorModalProps> = ({ tourist, onClose }) => {
  const [currentRisk, setCurrentRisk] = useState<RiskAssessment | null>(null);
  const [history, setHistory] = useState<RiskAssessment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tourist) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    Promise.all([
      api.getCurrentRisk(tourist.tourist_id).catch(() => null),
      api.getTripRiskHistory(tourist.trip_id, 20).catch(() => []),
    ]).then(([risk, hist]) => {
      if (isMounted) {
        setCurrentRisk(risk);
        setHistory(hist);
        setLoading(false);
      }
    }).catch(err => {
      if (isMounted) {
        setError(err.message || 'Failed to load risk assessment');
        setLoading(false);
      }
    });

    return () => {
      isMounted = false;
    };
  }, [tourist]);

  if (!tourist) return null;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'SAFE':
        return '#10B981';
      case 'LOW':
        return '#3B82F6';
      case 'MEDIUM':
        return '#F59E0B';
      case 'HIGH':
        return '#F97316';
      case 'CRITICAL':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  const getActionBadgeColor = (action: string) => {
    switch (action) {
      case 'ESCALATE_FOR_HUMAN_REVIEW':
        return 'bg-red-500/20 text-red-400 border-red-500/40';
      case 'CONTACT_TOURIST':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/40';
      case 'REVIEW':
        return 'bg-amber-500/20 text-amber-400 border-amber-500/40';
      case 'MONITOR':
      default:
        return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40';
    }
  };

  const activeLevel = currentRisk?.risk_level || tourist.risk_level || 'SAFE';
  const activeScore = currentRisk?.risk_score ?? tourist.risk_score ?? 0.0;
  const levelColor = getRiskColor(activeLevel);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-[#121827] border border-white/10 rounded-2xl w-full max-w-2xl overflow-hidden shadow-2xl my-8">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/10 bg-white/5">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-white tracking-wide">{tourist.tourist_name}</h2>
              <span
                className="px-2.5 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider border"
                style={{
                  color: levelColor,
                  borderColor: `${levelColor}60`,
                  backgroundColor: `${levelColor}15`,
                }}
              >
                {activeLevel} RISK
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Trip: <span className="text-slate-300 font-medium">{tourist.trip_title}</span> • Telemetry: <span className="font-mono text-indigo-400">{tourist.latitude.toFixed(4)}, {tourist.longitude.toFixed(4)}</span>
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-white/10 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Content */}
        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center text-slate-400">
              <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mb-3"></div>
              <p className="text-sm">Calculating transparent risk metrics...</p>
            </div>
          ) : error ? (
            <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          ) : (
            <>
              {/* Score & Gauge Cards */}
              <div className="grid grid-cols-3 gap-4">
                {/* Risk Score */}
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Normalized Score
                  </div>
                  <div className="text-3xl font-bold font-mono" style={{ color: levelColor }}>
                    {activeScore.toFixed(2)}
                  </div>
                  <div className="w-full bg-slate-800 rounded-full h-2 mt-3 overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${Math.min(100, Math.max(5, activeScore * 100))}%`,
                        backgroundColor: levelColor,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-slate-500 mt-1 font-mono">
                    <span>0.00 (SAFE)</span>
                    <span>1.00 (CRIT)</span>
                  </div>
                </div>

                {/* Model Confidence */}
                <div className="p-4 rounded-xl bg-white/5 border border-white/10">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Data Confidence
                  </div>
                  <div className="text-3xl font-bold font-mono text-white">
                    {currentRisk ? `${Math.round(currentRisk.confidence * 100)}%` : '--'}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-3 leading-tight">
                    Sensor accuracy: ±{tourist.accuracy.toFixed(1)}m • Freshness: {tourist.freshness}
                  </p>
                </div>

                {/* Recommended Action */}
                <div className="p-4 rounded-xl bg-white/5 border border-white/10 flex flex-col justify-between">
                  <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                    Recommended Action
                  </div>
                  <div>
                    <span className={`inline-block px-3 py-1.5 rounded-lg text-xs font-bold border tracking-wider uppercase ${getActionBadgeColor(currentRisk?.recommended_action || 'MONITOR')}`}>
                      {currentRisk?.recommended_action || 'MONITOR'}
                    </span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-2">
                    Human verification required prior to dispatch.
                  </p>
                </div>
              </div>

              {/* Natural Language Explanation */}
              {currentRisk?.explanation && (
                <div className="p-4 rounded-xl bg-indigo-500/10 border border-indigo-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-300">
                      Explainable Risk Assessment
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {currentRisk.explanation}
                  </p>
                  <div className="text-[11px] text-slate-400 mt-2 font-mono">
                    Model Version: {currentRisk.model_version} • Evaluated: {new Date(currentRisk.created_at).toLocaleTimeString()}
                  </div>
                </div>
              )}

              {/* Contributing Signals Breakdown */}
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                  Contributing Signals
                </h3>
                {currentRisk?.contributing_signals && currentRisk.contributing_signals.length > 0 ? (
                  <div className="space-y-2">
                    {currentRisk.contributing_signals.map((sig, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-3 rounded-xl bg-white/5 border border-white/10 text-xs"
                      >
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white uppercase tracking-wide">
                              {sig.signal_type.replace(/_/g, ' ')}
                            </span>
                            <span className="text-slate-400">
                              ({sig.raw_value} {sig.unit})
                            </span>
                          </div>
                          <p className="text-slate-300 text-[11px]">{sig.description}</p>
                        </div>
                        <div className="text-right">
                          <div className="font-mono font-bold text-slate-200">
                            +{sig.contribution.toFixed(2)}
                          </div>
                          <div className="text-[10px] text-slate-500">
                            weight: {sig.weight}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="p-4 rounded-xl bg-white/5 border border-white/10 text-xs text-slate-400 text-center">
                    All extracted signals are within nominal threshold parameters.
                  </div>
                )}
              </div>

              {/* Risk Evaluation History Timeline */}
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
                  Recent Risk Evaluations ({history.length})
                </h3>
                {history.length > 0 ? (
                  <div className="space-y-2">
                    {history.slice(0, 5).map((h) => {
                      const hColor = getRiskColor(h.risk_level);
                      return (
                        <div
                          key={h.id}
                          className="flex items-center justify-between p-2.5 rounded-xl bg-white/5 border border-white/10 text-xs"
                        >
                          <div className="flex items-center gap-3">
                            <span
                              className="w-2.5 h-2.5 rounded-full"
                              style={{ backgroundColor: hColor }}
                            />
                            <span className="font-bold text-slate-300">
                              {h.risk_level} ({h.risk_score.toFixed(2)})
                            </span>
                            <span className="text-slate-400 truncate max-w-xs text-[11px]">
                              {h.explanation}
                            </span>
                          </div>
                          <div className="text-slate-500 font-mono text-[11px]">
                            {new Date(h.created_at).toLocaleTimeString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <div className="p-3 text-xs text-slate-500 text-center">
                    No prior risk evaluations recorded for this trip.
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-white/10 bg-white/5 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition-colors"
          >
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
