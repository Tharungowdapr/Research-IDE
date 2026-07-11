'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Cpu, MemoryStick, HardDrive, Wifi, Battery,
  Thermometer, Zap, Leaf, Activity, Loader2, BatteryCharging,
} from 'lucide-react';
import { systemAPI } from '@/services/api';

const MAX_HISTORY = 60;

type Snap = {
  ts: number;
  cpu: { percent: number; count_logical: number; count_physical: number; freq_mhz: number | null; freq_max_mhz: number | null };
  ram: { total_gb: number; used_gb: number; available_gb: number; percent: number; swap_used_gb: number; swap_percent: number; swap_total_gb?: number };
  disk: { total_gb: number; used_gb: number; free_gb: number; percent: number };
  network: { bytes_sent_mb: number; bytes_recv_mb: number };
  battery: { percent: number; plugged: boolean; secs_left: number | null } | null;
  temps: Record<string, number>;
  energy: { cpu_draw_w: number; ram_draw_w: number; total_draw_w: number; note: string };
};

type Series = { values: number[]; color: string; label: string; unit: string; max?: number };

function LineChart({ series, height = 120, title, subtitle }: {
  series: Series[]; height?: number; title?: string; subtitle?: string;
}) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{ x: number; y: number; idx: number } | null>(null);
  const W = 600; const H = height; const PL = 38; const PR = 8; const PT = 6; const PB = 24;
  const cW = W - PL - PR; const cH = H - PT - PB;
  const gridLines = [0, 25, 50, 75, 100];
  const len = Math.max(...series.map(s => s.values.length), 2);

  const getMax = (s: Series) => s.max ?? 100;
  const toX = (i: number) => PL + (i / (Math.max(len - 1, 1))) * cW;
  const toY = (v: number, max: number) => PT + cH - (Math.min(v, max) / max) * cH;

  const buildPath = (vals: number[], max: number) => {
    if (vals.length < 2) return '';
    return vals.map((v, i) => `${i === 0 ? 'M' : 'L'}${toX(i).toFixed(1)},${toY(v, max).toFixed(1)}`).join(' ');
  };

  const buildArea = (vals: number[], max: number) => {
    if (vals.length < 2) return '';
    const line = vals.map((v, i) => `${toX(i).toFixed(1)},${toY(v, max).toFixed(1)}`).join(' L');
    const last = vals.length - 1;
    return `M${toX(0).toFixed(1)},${(PT + cH).toFixed(1)} L${line} L${toX(last).toFixed(1)},${(PT + cH).toFixed(1)} Z`;
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect) return;
    const svgX = ((e.clientX - rect.left) / rect.width) * W;
    const relX = svgX - PL;
    const idx = Math.round((relX / cW) * (len - 1));
    if (idx >= 0 && idx < len) setTooltip({ x: svgX, y: e.clientY - rect.top, idx });
  };

  return (
    <div className="relative">
      {(title || subtitle) && (
        <div className="flex items-center gap-3 mb-2">
          {title && <p className="text-xs font-semibold text-[var(--text-secondary)]">{title}</p>}
          {subtitle && <p className="text-[10px] text-[var(--text-muted)]">{subtitle}</p>}
          <div className="flex gap-3 ml-auto">
            {series.map(s => (
              <span key={s.label} className="flex items-center gap-1 text-[10px] text-[var(--text-muted)]">
                <span className="h-2 w-4 rounded-full inline-block" style={{ background: s.color }} />
                {s.label}
              </span>
            ))}
          </div>
        </div>
      )}
      <svg ref={svgRef} viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height }}
        onMouseMove={handleMouseMove} onMouseLeave={() => setTooltip(null)}>
        {gridLines.map(g => {
          const y = PT + cH - (g / 100) * cH;
          return (
            <g key={g}>
              <line x1={PL} y1={y} x2={W - PR} y2={y}
                stroke="var(--border)" strokeWidth="0.5" strokeDasharray={g === 0 ? 'none' : '3,3'} />
              <text x={PL - 4} y={y + 3} textAnchor="end" fontSize="8" fill="var(--text-muted)">{g}</text>
            </g>
          );
        })}
        {[0, 0.25, 0.5, 0.75, 1].map(t => {
          const x = PL + t * cW;
          const sec = Math.round((1 - t) * len * 2);
          return (
            <text key={t} x={x} y={H - 4} textAnchor="middle" fontSize="8" fill="var(--text-muted)">
              {sec === 0 ? 'now' : `-${sec}s`}
            </text>
          );
        })}
        {series.map(s => {
          const max = getMax(s);
          return (
            <g key={s.label}>
              <path d={buildArea(s.values, max)} fill={s.color} fillOpacity="0.08" />
              <path d={buildPath(s.values, max)} fill="none" stroke={s.color}
                strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
              {s.values.length > 0 && (
                <circle
                  cx={toX(s.values.length - 1)}
                  cy={toY(s.values[s.values.length - 1], max)}
                  r="3" fill={s.color} stroke="var(--bg-primary)" strokeWidth="1.5"
                />
              )}
            </g>
          );
        })}
        {tooltip && (
          <line x1={tooltip.x} y1={PT} x2={tooltip.x} y2={PT + cH}
            stroke="var(--text-muted)" strokeWidth="0.8" strokeDasharray="3,2" />
        )}
      </svg>
      {tooltip && (
        <div className="absolute pointer-events-none z-10 rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] px-2.5 py-1.5 text-xs shadow-lg"
          style={{ left: tooltip.x + 10, top: tooltip.y - 10, transform: tooltip.x > W * 0.7 ? 'translateX(-110%)' : undefined }}>
          {series.map(s => {
            const v = s.values[tooltip.idx];
            return v !== undefined ? (
              <div key={s.label} className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
                <span className="text-[var(--text-muted)]">{s.label}</span>
                <span className="font-semibold text-[var(--text-primary)]">{v.toFixed(1)}{s.unit}</span>
              </div>
            ) : null;
          })}
        </div>
      )}
    </div>
  );
}

