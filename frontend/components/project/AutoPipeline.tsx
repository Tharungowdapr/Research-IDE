'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Loader2, CheckCircle2, AlertCircle, Clock, ArrowRight } from 'lucide-react';
import { pipelineAPI } from '@/services/api';

const STAGE_LABELS: Record<string, string> = {
  analysis: 'NLP Analysis',
  papers: 'Literature Review',
  gaps: 'Research Gap',
  ideas: 'Research Ideas',
  objectives: 'SMART Objectives',
  planner: 'Methodology',
  data: 'Data Pipeline',
  code: 'Implementation',
  experiments: 'Experiments',
  results: 'Results Analysis',
  guide: 'Research Guide',
  report: 'Paper Writing',
  publish: 'Review & Publish',
};

const STAGE_ORDER = ['analysis', 'papers', 'gaps', 'ideas', 'objectives', 'planner', 'data', 'code', 'experiments', 'results', 'guide', 'report', 'publish'];

export default function AutoPipeline({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [running, setRunning] = useState(false);
  const [stages, setStages] = useState<Record<string, 'pending' | 'running' | 'done' | 'error'>>({});
  const [messages, setMessages] = useState<Record<string, string>>({});
  const [error, setError] = useState('');

  const handleRunFull = () => {
    setRunning(true);
    setError('');

    const initial: Record<string, 'pending' | 'running' | 'done' | 'error'> = {};
    STAGE_ORDER.forEach((s) => (initial[s] = 'pending'));
    initial.analysis = 'running';
    setStages(initial);

    pipelineAPI.runFullPipeline(
      projectId,
      (data) => {
        const stage = data.stage;
        if (data.status === 'running') {
          setStages((prev) => ({ ...prev, [stage]: 'running' }));
        } else if (data.status === 'done') {
          setStages((prev) => ({ ...prev, [stage]: 'done' }));
          // Start next stage
          const idx = STAGE_ORDER.indexOf(stage);
          if (idx >= 0 && idx < STAGE_ORDER.length - 1) {
            const next = STAGE_ORDER[idx + 1];
            setStages((prev) => ({ ...prev, [next]: 'running' }));
          }
        } else if (data.status === 'error') {
          setStages((prev) => ({ ...prev, [stage]: 'error' }));
          setError(data.message || 'An error occurred');
        }
        if (data.message) {
          setMessages((prev) => ({ ...prev, [stage]: data.message }));
        }
      },
      () => {
        setRunning(false);
      },
      (err) => {
        setRunning(false);
        setError(err.message || 'Pipeline failed');
      }
    );
  };

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-card)] p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-semibold text-sm text-[var(--text-primary)]">Auto Pipeline</h3>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Run all 13 steps automatically</p>
        </div>
        <button
          onClick={handleRunFull}
          disabled={running}
          className="btn-primary"
        >
          {running ? <Loader2 size={14} className="animate-spin" /> : <Play size={14} />}
          {running ? 'Running...' : 'Run Full Analysis'}
        </button>
      </div>

      {error && (
        <div className="mb-3 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400 flex items-center gap-1.5">
          <AlertCircle size={12} /> {error}
        </div>
      )}

      <div className="space-y-1.5">
        {STAGE_ORDER.map((stage) => {
          const status = stages[stage] || 'pending';
          const label = STAGE_LABELS[stage] || stage;
          const message = messages[stage];

          return (
            <div
              key={stage}
              className={`flex items-center gap-3 rounded-lg px-3 py-2 text-xs transition-all ${
                status === 'running' ? 'bg-brand-600/10 border border-brand-500/20' :
                status === 'done' ? 'bg-emerald-500/5 border border-emerald-500/10' :
                status === 'error' ? 'bg-red-500/5 border border-red-500/10' :
                'bg-[var(--bg-secondary)] border border-[var(--border)] opacity-50'
              }`}
            >
              <div className="flex-shrink-0">
                {status === 'running' && <Loader2 size={12} className="animate-spin text-brand-400" />}
                {status === 'done' && <CheckCircle2 size={12} className="text-emerald-400" />}
                {status === 'error' && <AlertCircle size={12} className="text-red-400" />}
                {status === 'pending' && <Clock size={12} className="text-[var(--text-muted)]" />}
              </div>
              <span className={`font-medium ${
                status === 'running' ? 'text-brand-400' :
                status === 'done' ? 'text-emerald-400' :
                status === 'error' ? 'text-red-400' :
                'text-[var(--text-muted)]'
              }`}>{label}</span>
              {message && (
                <span className="text-[var(--text-muted)] ml-auto truncate max-w-[300px]">{message}</span>
              )}
            </div>
          );
        })}
      </div>

      {!running && STAGE_ORDER.every((s) => stages[s] === 'done') && (
        <div className="mt-4 flex justify-end">
          <button onClick={() => router.push(`/projects/${projectId}/publish`)} className="btn-primary text-xs">
            View Final Step <ArrowRight size={12} />
          </button>
        </div>
      )}
    </div>
  );
}
