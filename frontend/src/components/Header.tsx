import React from 'react';
import { Eye, Activity, Cpu, ShieldCheck } from 'lucide-react';
import { ConnectionStatus } from '../hooks/useWebSocket';
import { StreamSettings } from '../types';

interface HeaderProps {
  connectionStatus: ConnectionStatus;
  latencyMs: number;
  settings: StreamSettings;
}

export const Header: React.FC<HeaderProps> = ({ connectionStatus, latencyMs, settings }) => {
  return (
    <header className="glass-panel sticky top-0 z-50 px-6 py-3 border-b border-white/10 flex items-center justify-between shadow-glass">
      {/* App Logo & Title */}
      <div className="flex items-center space-x-3">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-violet-600 shadow-glow-cyan">
          <Eye className="w-5 h-5 text-black font-bold" />
          <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-cyan-400 animate-pulse-glow" />
        </div>
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-lg font-bold tracking-wider font-sans bg-gradient-to-r from-cyan-400 via-teal-300 to-violet-400 bg-clip-text text-transparent">
              VISION<span className="text-white font-light">AI</span>
            </h1>
            <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/30">
              v1.0 REAL-TIME
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans">Object Detection & Multi-Object Tracking System</p>
        </div>
      </div>

      {/* Active Pipeline Badges */}
      <div className="hidden md:flex items-center space-x-3">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-white/10 text-xs font-mono">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-slate-400">MODEL:</span>
          <span className="text-cyan-300 uppercase font-semibold">{settings.model}</span>
        </div>
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900/60 border border-white/10 text-xs font-mono">
          <Activity className="w-3.5 h-3.5 text-violet-400" />
          <span className="text-slate-400">TRACKER:</span>
          <span className="text-violet-300 uppercase font-semibold">{settings.tracker}</span>
        </div>
      </div>

      {/* Connection & Status Pill */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-white/10 text-xs font-mono">
          <span className={`w-2.5 h-2.5 rounded-full ${
            connectionStatus === 'connected' ? 'bg-emerald-400 animate-pulse-glow shadow-[0_0_8px_#00ff88]' :
            connectionStatus === 'connecting' ? 'bg-amber-400 animate-ping' :
            'bg-rose-500'
          }`} />
          <span className="uppercase text-slate-300 font-medium">{connectionStatus}</span>
          {connectionStatus === 'connected' && (
            <span className="text-[11px] text-cyan-400 border-l border-slate-700 pl-2">
              {latencyMs}ms
            </span>
          )}
        </div>

        <div className="hidden sm:flex items-center space-x-1 text-slate-400 text-xs">
          <ShieldCheck className="w-4 h-4 text-emerald-400" />
          <span>GPU/CPU Acceleration</span>
        </div>
      </div>
    </header>
  );
};
