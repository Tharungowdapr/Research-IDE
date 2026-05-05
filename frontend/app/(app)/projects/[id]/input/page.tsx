'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Brain, ArrowRight, Loader2, Tag, Search as SearchIcon,
  AlertCircle, Lightbulb, CheckCircle2, Edit2, Save, X,
  ChevronDown, ChevronRight as ChevronRightIcon, BookOpen,
  Layers, GitBranch, MessageSquare, Shuffle, Hash, Scissors,
  BarChart2, Zap, Globe, Target,
} from 'lucide-react';
import { projectsAPI, pipelineAPI, getAuthToken } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { StreamLog } from '@/components/ui/StreamLog';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ── Small UI helpers ───────────────────────────────────────────────────────────
function Section({ icon: Icon, title, color = 'text-brand-400', children, defaultOpen = true }: any) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-[var(--border)] rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2.5 bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-all text-left"
      >
        <Icon size={13} className={color} />
        <span className="text-xs font-semibold text-[var(--text-primary)] flex-1">{title}</span>
        {open ? <ChevronDown size={12} className="text-[var(--text-muted)]" /> : <ChevronRightIcon size={12} className="text-[var(--text-muted)]" />}
      </button>
      {open && <div className="p-3 bg-[var(--bg-card)] space-y-2">{children}</div>}
    </div>
  );
}

function KV({ label, value, mono = false }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2 text-xs">
      <span className="text-[var(--text-muted)] flex-shrink-0 w-28">{label}</span>
      <span className={`text-[var(--text-secondary)] ${mono ? 'font-mono' : ''}`}>{value}</span>
    </div>
  );
}

function TagList({ items, color = 'badge-blue' }: { items: string[]; color?: string }) {
  if (!items?.length) return <span className="text-xs text-[var(--text-muted)]">None detected</span>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {items.map((item, i) => <span key={i} className={color}>{item}</span>)}
    </div>
  );
}

function TokenDisplay({ tokens, highlight }: { tokens: string[]; highlight?: string }) {
  if (!tokens?.length) return null;
  return (
    <div className="flex flex-wrap gap-1">
      {tokens.map((tok, i) => (
        <span key={i} className={`rounded px-1.5 py-0.5 text-xs font-mono border ${
          tok.startsWith('##')
            ? 'bg-purple-500/10 border-purple-500/30 text-purple-400'
            : 'bg-[var(--bg-secondary)] border-[var(--border)] text-[var(--text-secondary)]'
        }`}>
          {tok}
        </span>
      ))}
    </div>
  );
}

function BarRow({ label, value, max = 100, color = 'bg-brand-500' }: any) {
  const pct = Math.min((value / max) * 100, 100);
  return (
    <div>
      <div className="flex justify-between text-xs mb-0.5">
        <span className="text-[var(--text-muted)]">{label}</span>
        <span className="text-[var(--text-secondary)] font-mono">{value}</span>
      </div>
      <div className="h-1.5 rounded-full bg-[var(--bg-secondary)] overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

// ── Stream helper ──────────────────────────────────────────────────────────────
async function fetchStream(
  url: string,
  onProgress: (m: string) => void,
  onResult: (d: any) => void,
  onDone: () => void,
  onError: (m: string) => void,
) {
  const token = getAuthToken();
  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error(`Server error: ${res.status}`);
  const reader = res.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) throw new Error('No stream body');
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    for (const line of decoder.decode(value, { stream: true }).split('\n')) {
      if (!line.startsWith('data:')) continue;
      try {
        const evt = JSON.parse(line.slice(5).trim());
        if (evt.type === 'progress') onProgress(evt.message);
        else if (evt.type === 'result') onResult(evt.data);
        else if (evt.type === 'done') onDone();
        else if (evt.type === 'error') onError(evt.message);
      } catch {}
    }
  }
}

