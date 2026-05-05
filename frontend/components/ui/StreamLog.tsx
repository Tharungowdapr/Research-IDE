'use client';

import { Loader2 } from 'lucide-react';

interface Props {
  log: string[];
  streaming: boolean;
  label?: string;
}

export function StreamLog({ log, streaming, label = 'Processing...' }: Props) {
  if (!streaming && log.length === 0) return null;
  return (
    <div className="mb-5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-4 font-mono text-xs space-y-1 max-h-44 overflow-auto">
      {log.map((msg, i) => (
        <div key={i} className="flex items-center gap-2 text-[var(--text-secondary)]">
          <span className="text-brand-400 flex-shrink-0">▸</span>
          <span>{msg}</span>
        </div>
      ))}
      {streaming && (
        <div className="flex items-center gap-2 text-brand-400">
          <Loader2 size={10} className="animate-spin flex-shrink-0" />
          <span>{label}</span>
        </div>
      )}
    </div>
  );
}
