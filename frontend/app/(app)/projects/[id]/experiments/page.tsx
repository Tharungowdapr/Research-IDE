'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  FlaskConical, ArrowRight, Loader2, AlertCircle, Beaker,
  BarChart3, Settings, GitBranch,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function ExperimentsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [experiments, setExperiments] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.experiments) setExperiments(p.outputs.experiments);
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const r = await agentsAPI.generateExperiments(id);
      setExperiments(r.experiments);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleProceed = () => router.push(`/projects/${id}/results`);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Experiments</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 9 of 13 — Design your experiments</p>
        </div>
        {experiments && (
          <button onClick={handleProceed} className="btn-primary"><ArrowRight size={14} /> Results Analysis</button>
        )}
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2"><AlertCircle size={14} /> {String(error)}</div>}

      {!experiments && !generating ? (
        <div className="card text-center py-16">
          <FlaskConical size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No experiments designed yet.</p>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary mt-4">
            {generating ? <><Loader2 size={14} className="animate-spin" /> Generating...</> : <><Beaker size={14} /> Design Experiments</>}
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {generating && !experiments && (
            <div className="card text-center py-12"><Loader2 className="animate-spin text-brand-400 mx-auto" size={24} /><p className="text-sm text-[var(--text-secondary)] mt-3">Designing experiments...</p></div>
          )}

          {experiments?.experiments?.map((exp: any, i: number) => (
            <div key={i} className="card">
              <h3 className="font-semibold text-sm text-[var(--text-primary)] mb-1">{exp.name}</h3>
              <p className="text-xs text-[var(--text-secondary)] mb-3">{exp.objective}</p>

              {exp.model_config && (
                <div className="mb-3">
                  <p className="text-xs font-medium text-[var(--text-muted)] mb-1">Configuration</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(exp.model_config).map(([k, v]: any) => (
                      <span key={k} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--text-secondary)]">
                        {k.replace(/_/g, ' ')}: {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 text-xs">
                {exp.dataset && (
                  <div><span className="text-[var(--text-muted)]">Dataset:</span> <span className="text-[var(--text-secondary)]">{exp.dataset}</span></div>
                )}
                {exp.expected_runtime && (
                  <div><span className="text-[var(--text-muted)]">Runtime:</span> <span className="text-[var(--text-secondary)]">{exp.expected_runtime}</span></div>
                )}
              </div>

              {exp.metrics?.length > 0 && (
                <div className="mt-2 flex flex-wrap gap-1">
                  {exp.metrics.map((m: string) => <span key={m} className="badge-blue text-[10px]">{m}</span>)}
                </div>
              )}

              {exp.ablation?.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs font-medium text-[var(--text-muted)] mb-1 flex items-center gap-1"><GitBranch size={10} /> Ablation Studies</p>
                  <ul className="space-y-0.5">
                    {exp.ablation.map((a: string, j: number) => (
                      <li key={j} className="text-[10px] text-[var(--text-secondary)]">• {a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}

          {experiments?.hyperparameter_tuning && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <Settings size={14} className="text-brand-400" /> Hyperparameter Tuning
              </h2>
              <p className="text-xs text-[var(--text-secondary)] mb-2">Method: {experiments.hyperparameter_tuning.method} · Trials: {experiments.hyperparameter_tuning.trials}</p>
              {experiments.hyperparameter_tuning.params && (
                <div className="flex flex-wrap gap-1.5">
                  {Object.entries(experiments.hyperparameter_tuning.params).map(([k, v]: any) => (
                    <span key={k} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--text-secondary)]">
                      {k}: {Array.isArray(v) ? v.join(', ') : String(v)}
                    </span>
                  ))}
                </div>
              )}
            </div>
          )}

          {experiments?.visualization_plan?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <BarChart3 size={14} className="text-brand-400" /> Visualization Plan
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {experiments.visualization_plan.map((v: string) => <span key={v} className="badge-purple text-[10px]">{v}</span>)}
              </div>
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <button onClick={handleGenerate} disabled={generating} className="btn-ghost text-xs">Regenerate</button>
            <button onClick={handleProceed} className="btn-primary"><ArrowRight size={14} /> Results Analysis</button>
          </div>
        </div>
      )}
    </div>
  );
}
