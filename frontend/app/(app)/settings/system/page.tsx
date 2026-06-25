'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Cpu, MemoryStick, HardDrive, Wifi, Battery,
  Thermometer, Zap, Leaf, Activity, Loader2, BatteryCharging,
} from 'lucide-react';
import { systemAPI } from '@/services/api';

const MAX_HISTORY = 60; // 60 × 2s = 2 min window

type Snap = {
  ts: number;
  cpu: { percent: number; count_logical: number; count_physical: number; freq_mhz: number | null; freq_max_mhz: number | null };
  ram: { total_gb: number; used_gb: number; available_gb: number; percent: number; swap_used_gb: number; swap_percent: number };
  disk: { total_gb: number; used_gb: number; free_gb: number; percent: number };
  network: { bytes_sent_mb: number; bytes_recv_mb: number };
  battery: { percent: number; plugged: boolean; secs_left: number | null } | null;
  temps: Record<string, number>;
  energy: { cpu_draw_w: number; ram_draw_w: number; total_draw_w: number; note: string };
};

type Series = { values: number[]; color: string; label: string; unit: string; max?: number };

// ── LineChart component ───────────────────────────────────────────────────────
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
        {/* Grid lines */}
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
        {/* Time axis labels */}
        {[0, 0.25, 0.5, 0.75, 1].map(t => {
          const x = PL + t * cW;
          const sec = Math.round((1 - t) * len * 2);
          return (
            <text key={t} x={x} y={H - 4} textAnchor="middle" fontSize="8" fill="var(--text-muted)">
              {sec === 0 ? 'now' : `-${sec}s`}
            </text>
          );
        })}
        {/* Series */}
        {series.map(s => {
          const max = getMax(s);
          return (
            <g key={s.label}>
              <path d={buildArea(s.values, max)} fill={s.color} fillOpacity="0.08" />
              <path d={buildPath(s.values, max)} fill="none" stroke={s.color}
                strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
              {/* Current value dot */}
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
        {/* Tooltip crosshair */}
        {tooltip && (
          <line x1={tooltip.x} y1={PT} x2={tooltip.x} y2={PT + cH}
            stroke="var(--text-muted)" strokeWidth="0.8" strokeDasharray="3,2" />
        )}
      </svg>
      {/* Tooltip box */}
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

// ── Radial gauge ─────────────────────────────────────────────────────────────
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
  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-xl font-bold text-[var(--text-primary)] mb-4">System Monitor</h1>
      <p className="text-sm text-[var(--text-muted)]">System monitoring page - implementation in progress</p>
    </div>
  );
}
