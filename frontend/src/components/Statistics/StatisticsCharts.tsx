import { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid, Legend, Area, AreaChart,
} from 'recharts';
import { Activity, Cpu, Shield, TrendingUp, Wifi, Globe } from 'lucide-react';
import { format } from 'date-fns';
import { fetchStatistics, type StatisticsResponse } from '../../services/api';
import styles from './StatisticsCharts.module.css';

const CHART_COLORS = [
  '#00d4ff', '#7c4dff', '#ff2d55', '#ff6b35',
  '#ffc107', '#00e676', '#e040fb', '#f06292',
];

const POLL_INTERVAL = 5_000;

function StatCard({ icon, label, value, accent, bg }: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  accent?: string;
  bg?: string;
}) {
  return (
    <div className={`glass-card ${styles.statCard}`}>
      <div className={styles.statIcon} style={{ color: accent ?? 'var(--accent)', background: bg ?? 'var(--accent-dim)' }}>
        {icon}
      </div>
      <div className={styles.statBody}>
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
        <p key={i} style={{ color: p.color, marginTop: 3 }}>
          {p.name}: <strong>{p.value.toLocaleString()}</strong>
        </p>
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
        <StatCard
          icon={<Shield size={20} />}
          label="Total Predictions"
          value={loading ? '—' : stats!.total_predictions.toLocaleString()}
          accent="var(--accent)"
          bg="var(--accent-dim)"
        />
        <StatCard
          icon={<Activity size={20} />}
          label="Total Alerts"
          value={loading ? '—' : stats!.total_alerts.toLocaleString()}
          accent="var(--sev-critical)"
          bg="var(--sev-critical-bg)"
        />
        <StatCard
          icon={<Cpu size={20} />}
          label="Top Attack"
          value={loading ? '—' : (stats!.top_attack ?? 'N/A')}
          accent="var(--sev-high)"
          bg="var(--sev-high-bg)"
        />
        <StatCard
          icon={<Wifi size={20} />}
          label="Data Source"
          value={loading ? '—' : (stats?.source === 'redis_cache' ? 'Cache' : 'Live')}
          accent="var(--sev-low)"
          bg="var(--sev-low-bg)"
        />
      </div>

      <div className={styles.chartsRow}>
        {/* Attack Distribution - Pie */}
        <div className={`glass-card ${styles.chartCard}`}>
          <div className={styles.chartHeader}>
            <TrendingUp size={14} className="text-accent" />
            <h3>Attack Distribution</h3>
            <span className={styles.chartBadge}>Pie</span>
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={breakdownData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%" cy="50%"
                  innerRadius={45}
                  outerRadius={80}
                  paddingAngle={3}
                  label={({ name, percent }) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}
                  labelLine={false}
                  fontSize={10}
                >
                  {breakdownData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} stroke="transparent" />
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
            <Activity size={14} className="text-accent" />
            <h3>Volume by Attack Type</h3>
            <span className={styles.chartBadge}>Bar</span>
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={breakdownData} margin={{ top: 4, right: 8, bottom: 34, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="name" tick={{ fill: '#8892b0', fontSize: 9 }} angle={-30} textAnchor="end" interval={0} />
                <YAxis tick={{ fill: '#8892b0', fontSize: 9 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.03)' }} />
                <Bar dataKey="value" name="Count" radius={[5, 5, 0, 0]}>
                  {breakdownData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Timeline Area Chart */}
        <div className={`glass-card ${styles.chartCard} ${styles.wide}`}>
          <div className={styles.chartHeader}>
            <Activity size={14} className="text-accent" />
            <h3>Attack Volume — Last Hour</h3>
            {lastUpdated && (
              <span className={styles.updated}>Updated {format(lastUpdated, 'HH:mm:ss')}</span>
            )}
            <span className={styles.chartBadge}>Live</span>
          </div>
          {loading ? (
            <div className={`skeleton ${styles.chartSkeleton}`} />
          ) : timelineData.length === 0 ? (
            <div className={styles.noData}>No timeline data yet</div>
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={timelineData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="var(--accent)" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="var(--accent)" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="time" tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: '#8892b0', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area
                  type="monotone"
                  dataKey="count"
                  name="Events"
                  stroke="var(--accent)"
                  strokeWidth={2}
                  fill="url(#areaGrad)"
                  dot={false}
                  activeDot={{ r: 4, fill: 'var(--accent)', stroke: 'rgba(0,212,255,0.3)', strokeWidth: 3 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Top IPs */}
        <div className={`glass-card ${styles.chartCard}`}>
          <div className={styles.chartHeader}>
            <Globe size={14} className="text-accent" />
            <h3>Top Attacking IPs</h3>
            <span className={styles.chartBadge}>Top 8</span>
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
                const color = CHART_COLORS[i % CHART_COLORS.length];
                return (
                  <div key={ip.source_ip} className={styles.ipRow}>
                    <span className={styles.ipRank}>{i + 1}</span>
                    <div className={styles.ipBar}>
                      <div
                        className={styles.ipBarFill}
                        style={{ width: `${pct}%`, background: color }}
                      />
                    </div>
                    <span className={styles.ipAddr}>{ip.source_ip}</span>
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
