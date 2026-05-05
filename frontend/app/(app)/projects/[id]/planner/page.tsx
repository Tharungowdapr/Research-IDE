'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Cpu, ArrowRight, Loader2, AlertCircle, CheckCircle2, Clock, Package, FlaskConical, FolderTree, RefreshCw } from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { useStream } from '@/hooks/useStream';
import { StreamLog } from '@/components/ui/StreamLog';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

function PlannerPageInner() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const triggered = useRef(false);
  const { stream, streaming, log, error: streamError } = useStream();
  const codeStream = useStream();

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.plan) { setPlan(p.outputs.plan); setLoading(false); }
      else { setLoading(false); if (!triggered.current) { triggered.current = true; handleGenerate(); } }
    }).catch(() => { setError('Project not found'); setLoading(false); });
  }, [id]);

  const handleGenerate = () => {
    stream(id, 'plan', {
      onResult: (data) => { if (data?.plan) setPlan(data.plan); },
      onError: (msg) => setError(msg),
    });
  };

  const handleProceed = () => {
    codeStream.stream(id, 'code', {
      onResult: () => {},
      onDone: () => router.push(`/projects/${id}/code`),
      onError: (msg) => setError(msg),
    });
  };

  const displayError = error || streamError || codeStream.error;
  const anyStreaming = streaming || codeStream.streaming;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Execution Plan</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 5 of 7{plan?.total_estimate ? ` — ${plan.total_estimate}` : ''}</p>
        </div>
        <div className="flex gap-2">
          {plan && <button onClick={handleGenerate} disabled={anyStreaming} className="btn-secondary text-sm"><RefreshCw size={14}/> Regenerate</button>}
          {plan && <button onClick={handleProceed} disabled={anyStreaming} className="btn-primary">
            {codeStream.streaming ? <><Loader2 size={14} className="animate-spin"/>Generating code...</> : <>Generate Code <ArrowRight size={14}/></>}
          </button>}
        </div>
      </div>

      {displayError && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2"><AlertCircle size={14}/>{displayError}</div>}
      <StreamLog log={streaming ? log : codeStream.log} streaming={anyStreaming} label={codeStream.streaming ? 'Generating 12-file scaffold...' : 'Building execution plan...'}/>

      {(streaming && !plan) ? (
        <div className="card text-center py-16"><Loader2 size={24} className="animate-spin text-brand-400 mx-auto mb-3"/><p className="text-sm text-[var(--text-secondary)]">Building your execution plan...</p></div>
      ) : plan ? (
        <div className="space-y-5">
          {/* Overview */}
          <div className="card"><h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2">Overview</h2><p className="text-sm text-[var(--text-secondary)] leading-relaxed">{plan.overview}</p></div>

          {/* Phases */}
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-4">Project Phases</h2>
            <div className="space-y-4">
              {(plan.phases||[]).map((phase:any,i:number) => (
                <div key={i} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0">{phase.phase}</div>
                    {i<(plan.phases?.length||0)-1 && <div className="w-px flex-1 bg-[var(--border)] mt-2"/>}
                  </div>
                  <div className="flex-1 pb-4">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="font-medium text-sm text-[var(--text-primary)]">{phase.name}</span>
                      <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]"><Clock size={10}/>{phase.duration}</span>
                    </div>
                    <ul className="space-y-1">{(phase.tasks||[]).map((task:string,j:number)=>(
                      <li key={j} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]"><CheckCircle2 size={11} className="text-[var(--text-muted)] mt-0.5 flex-shrink-0"/>{task}</li>
                    ))}</ul>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Experiment Configs — NEW */}
          {plan.experiment_configs?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2"><FlaskConical size={14} className="text-purple-400"/> Experiment Configurations</h2>
              <div className="space-y-3">
                {plan.experiment_configs.map((cfg:any,i:number) => (
                  <div key={i} className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
                    <p className="text-xs font-medium text-[var(--text-primary)] mb-1">{cfg.name}</p>
                    {cfg.dataset && <p className="text-xs text-[var(--text-muted)] mb-2">Dataset: <span className="text-[var(--text-secondary)]">{cfg.dataset}</span></p>}
                    {cfg.expected_runtime && <p className="text-xs text-[var(--text-muted)] mb-2">Runtime: <span className="text-[var(--text-secondary)]">{cfg.expected_runtime}</span></p>}
                    {cfg.hyperparameters && Object.keys(cfg.hyperparameters).length > 0 && (
                      <div className="grid grid-cols-2 gap-1">
                        {Object.entries(cfg.hyperparameters).map(([k,v]:any) => (
                          <div key={k} className="flex justify-between text-xs">
                            <span className="text-[var(--text-muted)] font-mono">{k}:</span>
                            <span className="text-brand-400 font-mono">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* File Structure — NEW */}
          {plan.file_structure?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2"><FolderTree size={14} className="text-teal-400"/> Planned File Structure</h2>
              <div className="space-y-1">
                {plan.file_structure.map((entry:string, i:number) => {
                  const [fname, ...rest] = entry.split('—');
                  return (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <span className="text-brand-400 font-mono flex-shrink-0">{fname?.trim()}</span>
                      {rest.length > 0 && <span className="text-[var(--text-muted)]">— {rest.join('—').trim()}</span>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tech Stack */}
          {plan.tech_stack && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2"><Package size={14} className="text-brand-400"/> Tech Stack</h2>
              <div className="grid grid-cols-2 gap-4">
                {Object.entries(plan.tech_stack).map(([key,vals]:any) => (
                  <div key={key}>
                    <p className="text-xs font-medium text-[var(--text-muted)] capitalize mb-1.5">{key}</p>
                    <div className="flex flex-wrap gap-1">
                      {(Array.isArray(vals)?vals:[vals]).map((v:string)=>(
                        <span key={v} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">{v}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Baseline comparisons — NEW */}
          {plan.baseline_implementations?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Baseline Methods</h2>
              <div className="space-y-2">
                {plan.baseline_implementations.map((b:any,i:number) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span className="text-emerald-400 font-medium">{b.method_name}</span>
                    <span className="text-[var(--text-muted)]">({b.paper_reference}) — {b.why_baseline}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Eval metrics */}
          {plan.evaluation_metrics?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Evaluation Metrics</h2>
              <div className="flex flex-wrap gap-2">{plan.evaluation_metrics.map((m:string)=><span key={m} className="badge-blue">{m}</span>)}</div>
              {plan.baseline_comparison && <p className="text-xs text-[var(--text-muted)] mt-2">vs. {plan.baseline_comparison}</p>}
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
}

export default function PlannerPage() {
  return <ErrorBoundary><PlannerPageInner /></ErrorBoundary>;
}
