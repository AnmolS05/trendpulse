import React, { useState, useEffect, useCallback } from 'react';
import MetricsGrid from './MetricsGrid';
import AlertCard from './AlertCard';
import { Activity, RefreshCw, AlertCircle, Database, CheckCircle } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const Dashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncSuccess, setSyncSuccess] = useState(false);

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
      // Wait a moment before refreshing the alert feed to let updates settle
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

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  // Calculate dynamic metrics
  const avgScore = alerts.length
    ? Math.round(alerts.reduce((acc, curr) => acc + curr.meme_score, 0) / alerts.length)
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
              <h1 className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-blue-400 via-indigo-200 to-white bg-clip-text text-transparent">
                TrendPulse
              </h1>
              <p className="text-xs text-slate-400 font-medium">Equities phonetic confusion & speculative momentum scanner</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3 mt-4 sm:mt-0">
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
              <span>{isSyncing ? 'Scanning Trends...' : 'Scan Now'}</span>
            </button>

            {/* Refresh Button */}
            <button
              onClick={fetchAlerts}
              className="p-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition-all duration-200"
              title="Refresh alerts"
            >
              <Database className="w-4 h-4" />
            </button>
          </div>
        </header>

        {/* Sync Success banner */}
        {syncSuccess && (
          <div className="mb-6 flex items-center justify-between p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-400 text-sm font-medium animate-fadeIn">
            <div className="flex items-center space-x-2">
              <CheckCircle className="w-4 h-4" />
              <span>Scanning complete. Refreshing dashboard feed...</span>
            </div>
          </div>
        )}

        {/* Network Error banner */}
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
        <MetricsGrid activeAlerts={alerts.length} avgScore={avgScore} />

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
            <div className="flex flex-col items-center justify-center py-20 bg-slate-900/40 border border-slate-800/80 rounded-2xl">
              <div className="relative w-10 h-10">
                <div className="absolute top-0 left-0 w-full h-full border-4 border-blue-500/20 rounded-full"></div>
                <div className="absolute top-0 left-0 w-full h-full border-4 border-t-blue-500 rounded-full animate-spin"></div>
              </div>
              <p className="text-sm text-slate-400 mt-4 font-medium">Loading speculative alerts...</p>
            </div>
          ) : alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 bg-slate-900/40 border border-slate-800/80 rounded-2xl text-center px-4">
              <div className="p-3 bg-slate-800/60 border border-slate-700 rounded-2xl mb-4 text-slate-400">
                <Activity className="w-8 h-8" />
              </div>
              <h3 className="text-lg font-bold text-white">No Active Alerts Found</h3>
              <p className="text-sm text-slate-400 mt-2 max-w-md">
                No market anomalies have crossed the score threshold of 50. Click the <strong>Scan Now</strong> button to force a live scan or query the ingestion API.
              </p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
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
