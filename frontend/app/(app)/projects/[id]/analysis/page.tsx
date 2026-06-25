'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Brain, ArrowRight, Loader2, Tag, Search, AlertCircle,
  Globe, Cpu, CheckCircle2, Zap, FileText, Hash, BarChart3,
  Network, ChevronDown, ChevronUp, Lightbulb,
} from 'lucide-react';
import { projectsAPI, pipelineAPI } from '@/services/api';
import AutoPipeline from '@/components/project/AutoPipeline';

export default function AnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [project, setProject] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState('');
  const [showDepGraph, setShowDepGraph] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        setProject(p);
        if (p.outputs?.analysis) setAnalysis(p.outputs.analysis);
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  useEffect(() => {
    if (window.location.hash === '#auto-pipeline') {
      setTimeout(() => {
        document.getElementById('auto-pipeline')?.scrollIntoView({ behavior: 'smooth' });
      }, 500);
    }
  }, []);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setError('');
    try {
      const result = await pipelineAPI.analyzeNLP(id);
      setAnalysis(result.analysis);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'NLP analysis failed.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleProceedToPapers = async () => {
    try {
      await pipelineAPI.extractIntent(id);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to extract search intent.');
      return;
    }
    try {
      await pipelineAPI.retrievePapers(id, 20);
      router.push(`/projects/${id}/papers`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to retrieve papers.');
    }
  };

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;
  }

  return (
    <div className="p-8 max-w-6xl mx-auto">
      {error && (
        <div className="mb-6 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} /> {String(error)}
        </div>
      )}

      <div className="mb-6">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">NLP Analysis</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 1 of 13</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ──────── LEFT COLUMN ──────── */}
        <div className="space-y-6">
          {/* Research Input — large and prominent like the original */}
          <div className="card">
            <div className="flex items-center gap-2 mb-4">
              <Brain size={16} className="text-brand-400" />
              <h2 className="font-semibold text-sm text-[var(--text-primary)]">Research Input</h2>
              {analysis && <span className="badge-green ml-auto">Analyzed</span>}
            </div>
            <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-5 text-sm text-[var(--text-secondary)] leading-relaxed min-h-[200px] whitespace-pre-wrap">
              {project?.input_text}
            </div>
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className="btn-primary mt-4 w-full justify-center"
            >
              {analyzing ? (
                <><Loader2 size={14} className="animate-spin" /> Running deep NLP analysis...</>
              ) : (
                <><Brain size={14} /> {analysis ? 'Re-run NLP Analysis' : 'Run NLP Analysis'}</>
              )}
            </button>
          </div>

          {/* Text Statistics */}
          {analysis?.stats && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <Hash size={16} className="text-brand-400" />
                <h2 className="font-semibold text-sm text-[var(--text-primary)]">Text Statistics</h2>
              </div>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Tokens', value: analysis.stats.tokens },
                  { label: 'Sentences', value: analysis.stats.sentences },
                  { label: 'Characters', value: analysis.stats.characters },
                ].map((s) => (
                  <div key={s.label} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-4 text-center">
                    <p className="text-xl font-bold text-brand-400">{s.value}</p>
                    <p className="text-[11px] text-[var(--text-muted)] mt-1">{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* POS Distribution */}
          {analysis?.pos_distribution?.length > 0 && (
            <div className="card">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 size={16} className="text-brand-400" />
                <h2 className="font-semibold text-sm text-[var(--text-primary)]">POS Distribution</h2>
              </div>
              <div className="space-y-2">
                {analysis.pos_distribution.map((p: any) => (
                  <div key={p.tag} className="flex items-center gap-3 text-xs">
                    <span className="w-20 text-[var(--text-secondary)] font-medium">{p.tag}</span>
                    <div className="flex-1 h-3 rounded-full bg-[var(--bg-secondary)] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand-500/60"
                        style={{ width: `${Math.min(p.count / Math.max(...analysis.pos_distribution.map((x: any) => x.count)) * 100, 100)}%` }}
                      />
                    </div>
                    <span className="w-8 text-right text-[var(--text-muted)] tabular-nums">{p.count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ──────── RIGHT COLUMN ──────── */}
        <div className="space-y-6">
          {!analysis ? (
            /* Empty state — matches original input page style */
            <div className="card min-h-[400px] flex flex-col items-center justify-center text-center">
              <Cpu size={48} className="text-[var(--text-muted)] mb-4" />
              <p className="text-sm font-medium text-[var(--text-primary)]">No NLP analysis yet</p>
              <p className="text-xs text-[var(--text-muted)] mt-1 max-w-xs">
                Click &ldquo;Run NLP Analysis&rdquo; to extract domain, entities, keyphrases, dependency trees, and search queries from your research input.
              </p>
            </div>
          ) : (
            <>
              {/* Domain Classification */}
              {analysis?.domain && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <Globe size={16} className="text-brand-400" />
                    <h2 className="font-semibold text-sm text-[var(--text-primary)]">Domain Classification</h2>
                  </div>
                  <div className="flex items-center gap-3 flex-wrap">
                    <span className="badge-purple text-sm">{analysis.domain.broad}</span>
                    <span className="text-xs text-[var(--text-muted)]">
                      Confidence: {Math.round((analysis.domain.confidence || 0) * 100)}%
                    </span>
                  </div>
                  {analysis.domain.matched_keywords?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {analysis.domain.matched_keywords.map((kw: string) => (
                        <span key={kw} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-[11px] text-[var(--text-muted)]">{kw}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Named Entities */}
              {analysis?.entities?.length > 0 && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <Tag size={16} className="text-brand-400" />
                    <h2 className="font-semibold text-sm text-[var(--text-primary)]">Named Entities</h2>
                    <span className="badge-blue ml-auto">{analysis.entities.length} found</span>
                  </div>
                  <div className="space-y-2">
                    {analysis.entities.map((e: any, i: number) => (
                      <div key={i} className="flex items-center gap-3 text-sm">
                        <span className="rounded bg-brand-600/20 text-brand-400 px-2 py-0.5 text-[11px] font-medium whitespace-nowrap">{e.label_name}</span>
                        <span className="text-[var(--text-secondary)]">{e.text}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Keyphrases */}
              {analysis?.keyphrases?.length > 0 && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <Zap size={16} className="text-brand-400" />
                    <h2 className="font-semibold text-sm text-[var(--text-primary)]">Keyphrases</h2>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {analysis.keyphrases.map((kp: any) => (
                      <span
                        key={kp.phrase}
                        className="rounded-md px-2.5 py-1 text-xs border"
                        style={{
                          backgroundColor: `hsla(${kp.score * 240}, 60%, 50%, 0.15)`,
                          borderColor: `hsla(${kp.score * 240}, 60%, 50%, 0.3)`,
                          color: `hsla(${kp.score * 240}, 60%, 70%, 1)`,
                        }}
                      >
                        {kp.phrase}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Dependency Tree */}
              {analysis?.dependency_tree && (
                <div className="card">
                  <button
                    onClick={() => setShowDepGraph(!showDepGraph)}
                    className="w-full flex items-center justify-between mb-2"
                  >
                    <div className="flex items-center gap-2">
                      <Network size={16} className="text-brand-400" />
                      <h2 className="font-semibold text-sm text-[var(--text-primary)]">Dependency Tree</h2>
                    </div>
                    {showDepGraph ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </button>
                  {showDepGraph && (
                    <div className="text-xs text-[var(--text-secondary)] space-y-1 font-mono mt-2">
                      <RenderDepTree node={analysis.dependency_tree} depth={0} />
                    </div>
                  )}
                </div>
              )}

              {/* Search Queries */}
              {analysis?.search_queries?.length > 0 && (
                <div className="card">
                  <div className="flex items-center gap-2 mb-4">
                    <Search size={16} className="text-brand-400" />
                    <h2 className="font-semibold text-sm text-[var(--text-primary)]">Generated Search Queries</h2>
                  </div>
                  <div className="space-y-2">
                    {analysis.search_queries.map((q: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-3 py-2">
                        <span className="text-xs text-brand-400 font-mono mt-0.5">{i + 1}.</span>
                        <span className="text-xs text-[var(--text-secondary)]">{q}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Summary */}
              {analysis?.summary && (
                <div className="card border-brand-500/20 bg-brand-600/5">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb size={16} className="text-brand-400" />
                    <h2 className="font-semibold text-sm text-[var(--text-primary)]">Analysis Summary</h2>
                  </div>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{analysis.summary}</p>
                </div>
              )}

              {/* Proceed button */}
              <div className="card border-emerald-500/20 bg-emerald-500/5">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 size={18} className="text-emerald-400" />
                    <div>
                      <p className="text-sm font-medium text-[var(--text-primary)]">NLP analysis complete</p>
                      <p className="text-xs text-[var(--text-muted)]">
                        {analysis.keyphrases?.length || 0} keyphrases &bull; {analysis.entities?.length || 0} entities &bull; {analysis.search_queries?.length || 0} search queries
                      </p>
                    </div>
                  </div>
                  <button onClick={handleProceedToPapers} className="btn-primary">
                    <Search size={14} /> Search Papers <ArrowRight size={14} />
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Auto Pipeline */}
      <div id="auto-pipeline" className="mt-8">
        <AutoPipeline projectId={id} />
      </div>
    </div>
  );
}

function RenderDepTree({ node, depth }: { node: any; depth: number }) {
  if (!node) return null;
  return (
    <div>
      <div style={{ paddingLeft: depth * 16 }} className="flex items-center gap-1.5">
        <span className="text-brand-400">{node.word}</span>
        {node.dep && <span className="text-[var(--text-muted)] text-[10px]">({node.dep})</span>}
        {node.tag && <span className="text-[var(--text-muted)] text-[10px]">[{node.tag}]</span>}
      </div>
      {node.children?.map((child: any, i: number) => (
        <RenderDepTree key={i} node={child} depth={depth + 1} />
      ))}
    </div>
  );
}
