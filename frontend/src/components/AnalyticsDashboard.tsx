import React from 'react';
import { Activity, Target, Layers, Cpu } from 'lucide-react';
import { SystemTelemetry } from '../types';

interface AnalyticsDashboardProps {
  telemetry: SystemTelemetry;
}

export const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ telemetry }) => {
  const classEntries = Object.entries(telemetry.class_counts || {});
  const maxCount = Math.max(...classEntries.map(([, count]) => count), 1);

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
      {/* 1. FPS & Processing Speed */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10 flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-[11px] font-mono uppercase text-slate-400">FPS / Processing</span>
          <div className="text-2xl font-bold font-mono text-cyan-400 tracking-tight">
            {telemetry.fps} <span className="text-xs text-slate-400 font-sans">FPS</span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono">
            Inf: {telemetry.inference_time_ms}ms
          </p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
          <Activity className="w-5 h-5" />
        </div>
      </div>

      {/* 2. Active Tracked Objects */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10 flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-[11px] font-mono uppercase text-slate-400">Currently Tracked</span>
          <div className="text-2xl font-bold font-mono text-violet-400 tracking-tight">
            {telemetry.active_tracks_count} <span className="text-xs text-slate-400 font-sans font-normal">Active</span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono">
            Tracker: {telemetry.tracker.toUpperCase()}
          </p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-violet-500/10 border border-violet-500/30 flex items-center justify-center text-violet-400">
          <Target className="w-5 h-5" />
        </div>
      </div>

      {/* 3. Total Unique Objects Seen */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10 flex items-center justify-between">
        <div className="space-y-1">
          <span className="text-[11px] font-mono uppercase text-slate-400">Total Detected</span>
          <div className="text-2xl font-bold font-mono text-emerald-400 tracking-tight">
            {telemetry.total_objects_count} <span className="text-xs text-slate-400 font-sans font-normal">Objects</span>
          </div>
          <p className="text-[10px] text-slate-500 font-mono">
            Cumulative Session
          </p>
        </div>
        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
          <Layers className="w-5 h-5" />
        </div>
      </div>

      {/* 4. Per-Class Distribution Live Bar Breakdown */}
      <div className="glass-panel p-4 rounded-2xl border border-white/10 flex flex-col justify-between">
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono uppercase text-slate-400">Per-Class Counts</span>
          <Cpu className="w-4 h-4 text-slate-500" />
        </div>
        {classEntries.length > 0 ? (
          <div className="space-y-1.5 max-h-16 overflow-y-auto pr-1">
            {classEntries.map(([cls, count]) => (
              <div key={cls} className="flex items-center space-x-2 text-xs font-mono">
                <span className="w-16 truncate text-slate-300 capitalize">{cls}:</span>
                <div className="flex-1 bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div 
                    className="bg-gradient-to-r from-cyan-400 to-violet-500 h-full rounded-full transition-all duration-300"
                    style={{ width: `${(count / maxCount) * 100}%` }}
                  />
                </div>
                <span className="text-cyan-400 font-bold w-4 text-right">{count}</span>
              </div>
            ))}
          </div>
        ) : (
          <span className="text-xs text-slate-500 font-mono italic">No objects detected yet</span>
        )}
      </div>
    </div>
  );
};
