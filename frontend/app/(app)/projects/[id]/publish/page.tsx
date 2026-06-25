'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  CheckCircle2, ArrowRight, Loader2, AlertCircle, FileText,
  BookOpen, Award, Mail, ClipboardList,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function PublishPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [review, setReview] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.review) setReview(p.outputs.review);
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
      const r = await agentsAPI.generateReview(id);
      setReview(r.review);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed.');
    } finally {
      setGenerating(false);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6">
        <h1 className="text-xl font-bold text-[var(--text-primary)]">Review & Publish</h1>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 13 of 13 — Final review and publication prep</p>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2"><AlertCircle size={14} /> {String(error)}</div>}

      {!review && !generating ? (
        <div className="card text-center py-16">
          <CheckCircle2 size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">Ready to review your research.</p>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary mt-4">
            {generating ? <><Loader2 size={14} className="animate-spin" /> Generating...</> : <><ClipboardList size={14} /> Generate Review Checklist</>}
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {generating && !review && (
            <div className="card text-center py-12"><Loader2 className="animate-spin text-brand-400 mx-auto" size={24} /><p className="text-sm mt-3 text-[var(--text-secondary)]">Generating review checklist...</p></div>
          )}

          {/* Formatting Checklist */}
          {review?.formatting_checklist?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <FileText size={14} className="text-brand-400" /> Formatting Checklist
              </h2>
              <div className="space-y-2">
                {review.formatting_checklist.map((item: any, i: number) => (
                  <div key={i} className="flex items-start gap-2 text-xs">
                    <span className={`mt-0.5 ${item.status === 'done' ? 'text-emerald-400' : 'text-[var(--text-muted)]'}`}>
                      {item.status === 'done' ? '✓' : '○'}
                    </span>
                    <div>
                      <span className="text-[var(--text-secondary)]">{item.item}</span>
                      {item.details && <span className="text-[var(--text-muted)] ml-1">— {item.details}</span>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Suggested Venues */}
          {review?.suggested_venues?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Award size={14} className="text-brand-400" /> Suggested Publication Venues
              </h2>
              <div className="space-y-2">
                {review.suggested_venues.map((v: any, i: number) => (
                  <div key={i} className="rounded-lg border border-[var(--border)] p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-medium text-[var(--text-primary)]">{v.name}</span>
                      <span className="badge-purple text-[10px]">{v.type}</span>
                      {v.rank && <span className="badge-blue text-[10px]">Rank: {v.rank}</span>}
                    </div>
                    {v.deadline && <p className="text-xs text-[var(--text-muted)]">Deadline: {v.deadline}</p>}
                    {v.notes && <p className="text-xs text-[var(--text-secondary)] mt-1">{v.notes}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Plagiarism Guidelines */}
          {review?.plagiarism_guidelines?.length > 0 && (
            <div className="card border-yellow-500/20 bg-yellow-500/5">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <AlertCircle size={14} className="text-yellow-400" /> Plagiarism Guidelines
              </h2>
              <div className="space-y-1.5">
                {review.plagiarism_guidelines.map((g: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="text-yellow-400">⚠</span>
                    <span className="text-[var(--text-secondary)]">{g.item}</span>
                    {g.tool && <span className="badge-yellow text-[10px]">{g.tool}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Review Criteria */}
          {review?.review_criteria?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <ClipboardList size={14} className="text-brand-400" /> Self-Review Criteria
              </h2>
              <div className="space-y-2">
                {review.review_criteria.map((c: any, i: number) => (
                  <div key={i} className="flex items-center justify-between rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-2.5 text-xs">
                    <div>
                      <span className="font-medium text-[var(--text-primary)]">{c.criterion}</span>
                      <p className="text-[var(--text-muted)] text-[10px]">{c.what_to_check}</p>
                    </div>
                    {c.self_assessment && (
                      <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                        c.self_assessment === 'good' ? 'bg-emerald-500/10 text-emerald-400' :
                        c.self_assessment === 'fair' ? 'bg-yellow-500/10 text-yellow-400' :
                        'bg-red-500/10 text-red-400'
                      }`}>{c.self_assessment}</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Cover Letter */}
          {review?.cover_letter_template && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Mail size={14} className="text-brand-400" /> Cover Letter Template
              </h2>
              <pre className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed bg-[var(--bg-secondary)] rounded-lg p-3 border border-[var(--border)]">
                {review.cover_letter_template}
              </pre>
            </div>
          )}

          {/* Final Steps */}
          {review?.final_steps?.length > 0 && (
            <div className="card border-emerald-500/20 bg-emerald-500/5">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <BookOpen size={14} className="text-emerald-400" /> Final Steps
              </h2>
              <div className="space-y-2">
                {review.final_steps.map((s: any, i: number) => (
                  <div key={i} className="flex items-center gap-3 text-xs">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-emerald-600/20 text-emerald-400 text-[10px] font-bold">{s.step || i + 1}</span>
                    <span className="text-[var(--text-secondary)]">{s.task}</span>
                    {s.tools?.length > 0 && (
                      <div className="flex gap-1 ml-auto">
                        {(Array.isArray(s.tools) ? s.tools : [s.tools]).map((t: string) => (
                          <span key={t} className="badge-blue text-[10px]">{t}</span>
                        ))}
                      </div>
                    )}
                    {s.time && <span className="text-[var(--text-muted)] ml-auto">{s.time}</span>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex justify-center">
            <button onClick={handleGenerate} disabled={generating} className="btn-ghost text-xs">Regenerate Checklist</button>
          </div>
        </div>
      )}
    </div>
  );
}
