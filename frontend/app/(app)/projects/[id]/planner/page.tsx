'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Cpu, ArrowRight, Loader2, AlertCircle, CheckCircle2, Clock, Package, BookOpen, DollarSign, AlertTriangle, GitBranch, BarChart3 } from 'lucide-react';
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
      }
      setLoading(false);
    });
  }, [id]);

  const handleGenerate = () => {
    setStreaming(true);
    setError('');
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
          }
        } catch (e) {}
      },
      () => {
         setStreaming(false);
         projectsAPI.get(id).then(updated => {
            if (updated.outputs?.plan) setPlan(updated.outputs.plan);
         });
      },
      (err) => {
        console.error('Plan generation failed', err);
        setStreaming(false);
        setError('Failed to generate plan. Please try again.');
      }
    );
  };

  const handleProceed = () => {
    router.push(`/projects/${id}/guide`);
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

  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Loading...</p>
      </div>
    );
  }

  if (!plan && !streaming) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Cpu size={32} className="text-[var(--text-muted)]" />
        <p className="text-sm text-[var(--text-secondary)]">No execution plan yet.</p>
        <button onClick={handleGenerate} className="btn-primary">
          Generate Plan
        </button>
      </div>
    );
  }

  if (streaming && !plan) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Generating execution plan...</p>
      </div>
    );
  }

  if (!plan) return null;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Execution Plan</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 5 of 7 — Timeline: {safeStr(plan.total_estimate)}</p>
        </div>
        <button onClick={handleProceed} disabled={streaming} className="btn-primary">
          {streaming ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          {streaming ? 'Generating Plan...' : 'Research Guide'}
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

        {/* Phases with Timeline */}
        <div className="card">
          <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-4 flex items-center gap-2">
            <BarChart3 size={14} className="text-brand-400" /> Project Phases & Timeline
          </h2>
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

                  {/* Dependencies */}
                  {phase.dependencies?.length > 0 && (
                    <p className="text-[10px] text-[var(--text-muted)] mb-1 flex items-center gap-1">
                      <GitBranch size={9} /> Depends on: {phase.dependencies.join(', ')}
                    </p>
                  )}

                  {/* Tasks */}
                  <ul className="space-y-1 mb-2">
                    {(phase.tasks || []).map((task: any, j: number) => (
                      <li key={j} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                        <CheckCircle2 size={11} className="text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                        {safeStr(task)}
                      </li>
                    ))}
                  </ul>

                  {/* Resources */}
                  {phase.resources_required && (
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      {Object.entries(phase.resources_required).map(([key, val]: any) => (
                        <span key={key} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-1.5 py-0.5 text-[10px] text-[var(--text-muted)]">
                          {key.replace(/_/g, ' ')}: {safeStr(val)}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Milestones */}
                  {phase.milestones?.length > 0 && (
                    <div className="rounded-lg bg-emerald-500/5 border border-emerald-500/10 p-2 mt-1">
                      {phase.milestones.map((ms: any, j: number) => (
                        <div key={j} className="text-[10px] text-[var(--text-secondary)]">
                          <span className="text-emerald-400 font-medium">◆ {safeStr(ms.name)}</span>
                          {ms.criteria && <span className="text-[var(--text-muted)]"> — {safeStr(ms.criteria)}</span>}
                          {ms.deadline && <span className="text-[var(--text-muted)]"> ({safeStr(ms.deadline)})</span>}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Deliverables */}
                  {phase.deliverables?.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-1.5">
                      {phase.deliverables.map((d: string, j: number) => (
                        <span key={j} className="text-[10px] text-brand-400">[{safeStr(d)}]</span>
                      ))}
                    </div>
                  )}
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
                  <p className="text-xs font-medium text-[var(--text-muted)] capitalize mb-1.5">{key.replace(/_/g, ' ')}</p>
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

        {/* Risks with Mitigation */}
        {plan.risks?.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <AlertTriangle size={14} className="text-yellow-400" /> Risks & Mitigations
            </h2>
            <div className="space-y-2">
              {(plan.risks || []).map((r: any, i: number) => (
                <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium text-[var(--text-primary)]">{safeStr(r.risk || r)}</span>
                    {r.severity && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                        r.severity === 'high' ? 'bg-red-500/10 text-red-400' :
                        r.severity === 'medium' ? 'bg-yellow-500/10 text-yellow-400' :
                        'bg-blue-500/10 text-blue-400'
                      }`}>{r.severity}</span>
                    )}
                  </div>
                  {r.mitigation && <p className="text-xs text-[var(--text-secondary)]">✓ Mitigation: {safeStr(r.mitigation)}</p>}
                  {r.contingency && <p className="text-xs text-[var(--text-muted)]">↻ Contingency: {safeStr(r.contingency)}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Budget */}
        {plan.budget_estimation && (
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <DollarSign size={14} className="text-emerald-400" /> Budget Estimation
            </h2>
            <div className="grid grid-cols-2 gap-3">
              {Object.entries(plan.budget_estimation).map(([key, val]: any) => (
                <div key={key} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-2">
                  <p className="text-[10px] text-[var(--text-muted)] capitalize mb-0.5">{key.replace(/_/g, ' ')}</p>
                  <p className="text-xs text-[var(--text-primary)] font-medium">{safeStr(val)}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Literature Review Plan */}
        {plan.literature_review_plan?.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
              <BookOpen size={14} className="text-purple-400" /> Literature Review Plan
            </h2>
            <div className="space-y-2">
              {(plan.literature_review_plan || []).map((item: any, i: number) => (
                <div key={i} className="flex items-start gap-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                  <div className="flex h-5 w-5 items-center justify-center rounded-full bg-purple-600/20 text-purple-400 text-[10px] font-bold flex-shrink-0">
                    {item.priority || i + 1}
                  </div>
                  <div>
                    <p className="text-xs font-medium text-[var(--text-primary)]">{safeStr(item.topic)}</p>
                    {item.key_papers?.length > 0 && (
                      <ul className="mt-1 space-y-0.5">
                        {item.key_papers.map((p: string, j: number) => (
                          <li key={j} className="text-[10px] text-[var(--text-secondary)]">• {safeStr(p)}</li>
                        ))}
                      </ul>
                    )}
                    {item.why_first && <p className="text-[10px] text-[var(--text-muted)] mt-1">→ {safeStr(item.why_first)}</p>}
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

        {/* Datasets */}
        {plan.datasets?.length > 0 && (
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Datasets</h2>
            <div className="space-y-2">
              {plan.datasets.map((ds: any, i: number) => (
                <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-2 text-xs">
                  <p className="font-medium text-[var(--text-primary)]">{safeStr(ds.name)}</p>
                  <p className="text-[var(--text-muted)]">{safeStr(ds.why)}</p>
                  {ds.size && <p className="text-[var(--text-muted)]">Size: {safeStr(ds.size)}{ds.licensing ? ` • License: ${ds.licensing}` : ''}</p>}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
