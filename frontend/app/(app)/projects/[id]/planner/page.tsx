'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Cpu, ArrowRight, Loader2, AlertCircle, CheckCircle2, Clock, Package } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';
import { parse } from 'partial-json';

export default function PlannerPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState('');

  const streamContent = useRef('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.plan) {
        setPlan(p.outputs.plan);
        setLoading(false);
      } else {
        setStreaming(true);
        // Auto-generate plan with streaming
        agentsAPI.createPlanStream(
          id,
          (chunk) => {
            streamContent.current += chunk;
            try {
              let contentToParse = streamContent.current.trim();
              if (contentToParse.startsWith("```json")) contentToParse = contentToParse.substring(7);
              else if (contentToParse.startsWith("```")) contentToParse = contentToParse.substring(3);
              
              const partial = parse(contentToParse);
              if (partial && typeof partial === 'object' && Object.keys(partial).length > 0) {
                setPlan(partial);
                setLoading(false);
              }
            } catch (e) {
              // Ignore partial parse errors while streaming
            }
          },
          () => {
             setStreaming(false);
             setLoading(false);
             projectsAPI.get(id).then(updated => {
                if (updated.outputs?.plan) setPlan(updated.outputs.plan);
             });
          },
          (err) => {
            console.error('Plan generation failed', err);
            setLoading(false);
            setStreaming(false);
          }
        );
      }
    });
  }, [id]);

  const handleProceed = () => {
    router.push(`/projects/${id}/code`);
  };

  if (loading || !plan) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Generating execution plan...</p>
      </div>
    );
  }

  const getEstimate = (est: any) => {
    if (!est) return 'Unknown';
    if (typeof est === 'string') return est;
    if (typeof est === 'object') return est.person_months ? `${est.person_months} months` : 'See details below';
    return String(est);
  };

  const safeStr = (val: any): string => {
    if (val === null || val === undefined) return '';
    if (typeof val === 'string') return val;
    if (typeof val === 'object') {
      if (val.name) return String(val.name);
      if (val.task) return String(val.task);
      if (val.description) return String(val.description);
      try { return JSON.stringify(val); } catch { return ''; }
    }
    return String(val);
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Execution Plan</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 5 of 7 — Timeline: {getEstimate(plan.total_estimate)}</p>
        </div>
        <button onClick={handleProceed} disabled={streaming} className="btn-primary">
          {streaming ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          {streaming ? 'Generating Plan...' : 'Generate Code'}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" /> {error}
        </div>
      )}

      <div className="space-y-5">
        {/* Overview */}
        <div className="card">
          <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2">Overview</h2>
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{safeStr(plan.overview)}</p>
        </div>

        {/* Phases */}
        <div className="card">
          <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-4">Project Phases</h2>
          <div className="space-y-4">
            {(plan.phases || []).map((phase: any, i: number) => (
              <div key={i} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0">
                    {safeStr(phase.phase) || (i + 1)}
                  </div>
                  {i < (plan.phases?.length || 0) - 1 && (
                    <div className="w-px flex-1 bg-[var(--border)] mt-2" />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="font-medium text-sm text-[var(--text-primary)]">{safeStr(phase.name)}</span>
                    <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <Clock size={10} /> {safeStr(phase.duration)}
                    </span>
                  </div>
                  <ul className="space-y-1">
                    {(phase.tasks || []).map((task: any, j: number) => (
                      <li key={j} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                        <CheckCircle2 size={11} className="text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                        {safeStr(task)}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Tech Stack */}
        {plan.tech_stack && (
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <Package size={14} className="text-brand-400" /> Tech Stack
            </h2>
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(plan.tech_stack).map(([key, vals]: any) => (
                <div key={key}>
                  <p className="text-xs font-medium text-[var(--text-muted)] capitalize mb-1.5">{key}</p>
                  <div className="flex flex-wrap gap-1">
                    {(Array.isArray(vals) ? vals : [vals]).map((v: any, idx: number) => (
                      <span key={idx} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                        {safeStr(v)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Evaluation */}
        {plan.evaluation_metrics?.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Evaluation Metrics</h2>
            <div className="flex flex-wrap gap-2">
              {plan.evaluation_metrics.map((m: any, idx: number) => (
                <span key={idx} className="badge-blue">{safeStr(m)}</span>
              ))}
            </div>
            {plan.baseline_comparison && (
              <p className="text-xs text-[var(--text-muted)] mt-2">Baseline: {safeStr(plan.baseline_comparison)}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
