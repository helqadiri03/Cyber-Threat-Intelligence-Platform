import { formatDistanceToNow } from 'date-fns';
import { AlertTriangle, Radio, Trash2 } from 'lucide-react';
import styles from './LiveAlerts.module.css';
import type { LiveAlert, WsStatus } from '../../hooks/useWebSocket';

function getSeverity(risk: number): 'critical' | 'high' | 'medium' | 'low' {
  if (risk > 90) return 'critical';
  if (risk > 80) return 'high';
  if (risk > 50) return 'medium';
  return 'low';
}

interface Props {
  alerts: LiveAlert[];
  status: WsStatus;
  onClear: () => void;
}

export function LiveAlerts({ alerts, status, onClear }: Props) {
  return (
    <div className={`glass-card ${styles.panel}`}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.titleRow}>
          <Radio size={16} className="text-accent" />
          <h2>Live Alert Stream</h2>
          <span className={`status-dot ${status === 'connected' ? 'live' : status === 'connecting' ? 'degraded' : 'offline'}`} />
          <span className="text-muted" style={{ fontSize: '0.78rem' }}>
            {status === 'connected' ? 'Connected' : status === 'connecting' ? 'Connecting…' : 'Disconnected'}
          </span>
        </div>
        <div className={styles.actions}>
          <span className={styles.count}>{alerts.length} / 100</span>
          <button className="btn btn-ghost btn-sm btn-icon" onClick={onClear} title="Clear alerts">
            <Trash2 size={14} />
          </button>
        </div>
      </div>

      {/* Feed */}
      <div className={styles.feed}>
        {alerts.length === 0 ? (
          <div className={styles.empty}>
            <AlertTriangle size={28} style={{ opacity: 0.3 }} />
            <p>Waiting for alerts…</p>
          </div>
        ) : (
          alerts.map((alert) => {
            const sev = getSeverity(alert.risk_score);
            return (
              <div key={alert.id} className={`${styles.alertRow} ${styles[sev]} animate-slide`}>
                <div className={styles.alertLeft}>
                  <span className={`badge ${sev}`}>{sev}</span>
                  <span className={`mono ${styles.ip}`}>{alert.source_ip}</span>
                </div>
                <div className={styles.alertCenter}>
                  <span className={styles.attackType}>{alert.predicted_attack}</span>
                </div>
                <div className={styles.alertRight}>
                  <span className={styles.risk} style={{ color: sev === 'critical' ? 'var(--sev-critical)' : sev === 'high' ? 'var(--sev-high)' : sev === 'medium' ? 'var(--sev-medium)' : 'var(--sev-low)' }}>
                    {alert.risk_score}
                  </span>
                  <span className={styles.time}>
                    {formatDistanceToNow(new Date(alert.timestamp), { addSuffix: true })}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
