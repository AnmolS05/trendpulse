import React from 'react';
import { AlertCircle, Zap, ShieldCheck, Award } from 'lucide-react';

const MetricsGrid = ({ activeAlerts, avgScore, avgConfidence }) => {
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
          <span>Scanned across US and Indian equities</span>
        </div>
      </div>

      {/* Metric 2: Average Meme Score */}
      <div className="bg-[#151d30]/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-slate-700">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">Avg Meme Score</h3>
            <p className="text-4xl font-black text-white mt-2 tracking-tight">
              {avgScore}
              <span className="text-sm font-medium text-slate-400 ml-1">/ 105</span>
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

      {/* Metric 3: Average Confidence rating */}
      <div className="bg-[#151d30]/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-slate-700">
        <div className="flex items-start justify-between">
          <div>
            <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider">Avg Signal Confidence</h3>
            <p className="text-4xl font-black text-emerald-400 mt-2 tracking-tight">
              {avgConfidence}
              <span className="text-sm font-medium text-slate-400 ml-1">%</span>
            </p>
          </div>
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-400">
            <Award className="w-5 h-5" />
          </div>
        </div>
        <div className="mt-4 flex items-center space-x-1.5 text-xs text-slate-400 font-semibold">
          <span>Derived from multi-source validation checks</span>
        </div>
      </div>

    </div>
  );
};

export default MetricsGrid;
