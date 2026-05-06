'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Search, ArrowRight, Loader2, AlertCircle, TrendingUp, Lightbulb,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

const TYPE_COLORS: Record<string, string> = {
  methodological: 'badge-purple',
  dataset: 'badge-blue',
  evaluation: 'badge-yellow',
  application: 'badge-green',
  theoretical: 'badge-red',
};

const CONFIDENCE_COLORS: Record<string, string> = {
  high: 'text-emerald-400',
  medium: 'text-yellow-400',
  low: 'text-red-400',
};

export default function GapsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [gaps, setGaps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      setGaps(p.outputs?.gaps?.gaps || []);
      setLoading(false);
    });
  }, [id]);

  const handleGenerateIdeas = async () => {
    setGenerating(true);
    setError('');
    try {
      await agentsAPI.generateIdeas(id);
      router.push(`/projects/${id}/ideas`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Idea generation failed.');
      setGenerating(false);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Gap Analysis</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 3 of 7 — {gaps.length} gaps identified</p>
        </div>
        <button onClick={handleGenerateIdeas} disabled={generating || gaps.length === 0} className="btn-primary">
          {generating ? <Loader2 size={14} className="animate-spin" /> : <Lightbulb size={14} />}
          {generating ? 'Generating ideas...' : 'Generate Ideas'}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {gaps.length === 0 ? (
        <div className="card text-center py-16">
          <Search size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No gaps identified yet</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Go back and retrieve papers first</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {gaps.map((gap, i) => (
            <div key={i} className="card hover:border-brand-500/20 transition-all">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1.5">
                    <span className="text-xs font-semibold text-[var(--text-muted)]">#{i + 1}</span>
                    <h3 className="font-semibold text-sm text-[var(--text-primary)]">{gap.title}</h3>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    <span className={TYPE_COLORS[gap.type] || 'badge-blue'}>{gap.type}</span>
                    <span className={`text-xs font-medium ${CONFIDENCE_COLORS[gap.confidence] || 'text-[var(--text-muted)]'}`}>
                      {gap.confidence} confidence
                    </span>
                    <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                      <TrendingUp size={10} className="text-brand-400" />
                      Novelty potential: {gap.novelty_potential}/10
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-sm text-[var(--text-secondary)] leading-relaxed mb-3">{gap.description}</p>

              <div className="grid grid-cols-2 gap-3">
                {gap.supporting_papers?.length > 0 && (
                  <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="text-xs font-medium text-[var(--text-muted)] mb-1.5">Supporting Papers</p>
                    <ul className="space-y-0.5">
                      {gap.supporting_papers.slice(0, 3).map((p: string, j: number) => (
                        <li key={j} className="text-xs text-[var(--text-secondary)] truncate">• {p}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {gap.opportunity && (
                  <div className="rounded-lg bg-brand-600/10 border border-brand-500/20 p-3">
                    <p className="text-xs font-medium text-brand-400 mb-1.5 flex items-center gap-1">
                      <ArrowRight size={10} /> Opportunity
                    </p>
                    <p className="text-xs text-[var(--text-secondary)]">{gap.opportunity}</p>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
