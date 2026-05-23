import { formatDistanceToNow } from 'date-fns';
import { AlertTriangle, Radio, Trash2, ShieldAlert } from 'lucide-react';
import styles from './LiveAlerts.module.css';
import type { LiveAlert, WsStatus } from '../../hooks/useWebSocket';

function getSeverity(risk: number): 'critical' | 'high' | 'medium' | 'low' {
  if (risk > 90) return 'critical';
  if (risk > 80) return 'high';
  if (risk > 50) return 'medium';
  return 'low';
}

function getSeverityColor(sev: string) {
  switch (sev) {
    case 'critical': return 'var(--sev-critical)';
    case 'high':     return 'var(--sev-high)';
    case 'medium':   return 'var(--sev-medium)';
    default:         return 'var(--sev-low)';
  }
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
          <Radio size={15} className="text-accent" />
          <h2>Live Alert Stream</h2>
          <span className={`status-dot ${status === 'connected' ? 'live' : status === 'connecting' ? 'degraded' : 'offline'}`} />
          <span className="text-muted" style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
            {status === 'connected' ? 'Connected' : status === 'connecting' ? 'Connecting…' : 'Disconnected'}
          </span>
        </div>
        <div className={styles.actions}>
          <span className={styles.count}>{alerts.length} / 100</span>
          <button className="btn btn-ghost btn-sm btn-icon" onClick={onClear} title="Clear alerts">
            <Trash2 size={13} />
          </button>
        </div>
      </div>

      {/* Feed */}
      <div className={styles.feed}>
        {alerts.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>
              <AlertTriangle size={22} />
            </div>
            <span>Waiting for incoming alerts…</span>
          </div>
        ) : (
          alerts.map((alert) => {
            const sev = getSeverity(alert.risk_score);
            const color = getSeverityColor(sev);
            return (
              <div key={alert.id} className={`${styles.alertRow} ${styles[sev]} animate-slide`}>
                <div className={styles.alertLeft}>
                  <span className={`badge ${sev}`}>{sev}</span>
                  <span className={`mono ${styles.ip}`}>{alert.source_ip}</span>
                </div>
                <div className={styles.alertCenter}>
                  <span className={styles.attackType}>
                    <ShieldAlert size={11} style={{ color, marginRight: 5, verticalAlign: 'middle', opacity: 0.7 }} />
                    {alert.predicted_attack}
                  </span>
                </div>
                <div className={styles.alertRight}>
                  <div className={styles.riskWrapper}>
                    <span className={styles.riskLabel}>Risk</span>
                    <span className={styles.risk} style={{ color }}>{alert.risk_score}</span>
                  </div>
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
