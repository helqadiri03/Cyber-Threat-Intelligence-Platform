import { useEffect, useState } from 'react';
import { Shield, BarChart2, Bell, Database, Trash2, Play, Square } from 'lucide-react';
import { LiveAlerts } from './components/LiveAlerts/LiveAlerts';
import { StatisticsCharts } from './components/Statistics/StatisticsCharts';
import { PredictionsTable } from './components/Predictions/PredictionsTable';
import { useWebSocket } from './hooks/useWebSocket';
import styles from './App.module.css';
import './index.css';

function useClock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(id);
  }, []);
  return time;
}

type Tab = 'dashboard' | 'alerts' | 'predictions';

export default function App() {
  const { alerts, status, clearAlerts } = useWebSocket();
  const time = useClock();
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');
  const [producerStatus, setProducerStatus] = useState<'running' | 'stopped'>('running');
  const [isResetting, setIsResetting] = useState(false);
  const [isUpdatingProducer, setIsUpdatingProducer] = useState(false);

  const fetchProducerStatus = async () => {
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/producer/status`);
      const data = await res.json();
      if (data && data.status) {
        setProducerStatus(data.status);
      }
    } catch (err) {
      console.error("Failed to fetch producer status", err);
    }
  };

  useEffect(() => {
    fetchProducerStatus();
    const interval = setInterval(fetchProducerStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStopProducer = async () => {
    setIsUpdatingProducer(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/producer/stop`, { method: 'POST' });
      if (res.ok) {
        setProducerStatus('stopped');
      }
    } catch (err) {
      console.error("Error stopping producer", err);
    } finally {
      setIsUpdatingProducer(false);
    }
  };

  const handleStartProducer = async () => {
    setIsUpdatingProducer(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/producer/start`, { method: 'POST' });
      if (res.ok) {
        setProducerStatus('running');
      }
    } catch (err) {
      console.error("Error starting producer", err);
    } finally {
      setIsUpdatingProducer(false);
    }
  };

  const handleResetData = async () => {
    const confirmed = window.confirm(
      "CRITICAL ACTION:\nAre you absolutely sure you want to clear ALL historical predictions in MongoDB, raw telemetry in Cassandra, and real-time alerts in Redis?\n\nThis will completely reset the system to its initial state."
    );
    if (!confirmed) return;

    setIsResetting(true);
    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL}/system/reset`, { method: 'POST' });
      const data = await res.json();
      alert(data.message || "All database records have been successfully reset.");
      window.location.reload();
    } catch (err) {
      alert("System reset failed: " + err);
    } finally {
      setIsResetting(false);
    }
  };

  const timeStr = time.toLocaleTimeString('en-US', { hour12: false });
  const dateStr = time.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });

  return (
    <div className={styles.layout}>
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <header className={styles.header}>
        {/* Brand */}
        <div className={styles.brand}>
          <div className={styles.logo}>
            <Shield size={20} strokeWidth={2.5} />
          </div>
          <div className={styles.brandText}>
            <h1 className={styles.title}>
              CyberThreat<span className="text-accent">Intel</span>
            </h1>
            <p className={styles.subtitle}>AI-Driven Intrusion Detection</p>
          </div>
        </div>

        {/* Nav */}
        <nav className={styles.headerCenter}>
          <button
            className={`${styles.navLink} ${activeTab === 'dashboard' ? styles.active : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <BarChart2 size={13} /> Overview
          </button>
          <button
            className={`${styles.navLink} ${activeTab === 'alerts' ? styles.active : ''}`}
            onClick={() => setActiveTab('alerts')}
          >
            <Bell size={13} /> Live Alerts
          </button>
          <button
            className={`${styles.navLink} ${activeTab === 'predictions' ? styles.active : ''}`}
            onClick={() => setActiveTab('predictions')}
          >
            <Database size={13} /> Predictions
          </button>
        </nav>

        {/* Right side */}
        <div className={styles.headerRight}>
          <div className={styles.timeDisplay}>
            <span className={styles.timeClock}>{timeStr}</span>
            <span className={styles.timeDate}>{dateStr}</span>
          </div>

          <div className={styles.dividerV} />

          <div className={`${styles.statusPill} ${status === 'connected' ? styles.connected : status === 'connecting' ? styles.connecting : ''}`}>
            <span className={`status-dot ${status === 'connected' ? 'live' : status === 'connecting' ? 'degraded' : 'offline'}`} />
            {status === 'connected' ? 'Live Stream' : status === 'connecting' ? 'Connecting…' : 'Offline'}
          </div>

          <div className={styles.alertCount}>
            <span className={styles.alertCountNum}>{alerts.length}</span>
            <span className={styles.alertCountLabel}>alerts</span>
          </div>
        </div>
      </header>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className={styles.main}>
        {(activeTab === 'dashboard') && (
          <>
            {/* System Control Panel */}
            <section className={styles.controlsCard}>
              <div className={styles.controlsInfo}>
                <div className={styles.controlsTitle}>
                  <Shield size={16} className="text-accent" />
                  <span>Ingestion & Database Operations Command Centre</span>
                </div>
                <div className={styles.controlsDesc}>
                  Control real-time Kafka producer telemetry flows and execute system-wide database purges.
                </div>
              </div>

              <div className={styles.controlsActions}>
                {producerStatus === 'stopped' ? (
                  <button
                    className={`${styles.btnControl} ${styles.btnLaunch}`}
                    onClick={handleStartProducer}
                    disabled={isUpdatingProducer}
                  >
                    <Play size={14} fill="currentColor" />
                    <span>{isUpdatingProducer ? 'Starting...' : 'Launch Ingestion'}</span>
                  </button>
                ) : (
                  <button
                    className={`${styles.btnControl} ${styles.btnStop}`}
                    onClick={handleStopProducer}
                    disabled={isUpdatingProducer}
                  >
                    <Square size={14} fill="currentColor" />
                    <span>{isUpdatingProducer ? 'Stopping...' : 'Stop Ingestion'}</span>
                  </button>
                )}

                <button
                  className={`${styles.btnControl} ${styles.btnReset}`}
                  onClick={handleResetData}
                  disabled={isResetting}
                >
                  <Trash2 size={14} />
                  <span>{isResetting ? 'Purging Databases...' : 'Reset All Databases'}</span>
                </button>
              </div>
            </section>

            <section className={styles.statsSection}>
              <StatisticsCharts />
            </section>
            <section className={styles.alertsSection}>
              <LiveAlerts alerts={alerts} status={status} onClear={clearAlerts} />
            </section>
            <section className={styles.tableSection}>
              <PredictionsTable />
            </section>
          </>
        )}

        {activeTab === 'alerts' && (
          <div style={{ flex: 1, minHeight: 600 }}>
            <LiveAlerts alerts={alerts} status={status} onClear={clearAlerts} />
          </div>
        )}

        {activeTab === 'predictions' && (
          <section className={styles.tableSection}>
            <PredictionsTable />
          </section>
        )}
      </main>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className={styles.footer}>
        <div className={styles.footerLeft}>
          <Shield size={12} style={{ color: 'var(--accent)', opacity: 0.6 }} />
          <span>Cyber Threat Intelligence Platform</span>
          <span>·</span>
          <span>AI-Powered Network Security</span>
        </div>
        <div className={styles.footerRight}>
          {['Spark', 'Kafka', 'Cassandra', 'MongoDB', 'Redis'].map(t => (
            <span key={t} className={styles.footerTag}>{t}</span>
          ))}
        </div>
      </footer>
    </div>
  );
}
