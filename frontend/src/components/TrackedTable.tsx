import React from 'react';
import { Table, Clock, ShieldAlert, Sparkles } from 'lucide-react';
import { TrackedObject } from '../types';
import { getColorForId } from '../utils/colors';

interface TrackedTableProps {
  trackedObjects: TrackedObject[];
}

export const TrackedTable: React.FC<TrackedTableProps> = ({ trackedObjects }) => {
  return (
    <div className="glass-panel rounded-2xl border border-white/10 p-5 shadow-glass space-y-4">
      {/* Table Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Table className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-bold text-slate-100 uppercase tracking-wider">Active Tracked Objects</h3>
        </div>
        <div className="flex items-center space-x-2 text-xs font-mono text-cyan-400 bg-cyan-500/10 px-2.5 py-1 rounded-full border border-cyan-500/20">
          <Sparkles className="w-3 h-3" />
          <span>{trackedObjects.length} OBJECTS IN FRAME</span>
        </div>
      </div>

      {/* Table Content */}
      {trackedObjects.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-white/10 text-slate-400 uppercase tracking-wider">
                <th className="pb-3 font-semibold">Track ID</th>
                <th className="pb-3 font-semibold">Class</th>
                <th className="pb-3 font-semibold">Confidence</th>
                <th className="pb-3 font-semibold">Bounding Box [x1, y1, x2, y2]</th>
                <th className="pb-3 font-semibold text-right">Time-in-Frame</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {trackedObjects.map((obj) => {
                const color = getColorForId(obj.id);
                const durationSeconds = (obj.duration_frames / 25).toFixed(1);

                return (
                  <tr key={obj.id} className="hover:bg-white/5 transition-colors group">
                    {/* Track ID badge */}
                    <td className="py-3">
                      <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md text-slate-950 font-bold" style={{ backgroundColor: color }}>
                        <span>#{obj.id}</span>
                      </div>
                    </td>

                    {/* Class Name */}
                    <td className="py-3 text-slate-200 capitalize font-sans font-semibold">
                      {obj.class_name}
                    </td>

                    {/* Confidence Score */}
                    <td className="py-3">
                      <div className="flex items-center space-x-2">
                        <div className="w-16 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                          <div
                            className="bg-cyan-400 h-full rounded-full"
                            style={{ width: `${Math.round(obj.confidence * 100)}%` }}
                          />
                        </div>
                        <span className="text-cyan-300 font-bold">{Math.round(obj.confidence * 100)}%</span>
                      </div>
                    </td>

                    {/* Bounding Box Coordinates */}
                    <td className="py-3 text-slate-400 text-[11px]">
                      [{obj.bbox.map(c => Math.round(c)).join(', ')}]
                    </td>

                    {/* Time in Frame */}
                    <td className="py-3 text-right">
                      <div className="inline-flex items-center space-x-1 text-slate-300">
                        <Clock className="w-3 h-3 text-slate-500" />
                        <span>{durationSeconds}s</span>
                        <span className="text-slate-500 text-[10px]">({obj.duration_frames}f)</span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="py-8 text-center text-slate-500 space-y-2">
          <ShieldAlert className="w-8 h-8 mx-auto text-slate-600" />
          <p className="text-xs font-mono">No active objects currently being tracked in the viewport.</p>
        </div>
      )}
    </div>
  );
};
