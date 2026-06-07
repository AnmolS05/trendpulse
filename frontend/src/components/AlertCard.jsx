import React, { useState } from 'react';
import { AlertTriangle, TrendingUp, Hash, DollarSign, ShieldAlert, ChevronRight, Info, Award } from 'lucide-react';

const AlertCard = ({ alert }) => {
  const [showDetails, setShowDetails] = useState(false);

  // Check if stock is microcap (< $15 Million) for liquidity warnings
  const isMicroCap = alert.market_cap !== null && alert.market_cap < 15.0;

  // Determine priority color based on Meme Score
  const getScoreColor = (score) => {
    if (score >= 80) return {
      text: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/30',
      glow: 'shadow-[0_0_15px_-3px_rgba(244,63,94,0.3)]',
      progress: 'bg-gradient-to-r from-rose-500 to-orange-400'
    };
    if (score >= 60) return {
      text: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/30',
      glow: 'shadow-[0_0_15px_-3px_rgba(245,158,11,0.3)]',
      progress: 'bg-gradient-to-r from-amber-500 to-yellow-400'
    };
    return {
      text: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/30',
      glow: 'shadow-[0_0_15px_-3px_rgba(59,130,246,0.3)]',
      progress: 'bg-gradient-to-r from-blue-500 to-cyan-400'
    };
  };

  const style = getScoreColor(alert.meme_score);

  // Format timestamp nicely
  const formattedTime = new Date(alert.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  return (
    <div className={`group bg-[#151d30]/60 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:-translate-y-1 hover:border-slate-700 ${style.glow} hover:shadow-[0_20px_35px_-15px_rgba(0,0,0,0.5)]`}>
      
      {/* Top Header Row */}
      <div className="flex justify-between items-start mb-4">
        <div>
          <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-slate-800 text-slate-400 border border-slate-700/60 uppercase tracking-wider">
            {alert.ticker_symbol.includes('.') ? 'BSE/NSE' : 'NASDAQ/NYSE'}
          </span>
          <h3 className="text-2xl font-extrabold text-white mt-1.5 flex items-center tracking-tight">
            {alert.ticker_symbol}
            {alert.volume_surge_multiplier >= 3.0 && (
              <span className="ml-2 flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-rose-500"></span>
              </span>
            )}
          </h3>
          <p className="text-slate-400 text-xs font-semibold mt-0.5 truncate max-w-[170px]" title={alert.company_name}>
            {alert.company_name}
          </p>
        </div>

        {/* Meme Score Badge */}
        <div className={`flex flex-col items-end px-3 py-1.5 rounded-xl border ${style.bg} ${style.glow} text-center`}>
          <span className="text-[10px] uppercase font-extrabold tracking-widest text-slate-400">Meme Score</span>
          <span className={`text-xl font-black ${style.text}`}>{Math.round(alert.meme_score)}</span>
        </div>
      </div>

      {/* Visual Alignment Flow */}
      <div className="my-5 p-3.5 bg-slate-950/60 border border-slate-900 rounded-xl flex items-center justify-between">
        <div className="flex-1">
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Trending Topic</p>
          <p className="text-sm font-bold text-slate-200 truncate">{alert.brand_name}</p>
        </div>
        <div className="px-2 flex items-center text-slate-500">
          <ChevronRight className="w-5 h-5 text-blue-500/70 animate-pulse" />
        </div>
        <div className="flex-1 text-right">
          <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Confused Stock</p>
          <p className="text-sm font-bold text-blue-400 truncate">{alert.ticker_symbol}</p>
        </div>
      </div>

      {/* Primary Metrics Row */}
      <div className="grid grid-cols-2 gap-4 my-4">
        <div className="p-3 bg-slate-900/50 border border-slate-800/50 rounded-xl">
          <div className="flex items-center text-[11px] text-slate-400 font-medium mb-1">
            <TrendingUp className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
            <span>Volume Surge</span>
          </div>
          <p className="text-lg font-black text-white">{alert.volume_surge_multiplier.toFixed(1)}x</p>
        </div>
        
        <div className="p-3 bg-slate-900/50 border border-slate-800/50 rounded-xl">
          <div className="flex items-center text-[11px] text-slate-400 font-medium mb-1">
            <Hash className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
            <span>Social Velocity</span>
          </div>
          <p className="text-lg font-black text-white">{alert.social_velocity.toFixed(1)}x</p>
        </div>
      </div>

      {/* Dynamic Warnings / Badges Row */}
      <div className="flex flex-wrap gap-2 mt-4 min-h-[26px]">
        {isMicroCap && (
          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-[10px] font-extrabold bg-rose-500/10 border border-rose-500/30 text-rose-400 animate-pulse">
            <ShieldAlert className="w-3 h-3" />
            <span>⚠️ SLIPPAGE RISK</span>
          </span>
        )}

        <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-md text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700/50">
          <Award className="w-3 h-3 text-emerald-400" />
          <span>{alert.market_cap ? `$${alert.market_cap.toFixed(1)}M Cap` : 'N/A Cap'}</span>
        </span>
      </div>

      {/* Collapsible Score Details Indicator */}
      <div className="mt-5 pt-3 border-t border-slate-800/60 flex items-center justify-between">
        <span className="text-[10px] text-slate-500 font-medium">Spiked at {formattedTime}</span>
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="text-[11px] font-bold text-blue-400 hover:text-blue-300 transition-colors flex items-center space-x-1"
        >
          <Info className="w-3.5 h-3.5" />
          <span>{showDetails ? "Hide Metrics" : "Details"}</span>
        </button>
      </div>

      {/* Expanded Metrics Details Box */}
      {showDetails && (
        <div className="mt-4 p-4 bg-slate-950/80 border border-slate-900 rounded-xl space-y-3 text-xs animate-slideDown">
          <h4 className="font-extrabold text-white text-[11px] uppercase tracking-wider border-b border-slate-900 pb-1.5 text-slate-400">
            Heuristics Score Calculation
          </h4>
          
          <div className="space-y-2.5">
            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Social Attention Velocity (20% weight)</span>
                <span className="text-white font-semibold">{((alert.social_velocity / 10.0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div className="bg-indigo-500 h-1.5 rounded-full" style={{ width: `${Math.min((alert.social_velocity / 10.0) * 100, 100)}%` }}></div>
              </div>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 mb-1">
                <span>Market Volume Anomaly (30% weight)</span>
                <span className="text-white font-semibold">{((alert.volume_surge_multiplier / 5.0) * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                <div className="bg-blue-500 h-1.5 rounded-full" style={{ width: `${Math.min((alert.volume_surge_multiplier / 5.0) * 100, 100)}%` }}></div>
              </div>
            </div>

            <div className="flex items-center justify-between text-[11px] text-slate-400 pt-1.5 border-t border-slate-900">
              <span className="flex items-center"><DollarSign className="w-3 h-3 mr-1 text-emerald-400" /> Market Cap Penalty:</span>
              <span className="text-amber-400 font-semibold">
                -{alert.market_cap ? (10 * Math.log10(Math.max(alert.market_cap, 0.1))).toFixed(1) : '0.0'} pts
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertCard;