// ── NLP Breakdown Panel ────────────────────────────────────────────────────────
function NLPBreakdown({ intent }: { intent: any }) {
  const nlp = intent?.nlp_analysis || {};
  const morph = nlp.morphological || {};
  const syntax = nlp.syntactic || {};
  const semantic = nlp.semantic || {};
  const pragmatic = nlp.pragmatic || {};
  const discourse = nlp.discourse || {};
  const tok = intent?.tokenization_demo || {};
  const sw = intent?.stop_words_analysis || {};
  const stem = intent?.stemming_lemmatization || {};

  return (
    <div className="space-y-2">

      {/* Overview */}
      <Section icon={Target} title="Research Overview" color="text-emerald-400">
        <KV label="Domain" value={(intent.domain || []).join(', ')} />
        <KV label="Task" value={intent.task || '—'} />
        <KV label="Intent Type" value={pragmatic.intent_type || '—'} />
        <KV label="Technical Level" value={semantic.technical_level || '—'} />
        <KV label="Semantic Field" value={semantic.semantic_field || '—'} />
        {intent.problem_statement && (
          <div className="mt-2 rounded-lg bg-brand-600/10 border border-brand-500/20 p-2.5">
            <p className="text-[10px] font-medium text-brand-400 mb-1">Problem Statement</p>
            <p className="text-xs text-[var(--text-secondary)]">{intent.problem_statement}</p>
          </div>
        )}
      </Section>

      {/* Tokenization */}
      <Section icon={Scissors} title="Tokenization Analysis" color="text-yellow-400">
        {tok.original_sentence && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Original Input (first sentence)</p>
            <p className="text-xs text-[var(--text-secondary)] italic bg-[var(--bg-secondary)] rounded p-2">"{tok.original_sentence}"</p>
          </div>
        )}
        {tok.sentence_tokens?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Sentence Tokenization ({tok.sentence_tokens.length} sentences)</p>
            <div className="space-y-1">
              {tok.sentence_tokens.map((s: string, i: number) => (
                <div key={i} className="flex gap-2">
                  <span className="text-[10px] text-brand-400 font-mono mt-0.5 flex-shrink-0">S{i+1}</span>
                  <span className="text-xs text-[var(--text-secondary)] truncate">{s}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {tok.word_tokens?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Word Tokens</p>
            <TokenDisplay tokens={tok.word_tokens} />
          </div>
        )}
        {tok.subword_tokens_bpe?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">
              Subword Tokens (BPE — <span className="text-purple-400">##continuation</span>)
            </p>
            <TokenDisplay tokens={tok.subword_tokens_bpe} />
          </div>
        )}
        {tok.char_ngrams_sample?.length > 0 && (
          <div>
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Character N-grams (3-gram sample)</p>
            <div className="flex gap-1 flex-wrap">
              {tok.char_ngrams_sample.map((ng: string, i: number) => (
                <span key={i} className="rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 px-1.5 py-0.5 text-xs font-mono">"{ng}"</span>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* Stop Words */}
      <Section icon={Shuffle} title="Stop Word Filtering" color="text-orange-400">
        <div className="grid grid-cols-3 gap-2 mb-2">
          <div className="rounded-lg bg-[var(--bg-secondary)] p-2 text-center">
            <p className="text-lg font-bold text-[var(--text-primary)]">{sw.total_words || 0}</p>
            <p className="text-[10px] text-[var(--text-muted)]">Total words</p>
          </div>
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 p-2 text-center">
            <p className="text-lg font-bold text-red-400">{sw.stop_words_removed?.length || 0}</p>
            <p className="text-[10px] text-[var(--text-muted)]">Removed</p>
          </div>
          <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-2 text-center">
            <p className="text-lg font-bold text-emerald-400">{sw.content_words_kept?.length || 0}</p>
            <p className="text-[10px] text-[var(--text-muted)]">Kept</p>
          </div>
        </div>
        <BarRow label={`Reduction: ${sw.reduction_percentage || 0}%`} value={sw.reduction_percentage || 0} max={100} color="bg-red-500" />
        {sw.stop_words_removed?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[var(--text-muted)] mb-1">Removed stop words</p>
            <div className="flex flex-wrap gap-1">
              {(sw.stop_words_removed || []).map((w: string, i: number) => (
                <span key={i} className="text-xs line-through text-red-400 opacity-60">{w}</span>
              ))}
            </div>
          </div>
        )}
        {sw.content_words_kept?.length > 0 && (
          <div className="mt-2">
            <p className="text-[10px] text-[var(--text-muted)] mb-1">Content words kept</p>
            <TagList items={sw.content_words_kept} color="badge-green" />
          </div>
        )}
      </Section>

      {/* Morphological */}
      <Section icon={Layers} title="Morphological Analysis" color="text-blue-400">
        {morph.word_count > 0 && (
          <div className="grid grid-cols-2 gap-2 mb-2">
            <KV label="Word count" value={String(morph.word_count)} mono />
            <KV label="Avg word length" value={`${morph.avg_word_length} chars`} mono />
          </div>
        )}
        {morph.abbreviations_found?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Abbreviations Detected</p>
            <div className="space-y-1">
              {morph.abbreviations_found.map((a: string, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-xs">
                  <span className="text-blue-400 font-mono flex-shrink-0">→</span>
                  <span className="text-[var(--text-secondary)]">{a}</span>
                </div>
              ))}
            </div>
          </div>
        )}
        {morph.technical_morphemes?.length > 0 && morph.technical_morphemes[0] !== "No compound morphemes detected in input" && (
          <div>
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Compound Word Decomposition</p>
            <div className="space-y-1">
              {morph.technical_morphemes.map((m: string, i: number) => (
                <div key={i} className="flex items-start gap-1.5 text-xs">
                  <span className="text-purple-400 font-mono flex-shrink-0">⊕</span>
                  <span className="text-[var(--text-secondary)] font-mono">{m}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </Section>

      {/* Stemming & Lemmatization */}
      {stem.examples?.length > 0 && (
        <Section icon={GitBranch} title="Stemming & Lemmatization" color="text-teal-400">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-[var(--border)]">
                  {['Original','POS','Stemmed','Lemma'].map(h => (
                    <th key={h} className="text-left py-1 pr-3 text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {stem.examples.map((ex: any, i: number) => (
                  <tr key={i} className="border-b border-[var(--border)]/50">
                    <td className="py-1 pr-3 font-mono text-[var(--text-primary)]">{ex.original}</td>
                    <td className="py-1 pr-3">
                      <span className="rounded bg-yellow-500/10 border border-yellow-500/20 text-yellow-400 px-1 text-[10px] font-mono">{ex.pos}</span>
                    </td>
                    <td className="py-1 pr-3 font-mono text-red-400">{ex.stemmed}</td>
                    <td className="py-1 font-mono text-emerald-400">{ex.lemma}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-[var(--text-muted)] mt-1.5">
            <span className="text-red-400">Stemmed</span> = Porter/Snowball suffix stripping (may not be a real word) ·
            <span className="text-emerald-400"> Lemma</span> = dictionary base form
          </p>
        </Section>
      )}

      {/* Syntactic */}
      <Section icon={GitBranch} title="Syntactic Analysis" color="text-purple-400">
        <div className="grid grid-cols-2 gap-2 mb-2">
          <KV label="Sentences" value={String(syntax.sentence_count || 0)} mono />
          <KV label="Complexity" value={syntax.complexity_level || '—'} />
        </div>
        {syntax.noun_phrases?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Noun Phrases (NP)</p>
            <TagList items={syntax.noun_phrases} color="badge-purple" />
          </div>
        )}
        {syntax.main_verb_phrases?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Verb Phrases (VP)</p>
            <TagList items={syntax.main_verb_phrases} color="badge-blue" />
          </div>
        )}
        {syntax.dependency_patterns?.length > 0 && (
          <div>
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Dependency Patterns</p>
            {syntax.dependency_patterns.map((d: string, i: number) => (
              <p key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-purple-400 flex-shrink-0">→</span>{d}
              </p>
            ))}
          </div>
        )}
      </Section>

      {/* Semantic */}
      <Section icon={BookOpen} title="Semantic Analysis" color="text-indigo-400">
        {semantic.named_entities?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Named Entities (NER)</p>
            <div className="flex flex-wrap gap-1.5">
              {semantic.named_entities.map((e: any, i: number) => (
                <span key={i} className="flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs">
                  <span className="text-[var(--text-secondary)]">{e.text}</span>
                  <span className="text-[10px] text-brand-400 font-mono">[{e.type}]</span>
                </span>
              ))}
            </div>
          </div>
        )}
        {semantic.ambiguous_terms?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Lexical Ambiguity (WSD needed)</p>
            {semantic.ambiguous_terms.map((a: any, i: number) => (
              <div key={i} className="text-xs flex items-start gap-2 mb-1">
                <span className="text-yellow-400 font-medium flex-shrink-0">"{a.term}"</span>
                <span className="text-[var(--text-muted)]">→ could mean: {a.possible_meanings.join(' | ')}</span>
              </div>
            ))}
          </div>
        )}
        {semantic.core_concepts?.length > 0 && (
          <div>
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Core Concepts</p>
            <TagList items={semantic.core_concepts} color="badge-blue" />
          </div>
        )}
      </Section>

      {/* Pragmatic */}
      <Section icon={MessageSquare} title="Pragmatic Analysis" color="text-rose-400" defaultOpen={false}>
        <KV label="Speech Act" value={pragmatic.intent_type || '—'} />
        <KV label="Audience" value={pragmatic.target_audience || '—'} />
        {pragmatic.urgency_signals?.length > 0 && (
          <div className="mb-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Urgency / Constraint Signals</p>
            {pragmatic.urgency_signals.map((s: string, i: number) => (
              <p key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-rose-400 flex-shrink-0">!</span>{s}
              </p>
            ))}
          </div>
        )}
        {pragmatic.implicit_assumptions?.length > 0 && (
          <div>
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Implicit Assumptions</p>
            {pragmatic.implicit_assumptions.map((a: string, i: number) => (
              <p key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-[var(--text-muted)] flex-shrink-0">◈</span>{a}
              </p>
            ))}
          </div>
        )}
      </Section>

      {/* Discourse */}
      <Section icon={Hash} title="Discourse Analysis" color="text-cyan-400" defaultOpen={false}>
        <BarRow label="Coherence Score" value={discourse.coherence_score || 0} max={1} color="bg-cyan-500" />
        <KV label="Text Structure" value={discourse.text_structure || '—'} />
        {discourse.connective_words?.length > 0 && (
          <div className="mb-1">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Discourse Connectives Found</p>
            <TagList items={discourse.connective_words} color="badge-blue" />
          </div>
        )}
        {discourse.topic_progression?.length > 0 && (
          <div>
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider mb-1">Topic Progression</p>
            {discourse.topic_progression.map((t: string, i: number) => (
              <div key={i} className="flex items-start gap-2 text-xs mb-1">
                <span className="text-cyan-400 font-mono flex-shrink-0">[{i+1}]</span>
                <span className="text-[var(--text-secondary)] truncate">{t}</span>
              </div>
            ))}
          </div>
        )}
      </Section>

      {/* Research Intent */}
      <Section icon={Zap} title="Research Intent & Gap" color="text-amber-400" defaultOpen={false}>
        {intent.research_gap_hypothesis && (
          <div className="mb-2 rounded-lg bg-amber-500/10 border border-amber-500/20 p-2.5">
            <p className="text-[10px] font-medium text-amber-400 mb-1">Gap Hypothesis</p>
            <p className="text-xs text-[var(--text-secondary)]">{intent.research_gap_hypothesis}</p>
          </div>
        )}
        {intent.expected_contribution && (
          <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 p-2.5">
            <p className="text-[10px] font-medium text-emerald-400 mb-1">Expected Contribution</p>
            <p className="text-xs text-[var(--text-secondary)]">{intent.expected_contribution}</p>
          </div>
        )}
      </Section>

      {/* Search queries */}
      {intent.queries?.length > 0 && (
        <Section icon={SearchIcon} title="Generated Search Queries" color="text-green-400">
          <div className="space-y-1.5">
            {intent.queries.map((q: string, i: number) => (
              <div key={i} className="flex items-start gap-2 rounded bg-[var(--bg-secondary)] border border-[var(--border)] px-2.5 py-1.5">
                <span className="text-[10px] text-brand-400 font-mono mt-0.5 flex-shrink-0">{i+1}.</span>
                <span className="text-xs text-[var(--text-secondary)] font-mono break-all">{q}</span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
function InputPageInner() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken } = useAuthStore();
  const [project, setProject] = useState<any>(null);
  const [intent, setIntent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const [extracting, setExtracting] = useState(false);
  const [intentLog, setIntentLog] = useState<string[]>([]);
  const [retrieving, setRetrieving] = useState(false);
  const [retrieveLog, setRetrieveLog] = useState<string[]>([]);

  const [editing, setEditing] = useState(false);
  const [editText, setEditText] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    projectsAPI.get(id)
      .then((p) => {
        setProject(p);
        setEditText(p.input_text || '');
        if (p.outputs?.intent) setIntent(p.outputs.intent);
        setLoading(false);
      })
      .catch(() => { setError('Project not found'); setLoading(false); });
  }, [id]);

  const handleSaveEdit = async () => {
    if (!editText.trim() || editText === project?.input_text) { setEditing(false); return; }
    setSaving(true);
    try {
      await projectsAPI.updateInput(id, editText.trim());
      setProject((p: any) => ({ ...p, input_text: editText.trim() }));
      setIntent(null);
      setEditing(false);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Save failed');
    } finally { setSaving(false); }
  };

  const handleExtractIntent = useCallback(async () => {
    setExtracting(true); setIntentLog([]); setError('');
    try {
      await fetchStream(
        `${API_URL}/api/pipeline/stream/${id}/intent`,
        (m) => setIntentLog(l => [...l, m]),
        (d) => { if (d?.intent) setIntent(d.intent); },
        () => {}, (m) => setError(m),
      );
    } catch {
      try {
        const result = await pipelineAPI.extractIntent(id);
        setIntent(result.intent);
      } catch (e2: any) {
        setError(e2.response?.data?.detail || 'Intent extraction failed. Check AI Settings.');
      }
    } finally { setExtracting(false); }
  }, [id, accessToken]);

  const handleRetrievePapers = useCallback(async () => {
    setRetrieving(true); setRetrieveLog([]); setError('');
    try {
      await fetchStream(
        `${API_URL}/api/pipeline/stream/${id}/retrieve`,
        (m) => setRetrieveLog(l => [...l, m]),
        () => {}, () => router.push(`/projects/${id}/papers`),
        (m) => setError(m),
      );
    } catch (e: any) { setError(e.message || 'Retrieval failed'); }
    finally { setRetrieving(false); }
  }, [id, accessToken, router]);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  const isStreaming = extracting || retrieving;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-5">
        <h1 className="text-xl font-bold text-[var(--text-primary)] truncate">{project?.title}</h1>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 1 of 7 — NLP Analysis & Paper Retrieval</p>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} className="flex-shrink-0" /> {error}
          <button onClick={() => setError('')} className="ml-auto"><X size={14} /></button>
        </div>
      )}

      <StreamLog
        log={extracting ? intentLog : retrieveLog}
        streaming={isStreaming}
        label={extracting ? 'Running deep NLP analysis...' : 'Fetching papers from 4 sources...'}
      />

      {/* Main layout: input left, NLP breakdown right */}
      <div className="grid grid-cols-1 xl:grid-cols-5 gap-5 mb-5">

        {/* Left: Input (2/5) */}
        <div className="xl:col-span-2 space-y-4">
          <div className="card">
            <div className="flex items-center justify-between gap-2 mb-3">
              <div className="flex items-center gap-2">
                <Brain size={15} className="text-brand-400" />
                <h2 className="font-semibold text-sm text-[var(--text-primary)]">Research Description</h2>
              </div>
              {!editing ? (
                <button onClick={() => setEditing(true)} disabled={isStreaming} className="btn-ghost text-xs py-1 px-2">
                  <Edit2 size={11} /> Edit
                </button>
              ) : (
                <div className="flex gap-1">
                  <button onClick={handleSaveEdit} disabled={saving} className="btn-primary text-xs py-1 px-2">
                    {saving ? <Loader2 size={11} className="animate-spin" /> : <Save size={11} />} Save
                  </button>
                  <button onClick={() => { setEditing(false); setEditText(project?.input_text || ''); }} className="btn-ghost text-xs py-1 px-2">
                    <X size={11} />
                  </button>
                </div>
              )}
            </div>

            {editing ? (
              <textarea
                className="input min-h-[200px] resize-none text-sm leading-relaxed"
                value={editText}
                onChange={e => setEditText(e.target.value)}
                placeholder="Describe your research problem in detail..."
                autoFocus
              />
            ) : (
              <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3 text-sm text-[var(--text-secondary)] leading-relaxed min-h-[180px] whitespace-pre-wrap overflow-auto max-h-[280px]">
                {project?.input_text}
              </div>
            )}

            {!editing && (
              <button onClick={handleExtractIntent} disabled={isStreaming} className="btn-primary mt-3 w-full justify-center">
                {extracting
                  ? <><Loader2 size={13} className="animate-spin" /> Analyzing...</>
                  : <><Brain size={13} /> {intent ? 'Re-analyze NLP' : 'Analyze with AI'}</>}
              </button>
            )}
          </div>

          {/* Keywords */}
          {intent?.keywords?.length > 0 && (
            <div className="card">
              <p className="text-xs font-semibold text-[var(--text-secondary)] mb-2 flex items-center gap-1.5">
                <Tag size={12} className="text-brand-400" /> Extracted Keywords
              </p>
              <div className="flex flex-wrap gap-1.5">
                {intent.keywords.map((k: string) => (
                  <span key={k} className="rounded-md bg-[var(--bg-secondary)] border border-[var(--border)] px-2 py-0.5 text-xs text-[var(--text-secondary)]">
                    {k}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Proceed button */}
          {intent && !retrieving && !editing && (
            <div className="card border-emerald-500/20 bg-emerald-500/5">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <CheckCircle2 size={16} className="text-emerald-400 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-[var(--text-primary)]">Ready to retrieve papers</p>
                    <p className="text-xs text-[var(--text-muted)]">
                      {intent.queries?.length || 0} queries · 4 sources
                    </p>
                  </div>
                </div>
                <button onClick={handleRetrievePapers} disabled={retrieving} className="btn-primary text-sm">
                  <ArrowRight size={13} /> Retrieve
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right: NLP Breakdown (3/5) */}
        <div className="xl:col-span-3">
          {!intent ? (
            <div className="card flex flex-col items-center justify-center min-h-[400px] text-center">
              <Brain size={40} className="text-[var(--text-muted)] mb-4" />
              <p className="text-sm font-medium text-[var(--text-secondary)] mb-1">NLP Breakdown</p>
              <p className="text-xs text-[var(--text-muted)] max-w-xs">
                Click "Analyze with AI" to see deep NLP analysis: tokenization, morphology, syntax, semantics, pragmatics, discourse, stop words, stemming, and lemmatization.
              </p>
              {extracting && (
                <div className="mt-4 flex items-center gap-2 text-brand-400 text-sm">
                  <Loader2 size={16} className="animate-spin" /> Running analysis...
                </div>
              )}
            </div>
          ) : (
            <div className="overflow-auto max-h-[80vh] space-y-0">
              <div className="flex items-center justify-between mb-2">
                <h2 className="font-semibold text-sm text-[var(--text-primary)] flex items-center gap-2">
                  <BarChart2 size={14} className="text-brand-400" /> NLP Breakdown
                </h2>
                <span className="badge-green">Analyzed</span>
              </div>
              <NLPBreakdown intent={intent} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function InputPage() {
  return <ErrorBoundary><InputPageInner /></ErrorBoundary>;
}
