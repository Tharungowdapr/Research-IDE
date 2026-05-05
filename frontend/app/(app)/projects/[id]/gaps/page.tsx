'use client';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Search, ArrowRight, Loader2, AlertCircle, TrendingUp, Lightbulb, BarChart2, ChevronDown, BookOpen, AlertTriangle, Zap } from 'lucide-react';
import { projectsAPI, getAuthToken } from '@/services/api';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';
import { useAuthStore } from '@/store/useAuthStore';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const TYPE_COLORS: Record<string,string> = {
  methodological:'badge-purple', dataset:'badge-blue', evaluation:'badge-yellow',
  application:'badge-green', theoretical:'badge-red', limitation:'badge-red',
  unexplored_assumption:'badge-yellow', contradiction:'badge-red',
};

function ScoreBar({ label, value, max = 10 }: { label: string; value: number; max?: number }) {
  const pct = ((value || 0) / max) * 100;
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-yellow-500' : 'bg-red-500';
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[var(--text-muted)] font-mono uppercase tracking-wider">{label}</span>
        <span className="font-mono text-[var(--text-primary)]">{value || 0}/{max}</span>
      </div>
      <div className="h-1.5 bg-[var(--bg-primary)] overflow-hidden">
        <div className={`h-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function GapCard({ gap, index }: { gap: any; index: number }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`card cursor-pointer transition-all hover:border-brand-500/30 ${expanded ? 'border-brand-500/40' : ''}`}
      onClick={() => setExpanded(!expanded)}
    >
      {/* Always visible header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="text-xs font-mono text-brand-500 font-bold">#{index + 1}</span>
            <h3 className="font-semibold text-sm text-[var(--text-primary)] font-mono">{gap.title}</h3>
          </div>
          <div className="flex flex-wrap gap-1.5 mb-3">
            <span className={TYPE_COLORS[gap.type] || 'badge-blue'}>{gap.type?.replace('_', ' ')}</span>
            <span className={`text-xs font-mono ${gap.confidence === 'high' ? 'text-emerald-400' : gap.confidence === 'medium' ? 'text-yellow-400' : 'text-red-400'}`}>
              {gap.confidence} confidence
            </span>
            {gap.evidence_strength && <span className="badge-purple">{gap.evidence_strength} evidence</span>}
            <span className="flex items-center gap-1 text-xs text-[var(--text-muted)] font-mono">
              <TrendingUp size={10} className="text-brand-500" />Novelty: {gap.novelty_potential}/10
            </span>
            {gap.final_score && (
              <span className="flex items-center gap-1 text-xs text-brand-500 font-mono">
                <BarChart2 size={10} />Score: {gap.final_score}
              </span>
            )}
          </div>
          {/* Preview: first ~150 chars or 2 lines when collapsed */}
          {!expanded && (
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed line-clamp-2">{gap.description}</p>
          )}
        </div>
        <ChevronDown
          size={16}
          className={`text-[var(--text-muted)] flex-shrink-0 mt-1 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
        />
      </div>

      {/* Expanded detail */}
      {expanded && (
        <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-5" onClick={(e) => e.stopPropagation()}>
          {/* Full Description */}
          <div>
            <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mb-2">
              Detailed Description
            </h4>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
              {gap.description}
            </p>
          </div>

          {/* Deep Explanation */}
          {gap.explanation && (
            <div className="border-l-2 border-brand-500 pl-4">
              <h4 className="text-xs font-mono uppercase tracking-wider text-brand-500 mb-2 flex items-center gap-1.5">
                <Zap size={11} /> Why This Gap Exists
              </h4>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                {gap.explanation}
              </p>
            </div>
          )}

          {/* Direct References */}
          {(gap.direct_references?.length > 0 || gap.supporting_papers?.length > 0) && (
            <div>
              <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mb-2 flex items-center gap-1.5">
                <BookOpen size={11} /> Source Papers ({(gap.direct_references || gap.supporting_papers || []).length})
              </h4>
              <div className="space-y-1.5">
                {(gap.direct_references || gap.supporting_papers || []).map((ref: string, j: number) => (
                  <div key={j} className="text-xs text-[var(--text-secondary)] border-l-2 border-[var(--border)] pl-3 py-1.5 bg-[var(--bg-secondary)]">
                    {ref}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Opportunity + Scores */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {gap.opportunity && (
              <div className="bg-brand-600/10 border border-brand-500/20 p-4">
                <h4 className="text-xs font-mono uppercase tracking-wider text-brand-500 mb-2 flex items-center gap-1.5">
                  <ArrowRight size={11} /> Research Opportunity
                </h4>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{gap.opportunity}</p>
              </div>
            )}
            <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-4 space-y-3">
              <h4 className="text-xs font-mono uppercase tracking-wider text-[var(--text-muted)] mb-2">
                Scores
              </h4>
              <ScoreBar label="Addressability" value={gap.addressability} />
              <ScoreBar label="Impact" value={gap.impact} />
              <ScoreBar label="Novelty" value={gap.novelty_potential} />
            </div>
          </div>

          {/* Gap Category */}
          {gap.gap_category && (
            <div className="text-xs text-[var(--text-muted)] font-mono flex items-center gap-2">
              <AlertTriangle size={10} />
              Category: <span className="text-[var(--text-secondary)]">{gap.gap_category?.replace('_', ' ')}</span>
            </div>
          )}

          {/* Quality Warning */}
          {gap._quality_issues?.length > 0 && (
            <div className="bg-yellow-500/10 border border-yellow-500/20 p-3">
              <p className="text-xs font-mono text-yellow-400 mb-1">Quality Notes</p>
              <ul className="text-xs text-yellow-300/70 space-y-0.5">
                {gap._quality_issues.map((issue: string, k: number) => (
                  <li key={k}>• {issue}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function GapsPageInner() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken } = useAuthStore();
  const [gaps, setGaps] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [streamLog, setStreamLog] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      setGaps(p.outputs?.gaps?.gaps || []);
      setLoading(false);
      if (!p.outputs?.gaps) handleAnalyze();
    });
  }, [id]);

  const handleAnalyze = async () => {
    setAnalyzing(true);
    setStreamLog([]);
    setError('');
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_URL}/api/agents/stream/${id}/gaps`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No stream');
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split('\n')) {
          if (!line.startsWith('data:')) continue;
          try {
            const evt = JSON.parse(line.slice(5).trim());
            if (evt.type === 'progress') setStreamLog(l => [...l, evt.message]);
            if (evt.type === 'result' && evt.data?.gaps) setGaps(evt.data.gaps);
            if (evt.type === 'error') setError(evt.message);
          } catch {}
        }
      }
    } catch (e: any) { setError(e.message); }
    finally { setAnalyzing(false); }
  };

  const handleGenerateIdeas = async () => {
    setGenerating(true);
    setError('');
    try {
      const token = getAuthToken();
      const response = await fetch(`${API_URL}/api/agents/stream/${id}/ideas`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No stream');
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        for (const line of decoder.decode(value).split('\n')) {
          if (!line.startsWith('data:')) continue;
          try {
            const evt = JSON.parse(line.slice(5).trim());
            if (evt.type === 'progress') setStreamLog(l => [...l, evt.message]);
            if (evt.type === 'done') router.push(`/projects/${id}/ideas`);
            if (evt.type === 'error') setError(evt.message);
          } catch {}
        }
      }
    } catch (e: any) { setError(e.message); }
    finally { setGenerating(false); }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] font-mono uppercase tracking-tight">Gap Analysis</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 3 of 7 — {gaps.length} gaps identified • Click to expand details</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleAnalyze} disabled={analyzing} className="btn-secondary text-sm">
            {analyzing ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
            Re-analyze
          </button>
          <button onClick={handleGenerateIdeas} disabled={generating || gaps.length === 0} className="btn-primary">
            {generating ? <Loader2 size={14} className="animate-spin" /> : <Lightbulb size={14} />}
            {generating ? 'Generating...' : 'Generate Ideas'}
          </button>
        </div>
      </div>

      {error && <div className="mb-4 bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2"><AlertCircle size={14}/>{error}</div>}

      {(analyzing || generating || streamLog.length > 0) && (
        <div className="mb-5 bg-[var(--bg-secondary)] border border-[var(--border)] p-4 font-mono text-xs space-y-1 max-h-36 overflow-auto">
          {streamLog.map((msg, i) => (
            <div key={i} className="flex items-center gap-2 text-[var(--text-secondary)]">
              <span className="text-brand-500">▸</span> {msg}
            </div>
          ))}
          {(analyzing || generating) && <div className="flex items-center gap-2 text-brand-500"><Loader2 size={10} className="animate-spin"/>Processing...</div>}
        </div>
      )}

      {gaps.length === 0 && !analyzing ? (
        <div className="card text-center py-16">
          <Search size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No gaps yet — analyzing papers...</p>
        </div>
      ) : (
        <div className="space-y-4">
          {gaps.map((gap, i) => (
            <GapCard key={i} gap={gap} index={i} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function GapsPage() {
  return <ErrorBoundary><GapsPageInner /></ErrorBoundary>;
}
