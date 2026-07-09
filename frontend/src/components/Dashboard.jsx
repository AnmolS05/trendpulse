import React, { useState, useEffect, useCallback } from 'react';
import MetricsGrid from './MetricsGrid';
import AlertCard from './AlertCard';
import { 
  Activity, RefreshCw, AlertCircle, Database, CheckCircle, ShieldCheck, 
  Settings, Award, Sparkles, BarChart2, Plus, Trash2, Eye, ShieldAlert
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Dashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(false);
  const [activeTab, setActiveTab] = useState('active'); // 'active' or 'predictive'
  
  // New Phase 2 & 3 State
  const [config, setConfig] = useState({ 
    strict_real_data: true, 
    allow_simulated_data: false,
    meme_weight_velocity: 20,
    meme_weight_link: 30,
    meme_weight_surge: 30,
    meme_weight_cap: 10,
    global_alert_threshold: 50
  });
  const [sourceHealth, setSourceHealth] = useState([]);
  const [backtestStats, setBacktestStats] = useState(null);
  const [backtesting, setBacktesting] = useState(false);
  const [macroTrends, setMacroTrends] = useState([]);
  
  // Dynamic Admin Panel state
  const [keysStatus, setKeysStatus] = useState({});
  
  // UI Panels toggles
  const [showConfig, setShowConfig] = useState(false);

  const fetchAlerts = useCallback(async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/alerts`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setAlerts(data);
      setError(null);
    } catch (err) {
      console.error("Error fetching alerts:", err);
      setError("Failed to fetch live alerts from server.");
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Fetches the current admin/scanner configurations from backend.
   */
  const fetchConfig = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`, {
        headers: {
          'X-API-KEY': import.meta.env.VITE_API_KEY || 'dev_secret_key_123'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Error fetching config:", err);
    }
  }, []);

  /**
   * Fetches active API credentials status (masked).
   */
  const fetchKeysStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/keys`, {
        headers: {
          'X-API-KEY': import.meta.env.VITE_API_KEY || 'dev_secret_key_123'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setKeysStatus(data);
      }
    } catch (err) {
      console.error("Error fetching keys status:", err);
    }
  }, []);



  /**
   * Fetches source health records for the scraping adapters.
   */
  const fetchSourceHealth = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/health/sources`);
      if (response.ok) {
        const data = await response.json();
        setSourceHealth(data);
      }
    } catch (err) {
      console.error("Error fetching source health:", err);
    }
  }, []);



  const fetchMacroTrends = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/macro-trends`);
      if (response.ok) {
        const data = await response.json();
        setMacroTrends(data);
      }
    } catch (err) {
      console.error("Error fetching macro trends:", err);
    }
  }, []);



  const triggerSync = async () => {
    setIsSyncing(true);
    setSyncSuccess(false);
    try {
      const response = await fetch(`${API_BASE}/api/ingest`, {
        method: 'POST',
        headers: {
          'X-API-KEY': import.meta.env.VITE_API_KEY || 'dev_secret_key_123'
        }
      });
      if (!response.ok) {
        throw new Error(`Sync failed with status: ${response.status}`);
      }
      setSyncSuccess(true);
      fetchSourceHealth();
      setTimeout(() => {
        fetchAlerts();
        fetchMacroTrends();
        setSyncSuccess(false);
      }, 1500);
    } catch (err) {
      console.error("Error running manual sync:", err);
      setError("Failed to trigger manual trend ingestion.");
    } finally {
      setIsSyncing(false);
    }
  };

  /**
   * Updates admin settings configuration and posts to backend.
   * @param {Object} updatedFields - Fields to merge and update.
   */
  const updateConfig = async (updatedFields) => {
    const newConfig = { ...config, ...updatedFields };
    setConfig(newConfig);
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-KEY': import.meta.env.VITE_API_KEY || 'dev_secret_key_123'
        },
        body: JSON.stringify(newConfig)
      });
      if (response.ok) {
        fetchAlerts();
      }
    } catch (err) {
      console.error("Failed to update admin config:", err);
    }
  };



  const runBacktesting = async () => {
    setBacktesting(true);
    try {
      const response = await fetch(`${API_BASE}/api/backtest`, {
        method: 'POST',
        headers: {
          'X-API-KEY': import.meta.env.VITE_API_KEY || 'dev_secret_key_123'
        }
      });
      if (response.ok) {
        const data = await response.json();
        setBacktestStats(data);
      }
    } catch (err) {
      console.error("Error running backtest:", err);
    } finally {
      setBacktesting(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    fetchConfig();
    fetchSourceHealth();
    fetchKeysStatus();
    fetchMacroTrends();
  }, [fetchAlerts, fetchConfig, fetchSourceHealth, fetchKeysStatus, fetchMacroTrends]);

  // Dynamic statistics
  const avgScore = alerts.length
    ? Math.round(alerts.reduce((acc, curr) => acc + curr.meme_score, 0) / alerts.length)
    : 0;
  
  const avgConfidence = alerts.length
    ? Math.round(alerts.reduce((acc, curr) => acc + curr.confidence_score, 0) / alerts.length)
    : 0;

  // Ensure we fall back to a dynamic evaluation if config is loading
  const currentThreshold = config ? config.global_alert_threshold : 30;

  return (
    <div className="min-h-screen bg-[#0b0f19] bg-[radial-gradient(ellipse_80%_80%_at_50%_-20%,rgba(29,78,216,0.15),rgba(255,255,255,0))] text-slate-100 font-sans">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        
        {/* Navigation / Header */}
        <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between pb-6 mb-8 border-b border-slate-800">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-blue-600/10 border border-blue-500/30 rounded-xl">
              <Activity className="h-7 w-7 text-blue-400 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-200 to-white bg-clip-text text-transparent">
                  TrendPulse Pro
                </h1>
                <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-extrabold uppercase">
                  LIVE DATA
                </span>
              </div>
              <p className="text-xs text-slate-400 font-medium">Indian Equities (NSE/BSE) Scanner - Mistaken Identity Predictor via r/IndianStreetBets</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">


            {/* Config Toggle */}
            <button
              onClick={() => setShowConfig(!showConfig)}
              className={`p-2 rounded-lg border transition-all duration-200 ${
                showConfig 
                  ? 'bg-blue-600 text-white border-blue-500' 
                  : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
              title="Admin configuration"
            >
              <Settings className="w-4 h-4" />
            </button>

            {/* Sync Button */}
            <button
              onClick={triggerSync}
              disabled={isSyncing}
              className={`flex items-center space-x-2 px-4 py-2 text-sm font-semibold rounded-lg border transition-all duration-300 ${
                isSyncing
                  ? 'bg-slate-800/80 border-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-blue-600/10 border-blue-500/30 text-blue-400 hover:bg-blue-600/20 hover:border-blue-500'
              }`}
            >
              <RefreshCw className={`w-4 h-4 ${isSyncing ? 'animate-spin' : ''}`} />
              <span>{isSyncing ? 'Scanning...' : 'Scan Now'}</span>
            </button>

            {/* Refresh Button */}
            <button
              onClick={() => { fetchAlerts(); fetchMacroTrends(); }}
              className="p-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-all duration-200"
              title="Refresh alert feed"
            >
              <Database className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Dynamic Admin Settings Box */}
        {showConfig && (
          <div className="mb-8 p-6 bg-[#111827]/80 backdrop-blur-md border border-blue-500/20 rounded-2xl animate-slideDown">
            <h3 className="text-sm font-extrabold uppercase text-blue-400 tracking-wider mb-4 flex items-center">
              <Settings className="w-4 h-4 mr-2" />
              Scanner Engine Configuration
            </h3>
            
            {/* API Key Status Widget */}
            <div className="mb-6">
              <h4 className="text-xs font-bold uppercase text-slate-400 mb-3">API Credentials Configuration Status</h4>
              <div className="grid gap-4 sm:grid-cols-3">
                {Object.entries(keysStatus).map(([keyName, status]) => (
                  <div key={keyName} className="flex items-center justify-between p-2.5 bg-slate-900/60 border border-slate-800 rounded-lg text-xs">
                    <span className="text-slate-400 font-mono text-[10px] uppercase">{keyName.replace(/_/g, ' ')}</span>
                    <span className={`px-2 py-0.5 rounded font-extrabold text-[9px] uppercase ${
                      status === 'configured' 
                        ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' 
                        : 'bg-rose-500/10 border border-rose-500/20 text-rose-400'
                    }`}>
                      {status}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Dynamic Weights Sliders & Threshold Management */}
            <div>
              <h4 className="text-xs font-bold uppercase text-slate-400 mb-4">Scoring Algorithm Weight Settings</h4>
              <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-5">
                
                {/* Velocity Weight */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Velocity Weight</span>
                    <span className="text-blue-400 font-bold">{config.meme_weight_velocity}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={config.meme_weight_velocity || 20}
                    onChange={(e) => updateConfig({ meme_weight_velocity: parseFloat(e.target.value) })}
                    className="w-full h-1 bg-slate-850 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                </div>

                {/* Link Weight */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Similarity Weight</span>
                    <span className="text-blue-400 font-bold">{config.meme_weight_link}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={config.meme_weight_link || 30}
                    onChange={(e) => updateConfig({ meme_weight_link: parseFloat(e.target.value) })}
                    className="w-full h-1 bg-slate-855 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                </div>

                {/* Surge Weight */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Volume Surge Weight</span>
                    <span className="text-blue-400 font-bold">{config.meme_weight_surge}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={config.meme_weight_surge || 30}
                    onChange={(e) => updateConfig({ meme_weight_surge: parseFloat(e.target.value) })}
                    className="w-full h-1 bg-slate-855 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                </div>

                {/* Cap Weight */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Market Cap Penalty</span>
                    <span className="text-blue-400 font-bold">{config.meme_weight_cap}</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="50"
                    value={config.meme_weight_cap || 10}
                    onChange={(e) => updateConfig({ meme_weight_cap: parseFloat(e.target.value) })}
                    className="w-full h-1 bg-slate-855 rounded-lg appearance-none cursor-pointer accent-blue-500"
                  />
                </div>

                {/* Global Alert Threshold */}
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-indigo-400 font-extrabold">Min Alert Score</span>
                    <span className="text-indigo-400 font-bold">{config.global_alert_threshold}</span>
                  </div>
                  <input
                    type="range"
                    min="30"
                    max="90"
                    value={config.global_alert_threshold || 50}
                    onChange={(e) => updateConfig({ global_alert_threshold: parseFloat(e.target.value) })}
                    className="w-full h-1 bg-slate-855 rounded-lg appearance-none cursor-pointer accent-indigo-500"
                  />
                </div>

              </div>
            </div>

          </div>
        )}



        {/* Source Health and Ingest status banners */}
        <div className="mb-6 grid gap-4 md:grid-cols-4">
          {sourceHealth.map((sh) => (
            <div 
              key={sh.source} 
              className={`p-3 rounded-xl border flex items-center justify-between text-xs font-semibold backdrop-blur-sm ${
                sh.status === 'healthy' 
                  ? 'bg-emerald-500/5 border-emerald-500/10 text-emerald-400' 
                  : 'bg-rose-500/5 border-rose-500/10 text-rose-400'
              }`}
            >
              <div className="flex items-center space-x-2">
                <span className={`w-2 h-2 rounded-full ${sh.status === 'healthy' ? 'bg-emerald-500' : 'bg-rose-500 animate-pulse'}`}></span>
                <span className="uppercase tracking-wider text-[10px]">{sh.source.replace('_', ' ')}</span>
              </div>
              <span className="text-[10px] text-slate-500 font-medium">
                {sh.status === 'healthy' ? 'ACTIVE' : 'ERROR'}
              </span>
            </div>
          ))}
        </div>

        {syncSuccess && (
          <div className="mb-6 flex items-center justify-between p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm font-medium animate-fadeIn">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4" />
              <span>Ingestion pipeline scan completed successfully. Feed refreshed.</span>
            </div>
          </div>
        )}

        {error && (
          <div className="mb-6 flex items-center justify-between p-4 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm font-medium">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4" />
              <span>{error}</span>
            </div>
            <button onClick={fetchAlerts} className="underline hover:text-red-300">
              Retry Connection
            </button>
          </div>
        )}

        {/* System Stats overview */}
        <MetricsGrid activeAlerts={alerts.length} avgScore={avgScore} avgConfidence={avgConfidence} />

        {/* Today's Speculative Macro Trends & Catalysts */}
        <section className="mt-8">
          <div className="flex items-center space-x-2 mb-4">
            <Sparkles className="h-5 w-5 text-indigo-400" />
            <h3 className="text-lg font-bold tracking-wide text-white">Today's Speculative Macro Trends</h3>
          </div>
          
          <div className="grid gap-6 md:grid-cols-2">
            {macroTrends.map((trend) => (
              <div key={trend.id} className="bg-[#151d30]/40 backdrop-blur-md border border-slate-800/80 rounded-2xl p-5 relative overflow-hidden transition-all duration-300 hover:border-slate-700/60 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] px-2.5 py-0.5 rounded-full font-bold bg-slate-800 text-slate-400 border border-slate-700/60 uppercase tracking-wider">
                      {trend.trend_type}
                    </span>
                    <div className="flex items-center space-x-2">
                      <span className="text-[9px] text-slate-500 font-mono">
                        Updated: {new Date(trend.observed_at).toLocaleDateString([], {month: 'short', day: 'numeric'})}
                      </span>
                      <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase border ${
                        trend.impact_direction === 'Bullish' 
                          ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                          : 'bg-rose-500/10 border-rose-500/20 text-rose-400'
                      }`}>
                        {trend.impact_direction}
                      </span>
                    </div>
                  </div>
                  
                  <h4 className="text-base font-extrabold text-white tracking-tight">{trend.title}</h4>
                  <p className="text-slate-400 text-[11px] leading-relaxed mt-2">{trend.description}</p>
                </div>
                
                <div className="mt-4 pt-3 border-t border-slate-800/60 grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-slate-500 block uppercase font-bold text-[8px] tracking-wider">Impacted Sectors</span>
                    <span className="text-slate-300 font-semibold">{trend.suggested_sectors}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 block uppercase font-bold text-[8px] tracking-wider">Scanned Tickers</span>
                    <span className="text-indigo-400 font-extrabold">{trend.associated_tickers}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Backtesting Control Board */}
        <div className="mt-8 p-6 bg-[#151d30]/30 border border-slate-800 rounded-2xl flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-1">
            <h3 className="text-sm font-extrabold uppercase text-slate-300 tracking-wider flex items-center">
              <BarChart2 className="w-4 h-4 mr-2 text-blue-400" />
              Signal Replay & Backtesting Engine
            </h3>
            <p className="text-xs text-slate-400">
              Replay past alerts against market prices to compute scanner precision (2% gain threshold).
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            {backtestStats && (
              <div className="flex items-center space-x-4 bg-slate-950/80 p-3 border border-slate-850 rounded-xl text-xs font-semibold">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Signal Precision</span>
                  <span className="text-white text-sm font-bold">{backtestStats.precision.toFixed(1)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Avg Price Return</span>
                  <span className="text-emerald-400 text-sm font-bold">+{backtestStats.average_return.toFixed(2)}%</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Evaluated Triggers</span>
                  <span className="text-slate-300 text-sm font-bold">{backtestStats.evaluated_alerts}</span>
                </div>
              </div>
            )}

            <button
              onClick={runBacktesting}
              disabled={backtesting || alerts.length === 0}
              className={`flex items-center space-x-1.5 px-4 py-2 rounded-lg text-xs font-bold border transition-all duration-200 ${
                backtesting || alerts.length === 0
                  ? 'bg-slate-800/80 border-slate-700 text-slate-500 cursor-not-allowed'
                  : 'bg-indigo-600/10 border-indigo-500/30 text-indigo-400 hover:bg-indigo-600/20'
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${backtesting ? 'animate-spin' : ''}`} />
              <span>{backtesting ? 'Evaluating...' : 'Run Backtest'}</span>
            </button>
          </div>
        </div>

        {/* Alerts Grid */}
        <main className="mt-10">
          <div className="flex flex-col md:flex-row md:items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold tracking-wide text-white">Market Opportunity Feed</h2>
              <p className="text-xs text-slate-400 mt-1">Real-time alerts and predictive breakout candidates.</p>
            </div>
            <div className="flex mt-4 md:mt-0 space-x-2">
              <button
                onClick={() => setActiveTab('active')}
                className={`px-4 py-1.5 text-sm font-semibold rounded-lg border transition-all ${
                  activeTab === 'active' 
                    ? 'bg-blue-600/20 text-blue-400 border-blue-500/50' 
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
                }`}
              >
                Active Volume Surges
              </button>
              <button
                onClick={() => setActiveTab('predictive')}
                className={`px-4 py-1.5 text-sm font-semibold rounded-lg border transition-all flex items-center space-x-2 ${
                  activeTab === 'predictive' 
                    ? 'bg-purple-600/20 text-purple-400 border-purple-500/50' 
                    : 'bg-slate-800 border-slate-700 text-slate-400 hover:bg-slate-700'
                }`}
              >
                <span>Pre-Breakout Opportunities</span>
                {alerts.filter(a => a.is_predictive === 1).length > 0 && (
                  <span className="px-1.5 py-0.5 text-[10px] bg-purple-500 text-white rounded-full">
                    {alerts.filter(a => a.is_predictive === 1).length}
                  </span>
                )}
              </button>
            </div>
          </div>

          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 bg-slate-900/40 border border-slate-880 rounded-2xl">
              <div className="relative w-10 h-10">
                <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-500/20 rounded-full"></div>
                <div className="absolute top-0 left-0 w-full h-full border-4 border-t-blue-500 rounded-full animate-spin"></div>
              </div>
              <p className="text-sm text-slate-400 mt-4 font-medium">Loading speculative alerts...</p>
            </div>
          ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 bg-slate-900/40 border border-slate-880 rounded-2xl text-center px-4">
              <div className="p-3 bg-slate-800/60 border border-slate-700 rounded-2xl mb-4 text-slate-400">
                <Activity className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-white">No Active Alerts Found</h3>
              <p className="text-sm text-slate-400 mt-2 max-w-md">
                No market anomalies have crossed your active score threshold of {currentThreshold}. Click the <strong>Scan Now</strong> button to force a live scan or query the ingestion API.
              </p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 animate-fadeIn">
              {alerts.filter(a => activeTab === 'predictive' ? a.is_predictive === 1 : a.is_predictive === 0).map((alert) => (
                <AlertCard key={alert.id} alert={alert} />
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Dashboard;
