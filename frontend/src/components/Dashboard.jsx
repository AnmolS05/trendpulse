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
  
  // New Phase 2 & 3 State
  const [config, setConfig] = useState({ strict_real_data: true, allow_simulated_data: false });
  const [sourceHealth, setSourceHealth] = useState([]);
  const [watchlist, setWatchlist] = useState([]);
  const [backtestStats, setBacktestStats] = useState(null);
  const [backtesting, setBacktesting] = useState(false);
  
  // Watchlist Input
  const [newSymbol, setNewSymbol] = useState('');
  const [newThreshold, setNewThreshold] = useState(50);
  
  // UI Panels toggles
  const [showConfig, setShowConfig] = useState(false);
  const [showWatchlistPanel, setShowWatchlistPanel] = useState(false);

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

  const fetchConfig = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (err) {
      console.error("Error fetching config:", err);
    }
  }, []);

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

  const fetchWatchlist = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/watchlist`);
      if (response.ok) {
        const data = await response.json();
        setWatchlist(data);
      }
    } catch (err) {
      console.error("Error fetching watchlist:", err);
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
        setSyncSuccess(false);
      }, 1500);
    } catch (err) {
      console.error("Error running manual sync:", err);
      setError("Failed to trigger manual trend ingestion.");
    } finally {
      setIsSyncing(false);
    }
  };

  const updateConfig = async (strict, simulated) => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strict_real_data: strict, allow_simulated_data: simulated })
      });
      if (response.ok) {
        setConfig({ strict_real_data: strict, allow_simulated_data: simulated });
        fetchAlerts();
      }
    } catch (err) {
      console.error("Failed to update admin config:", err);
    }
  };

  const handleAddWatchlist = async (e) => {
    e.preventDefault();
    if (!newSymbol) return;
    try {
      const response = await fetch(`${API_BASE}/api/watchlist`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol_or_topic: newSymbol.trim().toUpperCase(), alert_threshold: parseFloat(newThreshold) })
      });
      if (response.ok) {
        setNewSymbol('');
        fetchWatchlist();
      }
    } catch (err) {
      console.error("Error adding to watchlist:", err);
    }
  };

  const handleRemoveWatchlist = async (symbol) => {
    try {
      const response = await fetch(`${API_BASE}/api/watchlist/${symbol}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchWatchlist();
      }
    } catch (err) {
      console.error("Error removing from watchlist:", err);
    }
  };

  const runBacktesting = async () => {
    setBacktesting(true);
    try {
      const response = await fetch(`${API_BASE}/api/backtest`, {
        method: 'POST'
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
    fetchWatchlist();
  }, [fetchAlerts, fetchConfig, fetchSourceHealth, fetchWatchlist]);

  // Dynamic statistics
  const avgScore = alerts.length
    ? Math.round(alerts.reduce((acc, curr) => acc + curr.meme_score, 0) / alerts.length)
    : 0;
  
  const avgConfidence = alerts.length
    ? Math.round(alerts.reduce((acc, curr) => acc + curr.confidence_score, 0) / alerts.length)
    : 0;

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
                {config.strict_real_data ? (
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-extrabold uppercase">
                    Strict Mode
                  </span>
                ) : (
                  <span className="text-[10px] px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/30 text-amber-400 font-extrabold uppercase animate-pulse">
                    Demo/Simulated
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-400 font-medium">Equities phonetic confusion & evidence-backed momentum scanner</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
            {/* Watchlist Toggle */}
            <button
              onClick={() => setShowWatchlistPanel(!showWatchlistPanel)}
              className={`flex items-center space-x-1 px-3 py-2 text-sm font-semibold rounded-lg border transition-all duration-200 ${
                showWatchlistPanel 
                  ? 'bg-indigo-600 text-white border-indigo-500' 
                  : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <Eye className="w-4 h-4" />
              <span>Watchlists ({watchlist.length})</span>
            </button>

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
              onClick={fetchAlerts}
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
            <div className="grid gap-6 md:grid-cols-2">
              <div className="flex items-start space-x-3">
                <input
                  id="strict-mode"
                  type="checkbox"
                  checked={config.strict_real_data}
                  onChange={(e) => updateConfig(e.target.checked, config.allow_simulated_data)}
                  className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <label htmlFor="strict-mode" className="text-sm font-bold text-white block">Strict Real-Data Mode</label>
                  <span className="text-xs text-slate-400">
                    When active, alerts are blocked unless real social mentions and live market volumes are verified. No fallback simulation is permitted.
                  </span>
                </div>
              </div>
              
              <div className="flex items-start space-x-3">
                <input
                  id="demo-mode"
                  type="checkbox"
                  checked={config.allow_simulated_data}
                  onChange={(e) => updateConfig(config.strict_real_data, e.target.checked)}
                  className="mt-1 h-4 w-4 rounded border-slate-700 bg-slate-800 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <label htmlFor="demo-mode" className="text-sm font-bold text-white block">Allow Simulated Fallbacks</label>
                  <span className="text-xs text-slate-400">
                    Enables mock values to populate empty APIs so the dashboard can demonstrate phonetic confusion mechanics without active keys.
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Watchlist Manager Panel */}
        {showWatchlistPanel && (
          <div className="mb-8 p-6 bg-[#111827]/80 backdrop-blur-md border border-indigo-500/20 rounded-2xl animate-slideDown">
            <h3 className="text-sm font-extrabold uppercase text-indigo-400 tracking-wider mb-4 flex items-center">
              <Sparkles className="w-4 h-4 mr-2" />
              Watchlist and Notification Manager
            </h3>
            
            <div className="grid gap-6 md:grid-cols-3">
              <form onSubmit={handleAddWatchlist} className="space-y-4 bg-slate-950/40 p-4 border border-slate-850 rounded-xl">
                <h4 className="text-xs font-bold uppercase text-slate-400">Add Watchlist Element</h4>
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-500">Symbol or Tag</label>
                  <input
                    type="text"
                    value={newSymbol}
                    onChange={(e) => setNewSymbol(e.target.value)}
                    placeholder="e.g. TSLA or AAPL"
                    className="w-full mt-1 px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg text-sm text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div>
                  <label className="text-[10px] uppercase font-bold text-slate-500">Alert Min Threshold: {newThreshold}</label>
                  <input
                    type="range"
                    min="30"
                    max="90"
                    value={newThreshold}
                    onChange={(e) => setNewThreshold(e.target.value)}
                    className="w-full h-1 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-indigo-500 mt-2"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full flex items-center justify-center space-x-1 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-xs font-bold transition-all duration-200"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Ticker</span>
                </button>
              </form>

              <div className="md:col-span-2 bg-slate-950/40 p-4 border border-slate-850 rounded-xl max-h-[200px] overflow-y-auto">
                <h4 className="text-xs font-bold uppercase text-slate-400 mb-3">Monitored Watchlist Symbols</h4>
                {watchlist.length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No watchlists configured. Add a ticker to begin monitoring.</p>
                ) : (
                  <div className="grid gap-2 sm:grid-cols-2">
                    {watchlist.map((item) => (
                      <div key={item.id} className="flex items-center justify-between p-2.5 bg-slate-900/80 border border-slate-800 rounded-lg text-xs">
                        <div>
                          <p className="font-extrabold text-white">{item.symbol_or_topic}</p>
                          <p className="text-[10px] text-slate-500">Threshold: {item.alert_threshold} meme score</p>
                        </div>
                        <button
                          onClick={() => handleRemoveWatchlist(item.symbol_or_topic)}
                          className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
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
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold tracking-wide text-white">Active Market Alert Feed</h2>
              <p className="text-xs text-slate-400 mt-1">Real-time alerts generated when social chatter aligns with equities volume surges.</p>
            </div>
            <span className="text-xs px-2.5 py-1 bg-slate-800/80 border border-slate-700 rounded-full font-semibold text-slate-400">
              WAL-Mode SQLite Sync
            </span>
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
                No market anomalies have crossed the score threshold of 50. Click the <strong>Scan Now</strong> button to force a live scan or query the ingestion API.
              </p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 animate-fadeIn">
              {alerts.map((alert) => (
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
