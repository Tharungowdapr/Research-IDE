'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Brain, ArrowRight, Loader2, Tag, Search, AlertCircle,
  Lightbulb, Globe, Cpu, CheckCircle2,
} from 'lucide-react';
import { projectsAPI, pipelineAPI } from '@/services/api';

export default function ProjectInputPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [project, setProject] = useState<any>(null);
  const [intent, setIntent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState(false);
  const [retrieving, setRetrieving] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      setProject(p);
      if (p.outputs?.intent) setIntent(p.outputs.intent);
      setLoading(false);
    });
  }, [id]);

  const handleExtractIntent = async () => {
    setExtracting(true);
    setError('');
    try {
      const result = await pipelineAPI.extractIntent(id);
      setIntent(result.intent);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Intent extraction failed. Check your AI settings.');
    } finally {
      setExtracting(false);
    }
  };

  const handleRetrievePapers = async () => {
    setRetrieving(true);
    setError('');
    try {
      await pipelineAPI.retrievePapers(id, 20);
      router.push(`/projects/${id}/papers`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Paper retrieval failed.');
    } finally {
      setRetrieving(false);
    }
  };

  if (loading) {
    return <div className="p-8 flex items-center justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-[var(--text-primary)] truncate">{project?.title}</h1>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 1 of 7 — Intent Extraction & NLP Analysis</p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Main layout: Input | NLP Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Left: Input */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Brain size={16} className="text-brand-400" />
            <h2 className="font-semibold text-sm text-[var(--text-primary)]">Research Input</h2>
          </div>
          <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-4 text-sm text-[var(--text-secondary)] leading-relaxed min-h-[200px]">
            {project?.input_text}
          </div>
          <button
            onClick={handleExtractIntent}
            disabled={extracting}
            className="btn-primary mt-4 w-full justify-center"
          >
            {extracting ? (
              <><Loader2 size={14} className="animate-spin" /> Extracting intent...</>
            ) : (
              <><Brain size={14} /> {intent ? 'Re-analyze' : 'Analyze with AI'}</>
            )}
          </button>
        </div>

        {/* Right: NLP Breakdown */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <Cpu size={16} className="text-emerald-400" />
            <h2 className="font-semibold text-sm text-[var(--text-primary)]">NLP Breakdown</h2>
            {intent && <span className="badge-green ml-auto">Analyzed</span>}
          </div>

          {!intent ? (
            <div className="flex flex-col items-center justify-center min-h-[200px] text-center">
              <Brain size={32} className="text-[var(--text-muted)] mb-3" />
              <p className="text-sm text-[var(--text-secondary)]">Click "Analyze with AI" to extract</p>
              <p className="text-xs text-[var(--text-muted)] mt-1">Domain, keywords, constraints, and search queries</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Domain */}
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Domain</p>
                <div className="flex flex-wrap gap-1.5">
                  {(intent.domain || []).map((d: string) => (
                    <span key={d} className="badge-blue">{d}</span>
                  ))}
                </div>
              </div>

              {/* Task */}
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Task</p>
                <p className="text-sm text-[var(--text-primary)]">{intent.task}</p>
              </div>

              {/* Constraints */}
              {intent.constraints && (
                <div>
                  <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1.5">Constraints</p>
                  <div className="flex flex-wrap gap-1.5">
                    {Object.entries(intent.constraints)
                      .filter(([k, v]) => v && v !== 'unspecified' && k !== 'other')
                      .map(([k, v]) => (
                        <span key={k} className="badge-yellow">
                          {k}: {String(v)}
                        </span>
                      ))}
                  </div>
                </div>
              )}

              {/* Keywords */}
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1.5 flex items-center gap-1">
                  <Tag size={10} /> Keywords
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {(intent.keywords || []).map((k: string) => (
                    <span key={k} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                      {k}
                    </span>
                  ))}
                </div>
              </div>

              {/* Queries */}
              <div>
                <p className="text-xs font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1.5 flex items-center gap-1">
                  <Search size={10} /> Search Queries
                </p>
                <div className="space-y-1.5">
                  {(intent.queries || []).map((q: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2.5 py-1.5">
                      <span className="text-xs text-brand-400 font-mono mt-0.5">{i + 1}.</span>
                      <span className="text-xs text-[var(--text-secondary)] font-mono">{q}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Problem Statement */}
              {intent.problem_statement && (
                <div className="rounded-lg bg-brand-600/10 border border-brand-500/20 p-3">
                  <p className="text-xs font-medium text-brand-400 mb-1 flex items-center gap-1">
                    <Lightbulb size={11} /> Problem Statement
                  </p>
                  <p className="text-xs text-[var(--text-secondary)]">{intent.problem_statement}</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Proceed Button */}
      {intent && (
        <div className="card border-emerald-500/20 bg-emerald-500/5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <CheckCircle2 size={18} className="text-emerald-400" />
              <div>
                <p className="text-sm font-medium text-[var(--text-primary)]">Intent extracted successfully</p>
                <p className="text-xs text-[var(--text-muted)]">
                  Found {intent.keywords?.length || 0} keywords and {intent.queries?.length || 0} search queries
                </p>
              </div>
            </div>
            <button
              onClick={handleRetrievePapers}
              disabled={retrieving}
              className="btn-primary"
            >
              {retrieving ? (
                <><Loader2 size={14} className="animate-spin" /> Fetching papers...</>
              ) : (
                <>Retrieve Papers <ArrowRight size={14} /></>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
