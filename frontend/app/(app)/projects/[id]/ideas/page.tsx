'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Lightbulb, Star, Zap, ArrowRight, Loader2, CheckCircle2,
  Clock, BarChart2, AlertCircle,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

const FEASIBILITY_COLORS: Record<string, string> = {
  high: 'badge-green', medium: 'badge-yellow', low: 'badge-red',
};

const DIFFICULTY_COLORS: Record<string, string> = {
  beginner: 'badge-green', intermediate: 'badge-blue', advanced: 'badge-purple',
};

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span className={`font-medium ${color}`}>{value?.toFixed(1)}/10</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--bg-secondary)] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${color === 'text-brand-400' ? 'bg-brand-500' : 'bg-emerald-500'}`}
          style={{ width: `${((value || 0) / 10) * 100}%` }}
        />
      </div>
    </div>
  );
}

export default function IdeasPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [ideas, setIdeas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState<number | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      setIdeas(p.outputs?.ideas?.ideas || []);
      setLoading(false);
    });
  }, [id]);

  const handleSelectIdea = async (index: number) => {
    setSelecting(index);
    setError('');
    try {
      await agentsAPI.selectIdea(id, index);
      router.push(`/projects/${id}/planner`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to select idea.');
      setSelecting(null);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Ideas</h1>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">
          Step 4 of 7 — {ideas.length} ideas generated, ranked by novelty × feasibility
        </p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {ideas.length === 0 ? (
        <div className="card text-center py-16">
          <Lightbulb size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No ideas yet — run gap analysis first</p>
        </div>
      ) : (
        <div className="space-y-5">
          {ideas.map((idea, i) => (
            <div
              key={i}
              className={`card transition-all hover:border-brand-500/30 ${i === 0 ? 'border-brand-500/40 bg-brand-600/5' : ''}`}
            >
              {/* Rank badge */}
              {i === 0 && (
                <div className="flex items-center gap-1.5 mb-3">
                  <Star size={14} className="text-yellow-400" />
                  <span className="text-xs font-medium text-yellow-400">Top Recommendation</span>
                </div>
              )}

              <div className="grid grid-cols-3 gap-5">
                {/* Left: Idea Details */}
                <div className="col-span-2 space-y-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-[var(--text-muted)] font-mono">#{i + 1}</span>
                      <h3 className="font-semibold text-[var(--text-primary)]">{idea.title}</h3>
                    </div>
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      <span className={FEASIBILITY_COLORS[idea.feasibility] || 'badge-blue'}>
                        {idea.feasibility} feasibility
                      </span>
                      <span className={DIFFICULTY_COLORS[idea.difficulty] || 'badge-blue'}>
                        {idea.difficulty}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                        <Clock size={10} /> {idea.time_estimate}
                      </span>
                    </div>
                    <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{idea.description}</p>
                  </div>

                  <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="text-xs font-medium text-brand-400 mb-1 flex items-center gap-1">
                      <Zap size={10} /> Why Novel
                    </p>
                    <p className="text-xs text-[var(--text-secondary)]">{idea.novelty}</p>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    {idea.suggested_methods?.length > 0 && (
                      <div>
                        <p className="font-medium text-[var(--text-muted)] mb-1">Methods</p>
                        <ul className="space-y-0.5 text-[var(--text-secondary)]">
                          {idea.suggested_methods.slice(0, 3).map((m: string, j: number) => (
                            <li key={j}>• {m}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {idea.suggested_datasets?.length > 0 && (
                      <div>
                        <p className="font-medium text-[var(--text-muted)] mb-1">Datasets</p>
                        <ul className="space-y-0.5 text-[var(--text-secondary)]">
                          {idea.suggested_datasets.slice(0, 3).map((d: string, j: number) => (
                            <li key={j}>• {d}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right: Scores + Action */}
                <div className="space-y-4">
                  <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3 space-y-3">
                    <p className="text-xs font-medium text-[var(--text-secondary)] flex items-center gap-1">
                      <BarChart2 size={11} /> Scores
                    </p>
                    <ScoreBar label="Novelty" value={idea.novelty_score} color="text-brand-400" />
                    <ScoreBar label="Feasibility" value={idea.feasibility_score} color="text-emerald-400" />
                  </div>

                  <button
                    onClick={() => handleSelectIdea(i)}
                    disabled={selecting !== null}
                    className={`w-full ${i === 0 ? 'btn-primary' : 'btn-secondary'} justify-center`}
                  >
                    {selecting === i ? (
                      <><Loader2 size={14} className="animate-spin" /> Selecting...</>
                    ) : (
                      <><CheckCircle2 size={14} /> Select This Idea</>
                    )}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
