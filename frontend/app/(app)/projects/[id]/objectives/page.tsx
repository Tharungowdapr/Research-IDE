'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Target, ArrowRight, Loader2, AlertCircle, CheckCircle2,
  Clock, Lightbulb, TrendingUp,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function ObjectivesPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [objectives, setObjectives] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.objectives?.objectives) setObjectives(p.outputs.objectives.objectives);
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
      const r = await agentsAPI.generateObjectives(id);
      setObjectives(r.objectives);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to generate objectives.');
    } finally {
      setGenerating(false);
    }
  };

  const handleProceed = () => {
    router.push(`/projects/${id}/planner`);
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Objectives</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 5 of 13 — Define SMART objectives</p>
        </div>
        {objectives.length > 0 && (
          <button onClick={handleProceed} className="btn-primary">
            <ArrowRight size={14} /> Design Methodology
          </button>
        )}
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} /> {String(error)}
        </div>
      )}

      {objectives.length === 0 && !generating ? (
        <div className="card text-center py-16">
          <Target size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No objectives defined yet.</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Generate SMART objectives from your selected idea</p>
          <button onClick={handleGenerate} className="btn-primary mt-4">
            <Target size={14} /> Generate Objectives
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {generating && objectives.length === 0 && (
            <div className="card text-center py-12">
              <Loader2 className="animate-spin text-brand-400 mx-auto mb-3" size={24} />
              <p className="text-sm text-[var(--text-secondary)]">Generating SMART objectives...</p>
            </div>
          )}

          {objectives.map((obj, i) => (
            <div key={i} className="card">
              <div className="flex items-start gap-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0 mt-0.5">
                  {i + 1}
                </div>
                <div className="flex-1">
                  <h3 className="text-sm font-medium text-[var(--text-primary)] mb-2">{obj.objective}</h3>
                  <div className="flex flex-wrap gap-2 text-xs">
                    {obj.type && (
                      <span className="badge-purple capitalize">{obj.type}</span>
                    )}
                    {obj.timeline && (
                      <span className="flex items-center gap-1 text-[var(--text-muted)]">
                        <Clock size={10} /> {obj.timeline}
                      </span>
                    )}
                  </div>
                  {obj.success_criteria && (
                    <div className="mt-2 flex items-start gap-1.5 text-xs text-[var(--text-secondary)]">
                      <CheckCircle2 size={10} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                      <span>{obj.success_criteria}</span>
                    </div>
                  )}
                  {obj.methodology_hint && (
                    <div className="mt-1 flex items-start gap-1.5 text-xs text-[var(--text-muted)]">
                      <Lightbulb size={10} className="text-brand-400 mt-0.5 flex-shrink-0" />
                      <span>{obj.methodology_hint}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {objectives.length > 0 && (
            <div className="flex gap-2 justify-end">
              <button onClick={handleGenerate} disabled={generating} className="btn-ghost text-xs">
                {generating ? <Loader2 size={12} className="animate-spin" /> : null}
                Regenerate
              </button>
              <button onClick={handleProceed} className="btn-primary">
                <ArrowRight size={14} /> Design Methodology
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
