'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Cpu, ArrowRight, Loader2, AlertCircle, CheckCircle2, Clock, Package } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function PlannerPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.plan) setPlan(p.outputs.plan);
      else {
        // Auto-generate plan
        agentsAPI.createPlan(id).then((r) => setPlan(r.plan)).catch(console.error);
      }
      setLoading(false);
    });
  }, [id]);

  const handleProceed = async () => {
    setGenerating(true);
    try {
      await agentsAPI.generateCode(id);
      router.push(`/projects/${id}/code`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Code generation failed.');
      setGenerating(false);
    }
  };

  if (loading || !plan) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Generating execution plan...</p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Execution Plan</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 5 of 7 — Timeline: {plan.total_estimate}</p>
        </div>
        <button onClick={handleProceed} disabled={generating} className="btn-primary">
          {generating ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          {generating ? 'Generating code...' : 'Generate Code'}
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
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{plan.overview}</p>
        </div>

        {/* Phases */}
        <div className="card">
          <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-4">Project Phases</h2>
          <div className="space-y-4">
            {(plan.phases || []).map((phase: any, i: number) => (
              <div key={i} className="flex gap-4">
                <div className="flex flex-col items-center">
                  <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0">
                    {phase.phase}
                  </div>
                  {i < (plan.phases?.length || 0) - 1 && (
                    <div className="w-px flex-1 bg-[var(--border)] mt-2" />
                  )}
                </div>
                <div className="flex-1 pb-4">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="font-medium text-sm text-[var(--text-primary)]">{phase.name}</span>
                    <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <Clock size={10} /> {phase.duration}
                    </span>
                  </div>
                  <ul className="space-y-1">
                    {(phase.tasks || []).map((task: string, j: number) => (
                      <li key={j} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                        <CheckCircle2 size={11} className="text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                        {task}
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
                    {(Array.isArray(vals) ? vals : [vals]).map((v: string) => (
                      <span key={v} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                        {v}
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
              {plan.evaluation_metrics.map((m: string) => (
                <span key={m} className="badge-blue">{m}</span>
              ))}
            </div>
            {plan.baseline_comparison && (
              <p className="text-xs text-[var(--text-muted)] mt-2">Baseline: {plan.baseline_comparison}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
