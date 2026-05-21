import { useCallback, useEffect, useRef, useState } from 'react';
import { RefreshCw, Search, X, ChevronLeft, ChevronRight } from 'lucide-react';
import { format } from 'date-fns';
import { fetchPredictions, type Prediction } from '../../services/api';
import styles from './PredictionsTable.module.css';

const ATTACK_TYPES = [
  '', 'DoS/DDoS', 'Botnet', 'WebAttack', 'BruteForce',
  'Recon', 'Infiltration', 'Heartbleed', 'Normal',
];

const CONFIDENCE_COLOR = (c: number) =>
  c >= 0.9 ? 'var(--sev-low)' : c >= 0.7 ? 'var(--sev-medium)' : 'var(--sev-high)';

export function PredictionsTable() {
  const [items, setItems] = useState<Prediction[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [loading, setLoading] = useState(false);
  const [attackTypeFilter, setAttackTypeFilter] = useState('');
  const [ipFilter, setIpFilter] = useState('');
  const [ipInput, setIpInput] = useState('');
  const [autoRefresh, setAutoRefresh] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchPredictions({
        page,
        page_size: pageSize,
        attack_type: attackTypeFilter || undefined,
        source_ip: ipFilter || undefined,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch { /* silent */ }
    finally { setLoading(false); }
  }, [page, pageSize, attackTypeFilter, ipFilter]);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (intervalRef.current) clearInterval(intervalRef.current);
    if (autoRefresh) {
      intervalRef.current = setInterval(load, 10_000);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [autoRefresh, load]);

  const applyIpFilter = () => { setIpFilter(ipInput.trim()); setPage(1); };
  const clearFilters = () => { setAttackTypeFilter(''); setIpFilter(''); setIpInput(''); setPage(1); };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const hasFilters = attackTypeFilter || ipFilter;

  return (
    <div className={`glass-card ${styles.panel}`}>
      {/* Header */}
      <div className={styles.header}>
        <h2>Predictions</h2>
        <span className={styles.total}>{total.toLocaleString()} total</span>
        <div className={styles.spacer} />

        {/* Auto-refresh toggle */}
        <div className={styles.toggleRow}>
          <span className="text-secondary" style={{ fontSize: '0.8rem' }}>Auto-refresh</span>
          <label className="toggle">
            <input type="checkbox" checked={autoRefresh} onChange={(e) => setAutoRefresh(e.target.checked)} />
            <span className="toggle-slider" />
          </label>
        </div>

        <button className="btn btn-ghost btn-sm" onClick={load} disabled={loading}>
          <RefreshCw size={13} className={loading ? styles.spin : ''} />
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className={styles.filters}>
        {/* Attack type */}
        <select
          className="select"
          style={{ maxWidth: 180 }}
          value={attackTypeFilter}
          onChange={(e) => { setAttackTypeFilter(e.target.value); setPage(1); }}
        >
          {ATTACK_TYPES.map((t) => (
            <option key={t} value={t}>{t || 'All Attack Types'}</option>
          ))}
        </select>

        {/* IP search */}
        <div className={styles.ipSearch}>
          <input
            className="input"
            placeholder="Filter by source IP…"
            value={ipInput}
            onChange={(e) => setIpInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && applyIpFilter()}
          />
          <button className="btn btn-primary btn-sm" onClick={applyIpFilter}>
            <Search size={13} />
          </button>
        </div>

        {hasFilters && (
          <button className="btn btn-ghost btn-sm" onClick={clearFilters}>
            <X size={13} /> Clear
          </button>
        )}
      </div>

      {/* Table */}
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>Source IP</th>
              <th>Attack Type</th>
              <th>Confidence</th>
              <th>Model</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {loading && items.length === 0 ? (
              Array.from({ length: 8 }).map((_, i) => (
                <tr key={i}>
                  {Array.from({ length: 5 }).map((__, j) => (
                    <td key={j}><div className={`skeleton ${styles.skeletonCell}`} /></td>
                  ))}
                </tr>
              ))
            ) : items.length === 0 ? (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
                  No predictions found
                </td>
              </tr>
            ) : (
              items.map((p) => (
                <tr key={p.id ?? p.source_ip + p.created_at}>
                  <td><span className="mono">{p.source_ip}</span></td>
                  <td>
                    <span className={styles.attackBadge}>{p.predicted_attack}</span>
                  </td>
                  <td>
                    {p.confidence != null ? (
                      <span style={{ color: CONFIDENCE_COLOR(p.confidence > 1 ? p.confidence / 100 : p.confidence), fontWeight: 600, fontFamily: 'var(--font-mono)' }}>
                        {(p.confidence > 1 ? p.confidence : p.confidence * 100).toFixed(1)}%
                      </span>
                    ) : '—'}
                  </td>
                  <td>
                    <span className="text-muted mono" style={{ fontSize: '0.75rem' }}>
                      {p.model_version ?? '—'}
                    </span>
                  </td>
                  <td>
                    <span className="text-muted" style={{ fontSize: '0.78rem' }}>
                      {format(new Date(p.created_at), 'MMM d, HH:mm:ss')}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className={styles.pagination}>
        <span className="text-muted" style={{ fontSize: '0.78rem' }}>
          Page {page} of {totalPages}
        </span>
        <div className={styles.pageControls}>
          <button className="btn btn-ghost btn-sm btn-icon" disabled={page <= 1} onClick={() => setPage(1)}>
            <ChevronLeft size={14} /><ChevronLeft size={14} style={{ marginLeft: -8 }} />
          </button>
          <button className="btn btn-ghost btn-sm btn-icon" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
            <ChevronLeft size={14} />
          </button>
          {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
            const start = Math.max(1, Math.min(page - 2, totalPages - 4));
            const n = start + i;
            return (
              <button
                key={n}
                className={`btn btn-sm ${n === page ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setPage(n)}
              >
                {n}
              </button>
            );
          })}
          <button className="btn btn-ghost btn-sm btn-icon" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
            <ChevronRight size={14} />
          </button>
          <button className="btn btn-ghost btn-sm btn-icon" disabled={page >= totalPages} onClick={() => setPage(totalPages)}>
            <ChevronRight size={14} /><ChevronRight size={14} style={{ marginLeft: -8 }} />
          </button>
        </div>
      </div>
    </div>
  );
}
