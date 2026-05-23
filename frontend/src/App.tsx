import { useEffect, useState } from 'react';
import { Shield, BarChart2, Bell, Database } from 'lucide-react';
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