function Gauge({ value, color, label, sublabel }: { value: number; color: string; label: string; sublabel?: string }) {
  const r = 28, cx = 36, cy = 36, sw = 7;
  const circ = 2 * Math.PI * r; const arc = circ * 0.75;
  const fill = arc - (Math.min(value, 100) / 100) * arc;
  return (
    <div className="flex flex-col items-center gap-1">
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--border)" strokeWidth={sw}
          strokeDasharray={`${arc} ${circ}`} strokeLinecap="round" transform={`rotate(-225 ${cx} ${cy})`} />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth={sw}
          strokeDasharray={`${arc - fill} ${circ}`} strokeLinecap="round"
          transform={`rotate(-225 ${cx} ${cy})`} style={{ transition: 'stroke-dasharray 0.4s' }} />
        <text x={cx} y={cy + 2} textAnchor="middle" dominantBaseline="middle"
          className="fill-[var(--text-primary)]" fontSize="11" fontWeight="600">
          {Math.round(value)}%
        </text>
      </svg>
      <p className="text-[10px] font-medium text-[var(--text-secondary)]">{label}</p>
      {sublabel && <p className="text-[10px] text-[var(--text-muted)]">{sublabel}</p>}
    </div>
  );
}

function Bar({ value, color }: { value: number; color: string }) {
  return (
    <div className="h-1.5 w-full rounded-full bg-[var(--border)] overflow-hidden">
      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${Math.min(value, 100)}%`, background: color }} />
    </div>
  );
}

function pctColor(p: number) { return p < 50 ? '#22c55e' : p < 75 ? '#f59e0b' : '#ef4444'; }
function fmtTime(s: number) { const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60); return h > 0 ? `${h}h ${m}m` : `${m}m`; }
function fmtWh(wh: number) { return wh < 1 ? `${(wh * 1000).toFixed(1)} mWh` : `${wh.toFixed(3)} Wh`; }
function co2Rate(w: number) { const g = w * 0.4; return g < 1000 ? `${g.toFixed(1)} g/hr` : `${(g / 1000).toFixed(2)} kg/hr`; }

export default function SystemMonitorPage() {
  const [history, setHistory] = useState<Snap[]>([]);
  const [latest, setLatest] = useState<Snap | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const cleanupRef = useRef<(() => void) | null>(null);

  const pushSnap = useCallback((snap: Snap) => {
    setLatest(snap);
    setHistory(prev => {
      const next = [...prev, snap];
      return next.length > MAX_HISTORY ? next.slice(-MAX_HISTORY) : next;
    });
  }, []);

  useEffect(() => {
    setConnected(false);
    setError('');
    cleanupRef.current = systemAPI.stream(
      (data) => {
        pushSnap(data);
        setConnected(true);
      },
      (err) => {
        console.error('System stream error:', err);
        setConnected(false);
        setError('Connection lost. Retrying...');
      }
    );
    return () => { cleanupRef.current?.(); };
  }, [pushSnap]);

  if (!latest && !error) {
    return (
      <div className="p-8 max-w-6xl mx-auto flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Connecting to system monitor...</p>
      </div>
    );
  }

  const cpuPct = latest?.cpu?.percent ?? 0;
  const ramPct = latest?.ram?.percent ?? 0;
  const diskPct = latest?.disk?.percent ?? 0;
  const batPct = latest?.battery?.percent ?? 0;
  const batPlugged = latest?.battery?.plugged ?? false;

  const cpuSeries: Series[] = [{ values: history.map(h => h.cpu.percent), color: '#6366f1', label: 'CPU', unit: '%' }];
  const ramSeries: Series[] = [{ values: history.map(h => h.ram.percent), color: '#22c55e', label: 'RAM', unit: '%' }];
  const netSeries: Series[] = [
    { values: history.map(h => h.network.bytes_recv_mb), color: '#3b82f6', label: 'Recv', unit: 'MB', max: undefined },
    { values: history.map(h => h.network.bytes_sent_mb), color: '#f59e0b', label: 'Sent', unit: 'MB', max: undefined },
  ];
  const powerSeries: Series[] = [{ values: history.map(h => h.energy.total_draw_w), color: '#ef4444', label: 'Power', unit: 'W', max: undefined }];

  const net_recv_rates = history.length > 1
    ? history.slice(1).map((h, i) => h.network.bytes_recv_mb - history[i].network.bytes_recv_mb)
    : [];
  const net_send_rates = history.length > 1
    ? history.slice(1).map((h, i) => h.network.bytes_sent_mb - history[i].network.bytes_sent_mb)
    : [];
  const netRateSeries: Series[] = [
    { values: net_recv_rates, color: '#3b82f6', label: 'Recv rate', unit: 'MB/2s', max: undefined },
    { values: net_send_rates, color: '#f59e0b', label: 'Send rate', unit: 'MB/2s', max: undefined },
  ];

  const temps = latest?.temps ?? {};
  const tempEntries = Object.entries(temps);

  const healthScore = (() => {
    let s = 100;
    if (cpuPct > 90) s -= 20; else if (cpuPct > 70) s -= 10;
    if (ramPct > 90) s -= 20; else if (ramPct > 70) s -= 10;
    if (diskPct > 95) s -= 15; else if (diskPct > 85) s -= 5;
    if (latest?.battery && batPct < 10 && !batPlugged) s -= 25;
    if (latest?.energy?.total_draw_w && latest.energy.total_draw_w > 80) s -= 5;
    return Math.max(0, s);
  })();

  const healthColor = healthScore > 70 ? '#22c55e' : healthScore > 40 ? '#f59e0b' : '#ef4444';
  const healthLabel = healthScore > 70 ? 'Healthy' : healthScore > 40 ? 'Moderate' : 'Stressed';

  return (
    <div className="p-8 max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">System Monitor</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Live system metrics · updates every 2s</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className={`h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-[var(--text-muted)]">{connected ? 'Connected' : 'Disconnected'}</span>
          </div>
          <div className="flex items-center gap-2 rounded-lg border border-[var(--border)] px-3 py-1.5">
            <Leaf size={13} style={{ color: healthColor }} />
            <span className="text-xs font-semibold" style={{ color: healthColor }}>{healthScore}/100</span>
            <span className="text-[10px] text-[var(--text-muted)]">{healthLabel}</span>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-lg bg-yellow-500/10 border border-yellow-500/20 px-4 py-2 text-xs text-yellow-400">{error}</div>
      )}

      <div className="grid grid-cols-4 gap-4">
        <div className="card flex flex-col items-center py-4">
          <Gauge value={cpuPct} color={pctColor(cpuPct)} label="CPU"
            sublabel={latest?.cpu?.count_logical ? `${latest.cpu.count_logical} cores` : undefined} />
        </div>
        <div className="card flex flex-col items-center py-4">
          <Gauge value={ramPct} color={pctColor(ramPct)} label="Memory"
            sublabel={latest?.ram ? `${latest.ram.used_gb.toFixed(1)} / ${latest.ram.total_gb.toFixed(1)} GB` : undefined} />
        </div>
        <div className="card flex flex-col items-center py-4">
          <Gauge value={diskPct} color={pctColor(diskPct)} label="Disk"
            sublabel={latest?.disk ? `${latest.disk.free_gb.toFixed(1)} GB free` : undefined} />
        </div>
        <div className="card flex flex-col items-center py-4">
          <Gauge value={latest?.battery ? batPct : 0} color={latest?.battery ? (batPlugged ? '#3b82f6' : pctColor(batPct)) : '#6b7280'}
            label={latest?.battery ? 'Battery' : 'No Battery'}
            sublabel={latest?.battery ? (batPlugged ? 'Plugged in' : fmtTime(latest.battery.secs_left ?? 0)) : 'Desktop'} />
        </div>
      </div>

      <div className="card space-y-4">
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-[10px] text-[var(--text-muted)] mb-1">CPU Usage</p>
            <p className="text-lg font-bold text-[var(--text-primary)]">{cpuPct.toFixed(1)}%</p>
            {latest?.cpu?.freq_mhz && <p className="text-[10px] text-[var(--text-muted)]">{latest.cpu.freq_mhz.toFixed(0)} MHz</p>}
          </div>
          <div>
            <p className="text-[10px] text-[var(--text-muted)] mb-1">Memory Used</p>
            <p className="text-lg font-bold text-[var(--text-primary)]">{(latest?.ram?.used_gb ?? 0).toFixed(1)} GB</p>
            <p className="text-[10px] text-[var(--text-muted)]">{ramPct.toFixed(1)}% of {(latest?.ram?.total_gb ?? 0).toFixed(1)} GB</p>
          </div>
          <div>
            <p className="text-[10px] text-[var(--text-muted)] mb-1">Disk Free</p>
            <p className="text-lg font-bold text-[var(--text-primary)]">{(latest?.disk?.free_gb ?? 0).toFixed(1)} GB</p>
            <p className="text-[10px] text-[var(--text-muted)]">{diskPct.toFixed(1)}% used</p>
          </div>
        </div>
        <Bar value={cpuPct} color={pctColor(cpuPct)} />
        <Bar value={ramPct} color={pctColor(ramPct)} />
        <Bar value={diskPct} color={pctColor(diskPct)} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <LineChart series={cpuSeries} title="CPU Usage" subtitle="%" height={120} />
        </div>
        <div className="card">
          <LineChart series={ramSeries} title="Memory Usage" subtitle="%" height={120} />
        </div>
        <div className="card">
          <LineChart series={netSeries} title="Network I/O" subtitle="cumulative MB" height={120} />
        </div>
        <div className="card">
          <LineChart series={netRateSeries.length > 0 && netRateSeries[0].values.length > 0 ? netRateSeries : [{ values: [0], color: '#3b82f6', label: 'Rate', unit: 'MB/2s' }]}
            title="Network Rate" subtitle="MB per 2s interval" height={120} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <LineChart series={powerSeries} title="Power Draw" subtitle="Watts" height={120} />
        </div>
        {tempEntries.length > 0 ? (
          <div className="card">
            <p className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Temperatures</p>
            <div className="space-y-2">
              {tempEntries.map(([k, v]) => (
                <div key={k} className="flex items-center gap-2">
                  <Thermometer size={12} className="text-[var(--text-muted)]" />
                  <span className="text-[10px] text-[var(--text-muted)] flex-1">{k}</span>
                  <span className="text-xs font-semibold text-[var(--text-primary)]">{v.toFixed(1)}°C</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="card">
            <p className="text-xs font-semibold text-[var(--text-secondary)] mb-2">Energy</p>
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">CPU Draw</span>
                <span className="text-[var(--text-primary)]">{(latest?.energy?.cpu_draw_w ?? 0).toFixed(2)} W</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">RAM Draw</span>
                <span className="text-[var(--text-primary)]">{(latest?.energy?.ram_draw_w ?? 0).toFixed(2)} W</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">Total</span>
                <span className="text-[var(--text-primary)] font-semibold">{(latest?.energy?.total_draw_w ?? 0).toFixed(2)} W</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-[var(--text-muted)]">CO₂ Rate</span>
                <span className="text-[var(--text-primary)]">{co2Rate(latest?.energy?.total_draw_w ?? 0)}</span>
              </div>
              {latest?.energy?.note && <p className="text-[10px] text-[var(--text-muted)] italic mt-1">{latest.energy.note}</p>}
            </div>
          </div>
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="card">
          <p className="text-xs font-semibold text-[var(--text-secondary)] mb-3 flex items-center gap-2">
            <Wifi size={13} /> Network Total
          </p>
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Received</span>
              <span className="text-[var(--text-primary)]">{(latest?.network?.bytes_recv_mb ?? 0).toFixed(2)} MB</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-[var(--text-muted)]">Sent</span>
              <span className="text-[var(--text-primary)]">{(latest?.network?.bytes_sent_mb ?? 0).toFixed(2)} MB</span>
            </div>
          </div>
        </div>
        <div className="card">
          <p className="text-xs font-semibold text-[var(--text-secondary)] mb-3 flex items-center gap-2">
            <Cpu size={13} /> System Info
          </p>
          <div className="space-y-2 text-xs">
            {latest?.cpu?.count_physical !== undefined && (
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Physical Cores</span>
                <span className="text-[var(--text-primary)]">{latest.cpu.count_physical}</span>
              </div>
            )}
            {latest?.cpu?.count_logical !== undefined && (
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Logical Cores</span>
                <span className="text-[var(--text-primary)]">{latest.cpu.count_logical}</span>
              </div>
            )}
            {latest?.cpu?.freq_max_mhz !== undefined && latest.cpu.freq_max_mhz !== null && (
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Max Frequency</span>
                <span className="text-[var(--text-primary)]">{latest.cpu.freq_max_mhz.toFixed(0)} MHz</span>
              </div>
            )}
            {latest?.ram?.swap_total_gb !== undefined && (
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)]">Swap</span>
                <span className="text-[var(--text-primary)]">{latest.ram.swap_used_gb.toFixed(1)} / {(latest.ram as any).swap_total_gb?.toFixed(1) ?? '—'} GB</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
