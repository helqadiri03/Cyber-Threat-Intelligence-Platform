import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend,
} from 'recharts';
import { Activity, Cpu, Shield, TrendingUp, Wifi } from 'lucide-react';
import { format } from 'date-fns';
import { fetchStatistics, type StatisticsResponse } from '../../services/api';
import styles from './StatisticsCharts.module.css';

const CHART_COLORS = [
  '#00d4ff', '#7c4dff', '#ff3b5c', '#ff7043',
  '#ffb300', '#00e676', '#e040fb', '#f06292',
];

const POLL_INTERVAL = 5_000;

function StatCard({ icon, label, value, accent }: {
  icon: React.ReactNode; label: string; value: string | number; accent?: string;
}) {
  return (
    <div className={`glass-card ${styles.statCard}`}>
      <div className={styles.statIcon} style={{ color: accent ?? 'var(--accent)' }}>{icon}</div>
      <div>
        <div className="stat-number" style={{ color: accent ?? 'var(--text-primary)' }}>{value}</div>
        <div className={styles.statLabel}>{label}</div>
      </div>
    </div>
  );
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className={styles.tooltip}>
      <p className={styles.tooltipLabel}>{label}</p>
      {payload.map((p: { name: string; value: number; color: string }, i: number) => (
        <p key={i} style={{ color: p.color }}>{p.name}: <strong>{p.value.toLocaleString()}</strong></p>
      ))}
    </div>
  );
};

export function StatisticsCharts() {
  const [stats, setStats] = useState<StatisticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const data = await fetchStatistics();
        if (active) { setStats(data); setLastUpdated(new Date()); setLoading(false); }
      } catch { /* silent */ }
    }
    poll();
    const id = setInterval(poll, POLL_INTERVAL);
    return () => { active = false; clearInterval(id); };
  }, []);

  const breakdownData = stats?.attack_breakdown?.map((b) => ({
    name: b.attack_type,
    value: b.count,
  })) ?? [];

  const timelineData = stats?.timeline?.map((t) => ({
    time: format(new Date(t.timestamp), 'HH:mm'),
    count: t.count,
  })) ?? [];

  const topIps = stats?.top_ips ?? [];

  return (
    <div className={styles.wrapper}>
      {/* Stat cards */}
      <div className={styles.statRow}>
        <StatCard icon={<Shield size={20} />}   label="Total Predictions"  value={loading ? '—' : stats!.total_predictions.toLocaleString()} />
        <StatCard icon={<Activity size={20} />}  label="Total Alerts"       value={loading ? '—' : stats!.total_alerts.toLocaleString()} accent="var(--sev-critical)" />
        <StatCard icon={<Cpu size={20} />}        label="Top Attack"         value={loading ? '—' : (stats!.top_attack ?? 'N/A')} accent="var(--sev-high)" />
        <StatCard icon={<Wifi size={20} />}       label="Data Source"        value={loading ? '—' : (stats?.source === 'redis_cache' ? 'Cache' : 'Live')} accent="var(--sev-low)" />
      </div>

      <div className={styles.chartsRow}>
        {/* Attack Distribution - Pie */}
        <div className={`glass-card ${styles.chartCard}`}>
          <div className={styles.chartHeader}>
            <TrendingUp size={15} className="text-accent" />
            <h3>Attack Distribution</h3>
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={breakdownData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} paddingAngle={2} label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`} labelLine={false} fontSize={11}>
                  {breakdownData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Attack Volume Bar */}
        <div className={`glass-card ${styles.chartCard}`}>
          <div className={styles.chartHeader}>
            <Activity size={15} className="text-accent" />
            <h3>Attack Volume by Type</h3>
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={breakdownData} margin={{ top: 4, right: 8, bottom: 30, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="name" tick={{ fill: '#8b92a9', fontSize: 10 }} angle={-30} textAnchor="end" interval={0} />
                <YAxis tick={{ fill: '#8b92a9', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
                <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                  {breakdownData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Timeline Line Chart */}
        <div className={`glass-card ${styles.chartCard} ${styles.wide}`}>
          <div className={styles.chartHeader}>
            <Activity size={15} className="text-accent" />
            <h3>Attack Volume — Last Hour</h3>
            {lastUpdated && <span className={styles.updated}>Updated {format(lastUpdated, 'HH:mm:ss')}</span>}
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : timelineData.length === 0 ? (
            <div className={styles.noData}>No timeline data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={timelineData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis dataKey="time" tick={{ fill: '#8b92a9', fontSize: 10 }} />
                <YAxis tick={{ fill: '#8b92a9', fontSize: 10 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ fontSize: '11px' }} />
                <Line type="monotone" dataKey="count" name="Events" stroke="var(--accent)" strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top IPs */}
        <div className={`glass-card ${styles.chartCard}`}>
          <div className={styles.chartHeader}>
            <Shield size={15} className="text-accent" />
            <h3>Top Attacking IPs</h3>
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : topIps.length === 0 ? (
            <div className={styles.noData}>No data yet</div>
          ) : (
            <div className={styles.ipList}>
              {topIps.slice(0, 8).map((ip, i) => {
                const max = topIps[0]?.count ?? 1;
                const pct = Math.round((ip.count / max) * 100);
                return (
                  <div key={ip.source_ip} className={styles.ipRow}>
                    <span className={styles.ipRank}>{i + 1}</span>
                    <div className={styles.ipBar}>
                      <div className={styles.ipBarFill} style={{ width: `${pct}%`, background: CHART_COLORS[i % CHART_COLORS.length] }} />
                    </div>
                    <span className="mono" style={{ fontSize: '0.8rem', minWidth: 100 }}>{ip.source_ip}</span>
                    <span className={styles.ipCount}>{ip.count.toLocaleString()}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
