import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, TrendingUp, Hash, DollarSign, ShieldAlert, 
  ChevronDown, ChevronUp, Info, Award, HelpCircle, CheckCircle, 
  Calendar, Link2, Newspaper, Clock, RefreshCw
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const AlertCard = ({ alert }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [evidence, setEvidence] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loadingEvidence, setLoadingEvidence] = useState(false);

  // Score styling config
  const getScoreColor = (score) => {
    if (score >= 80) return {
      text: 'text-rose-400',
      bg: 'bg-rose-500/10 border-rose-500/30',
      glow: 'shadow-[0_0_15px_-3px_rgba(244,63,94,0.3)]',
      progress: 'bg-rose-500'
    };
    if (score >= 60) return {
      text: 'text-amber-400',
      bg: 'bg-amber-500/10 border-amber-500/30',
      glow: 'shadow-[0_0_15px_-3px_rgba(245,158,11,0.3)]',
      progress: 'bg-amber-500'
    };
    return {
      text: 'text-blue-400',
      bg: 'bg-blue-500/10 border-blue-500/30',
      glow: 'shadow-[0_0_15px_-3px_rgba(59,130,246,0.3)]',
      progress: 'bg-blue-500'
    };
  };

  const style = getScoreColor(alert.meme_score);
  const confidenceStyle = getScoreColor(alert.confidence_score);

  // Parse list of drivers/weaknesses
  const drivers = alert.confidence_drivers ? alert.confidence_drivers.split(',').filter(Boolean) : [];
  const weaknesses = alert.confidence_weaknesses ? alert.confidence_weaknesses.split(',').filter(Boolean) : [];
  const riskFlagsList = alert.risk_flags ? alert.risk_flags.split(',').filter(Boolean) : [];

  // Fetch timeline and evidence when expanding card details
  useEffect(() => {
    if (showDetails && !evidence) {
      setLoadingEvidence(true);
      
      const headers = {
        'X-API-KEY': import.meta.env.VITE_API_KEY || 'dev_secret_key_123'
      };
      
      const fetchEvidence = fetch(`${API_BASE}/api/alerts/${alert.id}/evidence`, { headers })
        .then(res => res.json())
        .then(data => setEvidence(data))
        .catch(err => console.error("Error fetching evidence details:", err));
        
      const fetchTimeline = fetch(`${API_BASE}/api/alerts/${alert.id}/timeline`, { headers })
        .then(res => res.json())
        .then(data => setTimeline(data))
        .catch(err => console.error("Error fetching timeline details:", err));
        
      Promise.all([fetchEvidence, fetchTimeline]).finally(() => {
        setLoadingEvidence(false);
      });
    }
  }, [showDetails, alert.id, evidence]);

  // Format timestamp nicely
  const formattedTime = new Date(alert.timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });

  const formattedDate = new Date(alert.timestamp).toLocaleDateString([], {
    month: 'short',
    day: 'numeric'
  });

  return (
    <div className={`group bg-[#151d30]/60 backdrop-blur-md border border-slate-800/80 rounded-2xl p-6 relative overflow-hidden transition-all duration-300 hover:border-slate-700 ${style.glow} hover:shadow-[0_20px_35px_-15px_rgba(0,0,0,0.5)] flex flex-col justify-between`}>
      {alert.is_predictive === 1 && (
        <div className="absolute top-0 right-0 bg-purple-600/20 text-purple-400 border-l border-b border-purple-500/30 px-3 py-1 rounded-bl-xl text-[9px] font-extrabold uppercase tracking-wider animate-pulse">
          Pre-Breakout Candidate
        </div>
      )}
      <div>
        {/* Top Header Row */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <span className="text-[9px] px-2 py-0.5 rounded-full font-bold bg-slate-800 text-slate-400 border border-slate-700/60 uppercase tracking-wider">
              {alert.ticker_symbol.includes('.') ? 'NSE/BSE' : 'NASDAQ/NYSE'}
            </span>
            <h3 className="text-2xl font-extrabold text-white mt-1 flex items-center tracking-tight">
              {alert.ticker_symbol}
              {alert.volume_surge_multiplier >= 3.0 && (
                <span className="ml-2 flex h-2.5 w-2.5 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
                </span>
              )}
            </h3>
            <p className="text-slate-400 text-xs font-semibold truncate max-w-[150px]" title={alert.company_name}>
              {alert.company_name || 'Unknown Equities'}
            </p>
          </div>

          {/* Scores Side-by-Side */}
          <div className="flex space-x-2">
            {alert.is_predictive === 1 ? (
              <div className="flex flex-col items-center px-2.5 py-1 rounded-xl border bg-purple-500/10 border-purple-500/30 text-center min-w-[65px] shadow-[0_0_15px_-3px_rgba(168,85,247,0.3)]">
                <span className="text-[8px] uppercase font-extrabold tracking-wider text-slate-400">Breakout Prob</span>
                <span className="text-base font-black text-purple-400">{Math.round(alert.surge_probability || 0)}%</span>
              </div>
            ) : (
              <div className={`flex flex-col items-center px-2.5 py-1 rounded-xl border ${style.bg} text-center min-w-[65px]`}>
                <span className="text-[8px] uppercase font-extrabold tracking-wider text-slate-400">Meme Score</span>
                <span className={`text-base font-black ${style.text}`}>{Math.round(alert.meme_score)}</span>
              </div>
            )}
            
            <div className={`flex flex-col items-center px-2.5 py-1 rounded-xl border ${confidenceStyle.bg} text-center min-w-[65px]`}>
              <span className="text-[8px] uppercase font-extrabold tracking-wider text-slate-400">Confidence</span>
              <span className={`text-base font-black ${confidenceStyle.text}`}>{Math.round(alert.confidence_score)}%</span>
            </div>
          </div>
        </div>

        {/* Visual Topic Alignment Flow */}
        <div className="my-4 p-3 bg-slate-950/70 border border-slate-900 rounded-xl flex items-center justify-between">
          <div className="flex-1 min-w-0">
            <p className="text-[8px] text-slate-500 font-extrabold uppercase tracking-wider">Trending Topic</p>
            <p className="text-xs font-black text-slate-300 truncate">{alert.brand_name}</p>
          </div>
          <div className="px-2 text-indigo-500/70 animate-pulse font-bold text-xs">Phonetic Confusion</div>
          <div className="flex-1 text-right min-w-0">
            <p className="text-[8px] text-slate-500 font-extrabold uppercase tracking-wider">Listed Ticker</p>
            <p className="text-xs font-black text-blue-400 truncate">{alert.ticker_symbol}</p>
          </div>
        </div>

        {/* Primary Metrics Row */}
        <div className="grid grid-cols-2 gap-3 my-3">
          <div className="p-2.5 bg-slate-900/40 border border-slate-800/40 rounded-xl flex items-center space-x-3">
            {alert.is_predictive === 1 ? (
              <Clock className="w-4 h-4 text-purple-400 shrink-0" />
            ) : (
              <TrendingUp className="w-4 h-4 text-blue-400 shrink-0" />
            )}
            <div>
              <span className="text-[9px] text-slate-500 uppercase font-bold block">
                {alert.is_predictive === 1 ? 'Est. Lead Window' : 'Vol Surge'}
              </span>
              <p className="text-sm font-black text-white">
                {alert.is_predictive === 1 
                  ? `${alert.est_lead_time_hours ? alert.est_lead_time_hours.toFixed(1) : 'N/A'} hrs` 
                  : `${alert.volume_surge_multiplier.toFixed(2)}x`
                }
              </p>
            </div>
          </div>
          
          <div className="p-2.5 bg-slate-900/40 border border-slate-800/40 rounded-xl flex items-center space-x-3">
            <Hash className="w-4 h-4 text-indigo-400 shrink-0" />
            <div>
              <span className="text-[9px] text-slate-500 uppercase font-bold block">
                {alert.is_predictive === 1 ? 'Soc Accel' : 'Velocity'}
              </span>
              <p className="text-sm font-black text-white">
                {alert.is_predictive === 1 
                  ? `+${alert.social_acceleration ? alert.social_acceleration.toFixed(2) : '0.00'}x / hr`
                  : `${alert.social_velocity.toFixed(1)}x`
                }
              </p>
            </div>
          </div>
        </div>

        {/* Risk Warning Banners */}
        {riskFlagsList.length > 0 && (
          <div className="mt-3 p-3 bg-rose-500/5 border border-rose-500/10 rounded-xl flex items-start space-x-2">
            <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <div className="text-[10px] text-rose-300 font-medium">
              <span className="font-bold text-rose-400 block uppercase tracking-wider text-[9px] mb-0.5">Alert Risk Warning</span>
              {alert.risk_summary}
            </div>
          </div>
        )}
      </div>

      <div>
        {/* Footer trigger */}
        <div className="mt-4 pt-3 border-t border-slate-800/60 flex items-center justify-between">
          <div className="flex items-center space-x-1.5 text-[10px] text-slate-500 font-medium">
            <Clock className="w-3.5 h-3.5" />
            <span>Spiked at {formattedTime} ({formattedDate})</span>
          </div>
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-xs font-bold text-blue-400 hover:text-blue-300 transition-colors flex items-center space-x-0.5"
          >
            <span>{showDetails ? "Hide Trails" : "Show Evidence"}</span>
            {showDetails ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
          </button>
        </div>

        {/* Expanded Evidence Trails & Ingest timeline */}
        {showDetails && (
          <div className="mt-4 pt-4 border-t border-slate-800 space-y-4 text-xs animate-slideDown">
            {/* Explanation text */}
            <div className="p-3 bg-slate-900/60 rounded-xl border border-slate-800 text-[11px] text-slate-300 leading-relaxed">
              <p className="font-bold text-white mb-1 flex items-center">
                <Info className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
                Signal Explanation
              </p>
              {alert.explanation}
            </div>

            {/* Confidence Drivers & Weaknesses lists */}
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-850">
                <h5 className="text-[9px] uppercase font-bold text-emerald-400 tracking-wider mb-2 flex items-center">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Confidence Drivers
                </h5>
                {drivers.length === 0 ? (
                  <p className="text-[10px] text-slate-500 italic">None logged</p>
                ) : (
                  <ul className="space-y-1.5 text-[10px] text-slate-300 font-medium">
                    {drivers.map((d, i) => (
                      <li key={i} className="flex items-start">
                        <span className="text-emerald-400 mr-1.5">•</span>
                        <span>{d}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
              
              <div className="bg-slate-950/30 p-3 rounded-xl border border-slate-850">
                <h5 className="text-[9px] uppercase font-bold text-amber-400 tracking-wider mb-2 flex items-center">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  Confidence Weaknesses
                </h5>
                {weaknesses.length === 0 ? (
                  <p className="text-[10px] text-slate-500 italic">None logged</p>
                ) : (
                  <ul className="space-y-1.5 text-[10px] text-slate-300 font-medium">
                    {weaknesses.map((w, i) => (
                      <li key={i} className="flex items-start">
                        <span className="text-amber-400 mr-1.5">•</span>
                        <span>{w}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </div>

            {/* Dynamic Evidence details */}
            {loadingEvidence ? (
              <div className="flex items-center justify-center py-6">
                <RefreshCw className="w-4 h-4 animate-spin text-slate-500" />
                <span className="text-xs text-slate-500 ml-2">Harvesting logs...</span>
              </div>
            ) : (
              <>
                {/* News Catalysts list */}
                {evidence?.news_articles?.length > 0 && (
                  <div className="bg-slate-950/40 p-3 border border-slate-900 rounded-xl space-y-2">
                    <h5 className="text-[9px] uppercase font-bold text-blue-400 tracking-wider flex items-center border-b border-slate-900 pb-1">
                      <Newspaper className="w-3.5 h-3.5 mr-1.5 text-blue-400" />
                      Matched News Catalysts ({evidence.news_articles.length})
                    </h5>
                    <div className="space-y-2 max-h-[140px] overflow-y-auto pr-1">
                      {evidence.news_articles.map((art) => (
                        <div key={art.id} className="p-2 bg-slate-900/60 rounded border border-slate-850 text-[10px]">
                          <a 
                            href={art.url} 
                            target="_blank" 
                            rel="noopener noreferrer" 
                            className="font-bold text-slate-200 hover:text-blue-400 flex items-center transition-colors"
                          >
                            <Link2 className="w-3 h-3 mr-1 text-slate-500 shrink-0" />
                            <span className="truncate">{art.title}</span>
                          </a>
                          <div className="flex justify-between text-[9px] text-slate-500 mt-1">
                            <span>Source: {art.source}</span>
                            <span>{new Date(art.published_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Timeline display */}
                {timeline.length > 0 && (
                  <div className="bg-slate-950/40 p-3 border border-slate-900 rounded-xl">
                    <h5 className="text-[9px] uppercase font-bold text-indigo-400 tracking-wider flex items-center border-b border-slate-900 pb-1 mb-2">
                      <Clock className="w-3.5 h-3.5 mr-1.5 text-indigo-400" />
                      Ingestion Log Timeline
                    </h5>
                    <div className="relative border-l border-slate-800 pl-4 ml-2 space-y-3.5 py-1">
                      {timeline.map((event, index) => (
                        <div key={index} className="relative text-[10px]">
                          <span className="absolute -left-[21px] top-1 w-2.5 h-2.5 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
                            <span className="w-1 h-1 rounded-full bg-blue-500"></span>
                          </span>
                          <span className="text-[9px] text-slate-500 font-medium block">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </span>
                          <span className="font-extrabold text-slate-300 block">{event.event}</span>
                          <span className="text-slate-400 block mt-0.5">{event.details}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default React.memo(AlertCard);
