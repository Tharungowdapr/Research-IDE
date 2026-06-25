'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  BookOpen, Download, Loader2, ArrowRight, FileText,
  CheckCircle2, Clock, AlertCircle, Presentation,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function GuidePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [guide, setGuide] = useState<any>(null);
  const [slides, setSlides] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [slideGenerating, setSlideGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.guide) setGuide(p.outputs.guide);
        if (p.outputs?.presentation) setSlides(p.outputs.presentation?.slides || null);
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
      const result = await agentsAPI.generateGuide(id);
      setGuide(result.guide);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Generation failed.');
    }
    setGenerating(false);
  };

  const handleGenerateSlides = async () => {
    setSlideGenerating(true);
    try {
      const result = await agentsAPI.generatePresentation(id);
      setSlides(result.slides);
    } catch (e) {
      console.error(e);
    }
    setSlideGenerating(false);
  };

  const handleProceed = () => {
    router.push(`/projects/${id}/report`);
  };

  const safeStr = (val: any): string => {
    if (val === null || val === undefined) return '';
    if (typeof val === 'string') return val;
    if (typeof val === 'object') {
      try { return JSON.stringify(val); } catch { return ''; }
    }
    return String(val);
  };

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-[400px]">
        <Loader2 className="animate-spin text-brand-400" size={24} />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Guide</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 11 of 13 — Methodology, tools, and presentation</p>
        </div>
        <div className="flex gap-2">
          {!guide && (
            <button onClick={handleGenerate} disabled={generating} className="btn-primary">
              {generating ? <Loader2 size={14} className="animate-spin" /> : <BookOpen size={14} />}
              {generating ? 'Generating...' : 'Generate Guide'}
            </button>
          )}
          <button
            onClick={handleProceed}
            disabled={generating}
            className="btn-primary"
          >
            <ArrowRight size={14} /> Write Paper
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" /> {String(error)}
        </div>
      )}

      {!guide && !generating && (
        <div className="card text-center py-12">
          <BookOpen size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No research guide generated yet.</p>
          <p className="text-xs text-[var(--text-muted)] mt-1">Generate a guide to get methodology details, tool recommendations, and more.</p>
        </div>
      )}

      {generating && !guide && (
        <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
          <Loader2 className="animate-spin text-brand-400" size={24} />
          <p className="text-sm text-[var(--text-secondary)]">Generating research guide...</p>
        </div>
      )}

      {guide && (
        <div className="space-y-5">
          {/* Executive Summary */}
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2">Executive Summary</h2>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {safeStr(guide.project_report?.executive_summary)}
            </p>
          </div>

          {/* Methodology Walkthrough */}
          <div className="card">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-4">Methodology Walkthrough</h2>
            <div className="space-y-4">
              {(guide.project_report?.methodology_walkthrough || []).map((step: any, i: number) => (
                <div key={i} className="flex gap-4">
                  <div className="flex flex-col items-center">
                    <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0">
                      {i + 1}
                    </div>
                    {i < (guide.project_report?.methodology_walkthrough?.length || 0) - 1 && (
                      <div className="w-px flex-1 bg-[var(--border)] mt-2" />
                    )}
                  </div>
                  <div className="flex-1 pb-4">
                    <p className="font-medium text-sm text-[var(--text-primary)]">{safeStr(step.step)}</p>
                    <p className="text-xs text-[var(--text-secondary)] mt-1 leading-relaxed">{safeStr(step.description)}</p>
                    {step.tools?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {step.tools.map((tool: string, j: number) => (
                          <span key={j} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-[10px] text-[var(--text-muted)]">
                            {tool}
                          </span>
                        ))}
                      </div>
                    )}
                    {step.time_estimate && (
                      <p className="text-xs text-[var(--text-muted)] mt-1 flex items-center gap-1">
                        <Clock size={10} /> {step.time_estimate}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Tech Stack & Methodology */}
          <div className="grid grid-cols-2 gap-4">
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Tech Stack</h2>
              {guide.project_report?.tech_stack_recommendations && (
                <div className="space-y-3">
                  {Object.entries(guide.project_report.tech_stack_recommendations).map(([key, vals]: any) => (
                    <div key={key}>
                      <p className="text-xs font-medium text-[var(--text-muted)] capitalize mb-1">{key.replace(/_/g, ' ')}</p>
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
              )}
            </div>
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Research Methodology</h2>
              {guide.project_report?.research_methodology && (
                <div className="space-y-2 text-xs text-[var(--text-secondary)]">
                  {Object.entries(guide.project_report.research_methodology).map(([key, val]: any) => (
                    <div key={key}>
                      <span className="font-medium text-[var(--text-muted)] capitalize">{key.replace(/_/g, ' ')}: </span>
                      <span>{safeStr(val)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Related Work Deep Dive */}
          {guide.project_report?.related_work_deep_dive?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Related Work Deep Dive</h2>
              <div className="space-y-3">
                {guide.project_report.related_work_deep_dive.map((topic: any, i: number) => (
                  <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="text-sm font-medium text-[var(--text-primary)] mb-2">{safeStr(topic.topic)}</p>
                    {topic.key_papers?.length > 0 && (
                      <ul className="space-y-1 mb-2">
                        {topic.key_papers.map((paper: string, j: number) => (
                          <li key={j} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                            <CheckCircle2 size={10} className="text-brand-400 mt-0.5 flex-shrink-0" />
                            {paper}
                          </li>
                        ))}
                      </ul>
                    )}
                    <p className="text-xs text-[var(--text-muted)] italic">{safeStr(topic.how_this_differs)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Project Timeline */}
          {guide.project_report?.project_timeline?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Project Timeline</h2>
              <div className="space-y-3">
                {guide.project_report.project_timeline.map((phase: any, i: number) => (
                  <div key={i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-600/20 text-emerald-400 text-[10px] font-bold flex-shrink-0">
                        {i + 1}
                      </div>
                      {i < guide.project_report.project_timeline.length - 1 && (
                        <div className="w-px flex-1 bg-[var(--border)] mt-2" />
                      )}
                    </div>
                    <div className="flex-1 pb-3">
                      <p className="text-sm font-medium text-[var(--text-primary)]">{safeStr(phase.phase)}</p>
                      <p className="text-xs text-[var(--text-muted)] flex items-center gap-1">
                        <Clock size={10} /> {safeStr(phase.duration)}
                      </p>
                      {phase.tasks?.length > 0 && (
                        <ul className="mt-1 space-y-0.5">
                          {phase.tasks.map((task: string, j: number) => (
                            <li key={j} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                              <CheckCircle2 size={10} className="text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                              {safeStr(task)}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Success Criteria & Challenges */}
          <div className="grid grid-cols-2 gap-4">
            {guide.project_report?.success_criteria?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Success Criteria</h2>
                <ul className="space-y-1.5">
                  {guide.project_report.success_criteria.map((c: string, i: number) => (
                    <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                      <CheckCircle2 size={10} className="text-emerald-400 mt-0.5 flex-shrink-0" />
                      {safeStr(c)}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {guide.project_report?.potential_challenges?.length > 0 && (
              <div className="card">
                <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3">Challenges & Mitigations</h2>
                <div className="space-y-2">
                  {guide.project_report.potential_challenges.map((c: string, i: number) => (
                    <div key={i} className="text-xs">
                      <p className="text-[var(--text-secondary)]">⚠ {safeStr(c)}</p>
                      {guide.project_report?.mitigation_strategies?.[i] && (
                        <p className="text-[var(--text-muted)] ml-3 mt-0.5">→ {safeStr(guide.project_report.mitigation_strategies[i])}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Presentation Section */}
          <div className="card">
            <div className="flex items-center justify-between mb-3">
              <h2 className="font-semibold text-sm text-[var(--text-primary)]">Presentation Slides</h2>
              <div className="flex gap-2">
                {!slides && (
                  <button onClick={handleGenerateSlides} disabled={slideGenerating} className="btn-secondary text-xs">
                    {slideGenerating ? <Loader2 size={12} className="animate-spin" /> : <Presentation size={12} />}
                    {slideGenerating ? 'Generating...' : 'Generate Slides'}
                  </button>
                )}
                {slides && (
                  <a href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/agents/${id}/download/pptx`}
                     className="btn-secondary text-xs"
                     target="_blank"
                  >
                    <Download size={12} /> Download PPTX
                  </a>
                )}
              </div>
            </div>
            {slides && (
              <div className="space-y-2">
                {slides.map((slide: any, i: number) => (
                  <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="text-sm font-medium text-[var(--text-primary)]">Slide {i + 1}: {slide.title}</p>
                    {slide.bullets?.length > 0 && (
                      <ul className="mt-1 space-y-0.5">
                        {slide.bullets.map((b: string, j: number) => (
                          <li key={j} className="text-xs text-[var(--text-secondary)]">• {b}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}
            {slideGenerating && (
              <p className="text-xs text-[var(--text-secondary)] flex items-center gap-2 mt-2">
                <Loader2 size={12} className="animate-spin" /> Generating slide content...
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
