'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Lightbulb, Star, Zap, ArrowRight, Loader2, CheckCircle2, Clock, BarChart2, AlertCircle, MessageSquare, RefreshCw, Plus, Filter, Send } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';
import { useStream } from '@/hooks/useStream';
import { StreamLog } from '@/components/ui/StreamLog';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

const FEASIBILITY_COLORS: Record<string,string> = { high:'badge-green', medium:'badge-yellow', low:'badge-red', High:'badge-green', Medium:'badge-yellow', Low:'badge-red' };
const COMPLEXITY_COLORS: Record<string,string> = { High:'badge-red', Medium:'badge-yellow', Low:'badge-green', high:'badge-red', medium:'badge-yellow', low:'badge-green' };
const DIFFICULTY_COLORS: Record<string,string> = { beginner:'badge-green', intermediate:'badge-blue', advanced:'badge-purple' };

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span className={`font-medium ${color}`}>{(value||0).toFixed(1)}/10</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--bg-secondary)] overflow-hidden">
        <div className={`h-full rounded-full ${color==='text-brand-400'?'bg-brand-500':'bg-emerald-500'}`} style={{width:`${((value||0)/10)*100}%`}} />
      </div>
    </div>
  );
}

function IdeasPageInner() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [ideas, setIdeas] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selecting, setSelecting] = useState<number|null>(null);
  const [error, setError] = useState('');
  const [loadingMore, setLoadingMore] = useState(false);
  const { stream, streaming, log, error: streamError } = useStream();

  // Filters & Submission
  const [complexityFilter, setComplexityFilter] = useState<string>('');
  const [feasibilityFilter, setFeasibilityFilter] = useState<string>('');
  const [userIdeaText, setUserIdeaText] = useState('');
  const [submittingIdea, setSubmittingIdea] = useState(false);
  const [showSubmitModal, setShowSubmitModal] = useState(false);

  const applyFilters = async () => {
    setLoading(true);
    try {
      const result = await agentsAPI.filterIdeas(id, complexityFilter || undefined, feasibilityFilter || undefined);
      setIdeas(result.ideas || []);
    } catch(e) {
      setError('Failed to filter ideas');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    applyFilters();
  }, [complexityFilter, feasibilityFilter]);

  const handleSubmitIdea = async () => {
    if (!userIdeaText.trim()) return;
    setSubmittingIdea(true);
    setError('');
    try {
      const res = await agentsAPI.submitUserIdea(id, userIdeaText);
      setIdeas([res.refined_idea, ...ideas]);
      setShowSubmitModal(false);
      setUserIdeaText('');
    } catch(e: any) {
      setError(e.response?.data?.detail || 'Failed to submit idea');
    } finally {
      setSubmittingIdea(false);
    }
  };

  useEffect(() => {
    // Initial fetch handled by applyFilters above, but if we need full fetch:
    projectsAPI.get(id).then((p) => {
      const saved = p.outputs?.ideas?.ideas;
      if (saved && saved.length > 0 && !complexityFilter && !feasibilityFilter) {
        setIdeas(saved);
        setLoading(false);
      } else if (!saved || saved.length === 0) {
        setLoading(false);
        handleGenerate();
      }
    }).catch(() => { setError('Project not found'); setLoading(false); });
  }, [id]);

  const handleGenerateMore = async () => {
    setLoadingMore(true);
    setError('');
    try {
      const result = await agentsAPI.generateMoreIdeas(id);
      setIdeas(result.total_ideas || ideas.concat(result.new_ideas || []));
      // Reload from server
      const p = await projectsAPI.get(id);
      if (p.outputs?.ideas?.ideas) setIdeas(p.outputs.ideas.ideas);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to generate more ideas');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleGenerate = () => {
    stream(id, 'ideas', {
      onResult: (data) => { if (data?.ideas) setIdeas(data.ideas); },
      onError: (msg) => setError(msg),
    });
  };

  const handleSelect = async (index: number) => {
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

  const displayError = error || streamError;
  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400"/></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)] font-mono tracking-tight uppercase">Research Ideas</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 4 of 7 — Critic-Defender ranked ideas</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowSubmitModal(true)} disabled={streaming || loadingMore} className="btn-secondary text-sm border-brand-500/50 text-brand-400">
            <Plus size={14}/> Submit Idea
          </button>
          <button onClick={handleGenerateMore} disabled={streaming || loadingMore} className="btn-secondary text-sm">
            {loadingMore ? <Loader2 size={14} className="animate-spin"/> : <Plus size={14}/>}
            4 More Ideas
          </button>
          <button onClick={handleGenerate} disabled={streaming} className="btn-ghost text-sm">
            {streaming ? <Loader2 size={14} className="animate-spin"/> : <RefreshCw size={14}/>}
            Reset
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-6 flex gap-3 items-center">
        <Filter size={14} className="text-[var(--text-muted)]" />
        <select 
          className="text-xs bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-2 py-1 text-[var(--text-primary)] focus:outline-none focus:border-brand-500"
          value={complexityFilter} onChange={(e) => setComplexityFilter(e.target.value)}
        >
          <option value="">All Complexities</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
        </select>
        <select 
          className="text-xs bg-[var(--bg-secondary)] border border-[var(--border)] rounded px-2 py-1 text-[var(--text-primary)] focus:outline-none focus:border-brand-500"
          value={feasibilityFilter} onChange={(e) => setFeasibilityFilter(e.target.value)}
        >
          <option value="">All Feasibilities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
      </div>

      {/* Submit Modal */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
          <div className="bg-[#0a0a0a] border border-[#333] p-6 rounded-none w-full max-w-2xl">
            <h2 className="text-xl font-mono uppercase text-white mb-4">Submit Custom Idea</h2>
            <p className="text-sm text-gray-400 mb-4">Describe your research idea. The system will critique it, identify flaws, and refine it into our standard structured format.</p>
            <textarea 
              value={userIdeaText}
              onChange={(e) => setUserIdeaText(e.target.value)}
              placeholder="Enter your idea here..."
              className="w-full h-32 bg-black border border-[#333] text-white p-3 font-mono text-sm mb-4 focus:border-brand-500 focus:outline-none resize-none"
            />
            <div className="flex justify-end gap-3">
              <button onClick={() => setShowSubmitModal(false)} className="px-4 py-2 text-xs font-mono text-gray-400 hover:text-white uppercase border border-transparent">Cancel</button>
              <button onClick={handleSubmitIdea} disabled={submittingIdea || !userIdeaText.trim()} className="px-4 py-2 text-xs font-mono bg-white text-black hover:bg-gray-200 uppercase flex items-center gap-2">
                {submittingIdea ? <Loader2 size={14} className="animate-spin" /> : <Send size={14}/>}
                Analyze & Refine
              </button>
            </div>
          </div>
        </div>
      )}

      {displayError && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2"><AlertCircle size={14}/>{displayError}</div>}
      <StreamLog log={log} streaming={streaming} label="Running Critic-Defender loop..." />

      {ideas.length === 0 && !streaming ? (
        <div className="card text-center py-16"><Lightbulb size={32} className="mx-auto mb-3 text-[var(--text-muted)]"/><p className="text-sm text-[var(--text-secondary)]">No ideas yet — generating...</p></div>
      ) : (
        <div className="space-y-5">
          {ideas.map((idea, i) => (
            <div key={i} className={`card transition-all hover:border-brand-500/30 ${i===0?'border-brand-500/40 bg-brand-600/5':''}`}>
              {i===0 && <div className="flex items-center gap-1.5 mb-3"><Star size={14} className="text-yellow-400"/><span className="text-xs font-medium text-yellow-400">Top Recommendation</span></div>}

              {/* Critic badge */}
              {idea.critique_summary && (
                <div className={`flex items-center gap-1.5 mb-3 px-2.5 py-1.5 text-xs ${idea.survived_critique ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400' : 'bg-yellow-500/10 border border-yellow-500/20 text-yellow-400'}`}>
                  <MessageSquare size={11}/>
                  <span className="font-medium">{idea.survived_critique ? 'Passed peer review:' : 'Note:'}</span>
                  <span className="opacity-80">{idea.critique_summary}</span>
                </div>
              )}

              <div className="grid grid-cols-3 gap-5">
                <div className="col-span-2 space-y-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-[var(--text-muted)] font-mono">#{i+1}</span>
                      <h3 className="font-semibold text-[var(--text-primary)] font-mono text-lg">{idea.title}</h3>
                    </div>
                    <p className="text-sm text-[var(--text-secondary)] leading-relaxed mt-2 mb-3">{idea.description}</p>
                    <div className="flex flex-wrap gap-1.5 mb-3">
                      <span className={FEASIBILITY_COLORS[idea.feasibility]||'badge-blue'}>{idea.feasibility} feasibility</span>
                      <span className={COMPLEXITY_COLORS[idea.complexity]||'badge-blue'}>{idea.complexity} complexity</span>
                      {idea.estimated_time && <span className="flex items-center gap-1 text-xs text-[var(--text-muted)] border border-[var(--border)] px-1.5 font-mono"><Clock size={10}/>{idea.estimated_time}</span>}
                      {idea.difficulty && <span className={DIFFICULTY_COLORS[idea.difficulty]||'badge-blue'}>{idea.difficulty}</span>}
                      {idea.is_user_submitted && <span className="badge-purple">User Submitted</span>}
                    </div>
                  </div>
                  
                  <div className="space-y-4">
                    <div>
                      <p className="text-xs font-mono text-[var(--text-muted)] mb-1.5 uppercase tracking-wider">Problem Statement</p>
                      <p className="text-sm text-[var(--text-primary)] leading-relaxed whitespace-pre-line">{idea.problem_statement || idea.description}</p>
                    </div>
                    <div className="border-l-2 border-brand-500 pl-4">
                      <p className="text-xs font-mono text-brand-500 mb-1.5 uppercase tracking-wider flex items-center gap-1"><Zap size={10}/> Proposed Solution</p>
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">{idea.proposed_solution || idea.approach}</p>
                    </div>
                    <div>
                      <p className="text-xs font-mono text-emerald-400 mb-1.5 flex items-center gap-1 uppercase tracking-wider"><ArrowRight size={10}/> Why It Addresses Gap</p>
                      <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">{idea.why_it_addresses_gap || idea.novelty}</p>
                    </div>
                    {idea.potential_challenges && (
                      <div className="border-l-2 border-yellow-500/50 pl-4 py-1">
                        <p className="text-xs font-mono text-yellow-500/80 mb-1.5 uppercase tracking-wider">Potential Challenges</p>
                        <p className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">{idea.potential_challenges}</p>
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs pt-3 border-t border-[var(--border)]">
                    {idea.suggested_methods?.length>0 && <div><p className="font-medium text-[var(--text-muted)] mb-1 font-mono uppercase">Methods</p><ul className="space-y-0.5 text-[var(--text-secondary)]">{idea.suggested_methods.slice(0,4).map((m:string,j:number)=><li key={j}>• {m}</li>)}</ul></div>}
                    {idea.suggested_datasets?.length>0 && <div><p className="font-medium text-[var(--text-muted)] mb-1 font-mono uppercase">Datasets</p><ul className="space-y-0.5 text-[var(--text-secondary)]">{idea.suggested_datasets.slice(0,4).map((d:string,j:number)=><li key={j}>• {d}</li>)}</ul></div>}
                  </div>

                  {/* Quality validation warning */}
                  {idea._quality_issues?.length > 0 && (
                    <div className="bg-yellow-500/10 border border-yellow-500/20 p-3 mt-2">
                      <p className="text-xs font-mono text-yellow-400 mb-1">Quality Notes</p>
                      <ul className="text-xs text-yellow-300/70 space-y-0.5">
                        {idea._quality_issues.map((issue: string, k: number) => (
                          <li key={k}>• {issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
                <div className="space-y-4">
                  <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-3 space-y-3">
                    <p className="text-xs font-medium text-[var(--text-secondary)] flex items-center gap-1 font-mono uppercase"><BarChart2 size={11}/> Scores</p>
                    <ScoreBar label="Innovation Level" value={idea.innovation_level || idea.novelty_score} color="text-brand-400"/>
                    <ScoreBar label="Feasibility" value={idea.feasibility_score} color="text-emerald-400"/>
                  </div>
                  {idea.assumptions?.length > 0 && (
                    <div className="bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                      <p className="text-xs font-mono text-[var(--text-muted)] mb-1.5 uppercase">Key Assumptions</p>
                      <ul className="text-xs text-[var(--text-secondary)] space-y-1">
                        {idea.assumptions.slice(0,3).map((a: string, k: number) => <li key={k} className="flex items-start gap-1"><span className="text-brand-500">→</span>{a}</li>)}
                      </ul>
                    </div>
                  )}
                  {idea.failure_modes?.length > 0 && (
                    <div className="bg-red-500/5 border border-red-500/20 p-3">
                      <p className="text-xs font-mono text-red-400 mb-1.5 uppercase">Failure Modes</p>
                      <ul className="text-xs text-red-300/70 space-y-1">
                        {idea.failure_modes.slice(0,2).map((f: string, k: number) => <li key={k} className="flex items-start gap-1"><span className="text-red-400">⚠</span>{f}</li>)}
                      </ul>
                    </div>
                  )}
                  <button onClick={()=>handleSelect(i)} disabled={selecting!==null}
                    className={`w-full ${i===0?'btn-primary':'btn-secondary'} justify-center`}>
                    {selecting===i ? <><Loader2 size={14} className="animate-spin"/>Selecting...</> : <><CheckCircle2 size={14}/>Select This Idea</>}
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

export default function IdeasPage() {
  return <ErrorBoundary><IdeasPageInner /></ErrorBoundary>;
}
