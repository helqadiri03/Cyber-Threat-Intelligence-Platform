import './index.css';
import { Shield } from 'lucide-react';
import { LiveAlerts } from './components/LiveAlerts/LiveAlerts';
import { StatisticsCharts } from './components/Statistics/StatisticsCharts';
import { PredictionsTable } from './components/Predictions/PredictionsTable';
import { useWebSocket } from './hooks/useWebSocket';
import styles from './App.module.css';

export default function App() {
  const { alerts, status, clearAlerts } = useWebSocket();

  return (
    <div className={styles.layout}>
      {/* ── Header ─────────────────────────────────────────────────── */}
      <header className={styles.header}>
        <div className={styles.brand}>
          <div className={styles.logo}>
            <Shield size={22} />
          </div>
          <div>
            <h1 className={styles.title}>CyberThreat<span className="text-accent">Intelligence</span></h1>
            <p className={styles.subtitle}>AI-Driven Network Intrusion Detection Platform</p>
          </div>
        </div>
        <div className={styles.headerRight}>
          <div className={styles.statusPill}>
            <span className={`status-dot ${status === 'connected' ? 'live' : status === 'connecting' ? 'degraded' : 'offline'}`} />
            <span>{status === 'connected' ? 'Live' : status === 'connecting' ? 'Connecting' : 'Offline'}</span>
          </div>
          <div className={styles.alertCount}>
            <span className={styles.alertCountNum}>{alerts.length}</span>
            <span className="text-muted">alerts</span>
          </div>
        </div>
      </header>

      {/* ── Main Content ────────────────────────────────────────────── */}
      <main className={styles.main}>
        {/* Top: Statistics */}
        <section className={styles.statsSection}>
          <StatisticsCharts />
        </section>

        {/* Middle: Live Alerts + (future: map) */}
        <section className={styles.alertsSection}>
          <LiveAlerts alerts={alerts} status={status} onClear={clearAlerts} />
        </section>

        {/* Bottom: Predictions Table */}
        <section className={styles.tableSection}>
          <PredictionsTable />
        </section>
      </main>

      <footer className={styles.footer}>
        <span className="text-muted">Cyber Threat Intelligence Platform</span>
        <span className="text-muted">·</span>
        <span className="text-muted">Spark · Kafka · Cassandra · MongoDB · Redis</span>
      </footer>
    </div>
  );
}
