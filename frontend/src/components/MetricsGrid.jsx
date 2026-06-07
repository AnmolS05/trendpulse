import React from 'react';
import { AlertCircle, Zap, ShieldCheck } from 'lucide-react';

const MetricsGrid = ({ activeAlerts, avgScore }) => {
  // Determine health color indicator
  const getStatusColor = (count) => {
    if (count > 5) return 'text-rose-400 bg-rose-500/10 border-rose-500/20';
    if (count > 0) return 'text-amber-400 bg-amber-500/10 border-amber-500/20';
    return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      
      {/* Metric 1: Active Alerts count */}
      <div className="bg-[#151d30]/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-slate-700">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">Active Alerts</h3>
            <p className="text-4xl font-black text-white mt-2 tracking-tight">{activeAlerts}</p>
          </div>
          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl text-blue-400">
            <AlertCircle className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-4 flex items-center space-x-1.5 text-xs text-slate-400 font-semibold">
          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-ping"></span>
          <span>Scanned across seeded equity pairs</span>
        </div>
      </div>

      {/* Metric 2: Average Meme Score */}
      <div className="bg-[#151d30]/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-slate-700">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">Avg Meme Score</h3>
            <p className="text-4xl font-black text-white mt-2 tracking-tight">
              {avgScore}
              <span className="text-sm font-medium text-slate-400 ml-1">/ 100</span>
            </p>
          </div>
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-indigo-400">
            <Zap className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-4 flex items-center text-xs text-slate-400 font-semibold">
          <span className="text-indigo-400 mr-1.5 font-bold">FOMO Intensity:</span>
          <span>{avgScore >= 75 ? 'HIGH' : avgScore >= 50 ? 'MODERATE' : 'LOW'}</span>
        </div>
      </div>

      {/* Metric 3: System / Connection status */}
      <div className="bg-[#151d30]/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-slate-700">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">Scanner Status</h3>
            <div className="flex items-center space-x-2 mt-2">
              <span className="relative flex h-3 w-3">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
              </span>
              <p className="text-2xl font-black text-emerald-400 tracking-tight">OPERATIONAL</p>
            </div>
          </div>
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <ShieldCheck className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-4 flex items-center space-x-1.5 text-xs text-slate-400 font-semibold">
          <span>Continuous Metaphone checks online</span>
        </div>
      </div>

    </div>
  );
};

export default MetricsGrid;
