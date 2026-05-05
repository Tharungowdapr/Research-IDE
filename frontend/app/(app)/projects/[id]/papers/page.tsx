'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  BookOpen, ExternalLink, Users, Calendar, Star, ArrowRight, Loader2,
  Search, Filter, AlertCircle, Github, BarChart2, Plus, X, Save,
} from 'lucide-react';
import { projectsAPI, pipelineAPI, getAuthToken } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { StreamLog } from '@/components/ui/StreamLog';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

function AddPaperModal({ onAdd, onClose }: { onAdd: (p: any) => void; onClose: () => void }) {
  const [form, setForm] = useState({ title: '', abstract: '', authors: '', year: '', url: '' });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title.trim()) { setError('Title is required'); return; }
    setSaving(true);
    try {
      // Will be called with projectId from parent
      onAdd({ ...form, authors: form.authors.split(',').map(a => a.trim()).filter(Boolean) });
    } catch (e: any) { setError(e.message); setSaving(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="card w-full max-w-lg">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-[var(--text-primary)]">Add Paper Manually</h2>
          <button onClick={onClose} className="btn-ghost p-1"><X size={16} /></button>
        </div>
        {error && <div className="mb-3 text-sm text-red-400 rounded-lg bg-red-500/10 px-3 py-2">{error}</div>}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Title *</label>
            <input className="input" value={form.title} onChange={e => setForm({...form, title: e.target.value})} placeholder="Paper title" autoFocus />
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Abstract</label>
            <textarea className="input min-h-[80px] resize-none" value={form.abstract} onChange={e => setForm({...form, abstract: e.target.value})} placeholder="Paper abstract..." />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Authors (comma-separated)</label>
              <input className="input" value={form.authors} onChange={e => setForm({...form, authors: e.target.value})} placeholder="A. Smith, B. Jones" />
            </div>
            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">Year</label>
              <input className="input" value={form.year} onChange={e => setForm({...form, year: e.target.value})} placeholder="2024" />
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1">URL (DOI, arXiv, etc.)</label>
            <input className="input" value={form.url} onChange={e => setForm({...form, url: e.target.value})} placeholder="https://arxiv.org/abs/..." />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
            <button type="submit" disabled={saving} className="btn-primary">
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />} Add Paper
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function PapersPageInner() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { accessToken } = useAuthStore();
  const [papers, setPapers] = useState<any[]>([]);
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [gapLog, setGapLog] = useState<string[]>([]);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      setPapers(p.outputs?.papers?.papers || []);
      setLoading(false);
    });
  }, [id]);

  const handleAnalyzeGaps = async () => {
    setAnalyzing(true); setGapLog([]); setError('');
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
            if (evt.type === 'progress') setGapLog(l => [...l, evt.message]);
            if (evt.type === 'done') { router.push(`/projects/${id}/gaps`); return; }
            if (evt.type === 'error') setError(evt.message);
          } catch {}
        }
      }
    } catch (e: any) { setError(e.message); }
    finally { setAnalyzing(false); }
  };

  const handleAddPaper = async (paperData: any) => {
    try {
      const result = await pipelineAPI.addPaperManually(id, paperData);
      setPapers(prev => [...prev, result.paper]);
      setShowAddModal(false);
    } catch (e: any) { throw e; }
  };

  const filtered = papers.filter(p =>
    !search ||
    p.title?.toLowerCase().includes(search.toLowerCase()) ||
    p.abstract?.toLowerCase().includes(search.toLowerCase()) ||
    p.authors?.some((a: string) => a.toLowerCase().includes(search.toLowerCase()))
  );

  const sources = ['arxiv', 'semantic_scholar', 'openalex', 'paperswithcode', 'manual'];

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {showAddModal && <AddPaperModal onAdd={handleAddPaper} onClose={() => setShowAddModal(false)} />}

      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Paper Explorer</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 2 of 7 — {papers.length} papers</p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowAddModal(true)} className="btn-secondary text-sm"><Plus size={14} /> Add Paper</button>
          <button onClick={handleAnalyzeGaps} disabled={analyzing || papers.length === 0} className="btn-primary">
            {analyzing ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
            {analyzing ? 'Analyzing...' : 'Analyze Gaps'}
          </button>
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2"><AlertCircle size={14} />{error}</div>}
      <StreamLog log={gapLog} streaming={analyzing} label="Running 3-pass gap analysis..." />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Filters */}
        <div className="lg:col-span-2 hidden lg:block">
          <div className="card sticky top-4">
            <p className="text-xs font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-1"><Filter size={11} /> Sources</p>
            <div className="space-y-2 text-xs text-[var(--text-muted)]">
              {sources.map(src => {
                const count = papers.filter(p => p.source === src).length;
                if (count === 0) return null;
                return (
                  <div key={src} className="flex justify-between">
                    <span className="capitalize">{src.replace('_', ' ')}</span>
                    <span className="badge-blue">{count}</span>
                  </div>
                );
              })}
              <div className="border-t border-[var(--border)] pt-2 flex justify-between font-medium">
                <span>Total</span><span className="text-brand-400">{papers.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Paper list */}
        <div className="lg:col-span-5 space-y-2">
          <div className="relative mb-3">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input type="text" className="input pl-8 text-xs" placeholder="Search by title, abstract, or author..."
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          {filtered.length === 0 ? (
            <div className="card text-center py-10">
              <BookOpen size={28} className="mx-auto mb-2 text-[var(--text-muted)]" />
              <p className="text-sm text-[var(--text-secondary)]">No papers found</p>
              <button onClick={() => setShowAddModal(true)} className="btn-secondary text-xs mt-3"><Plus size={12} /> Add one manually</button>
            </div>
          ) : (
            filtered.map(paper => (
              <button key={paper.id} onClick={() => setSelected(paper)}
                className={`w-full text-left card hover:border-brand-500/30 transition-all ${selected?.id === paper.id ? 'border-brand-500/50 bg-brand-600/5' : ''}`}>
                <p className="text-sm font-medium text-[var(--text-primary)] leading-snug line-clamp-2 mb-2">{paper.title}</p>
                <div className="flex items-center gap-2 text-xs text-[var(--text-muted)] flex-wrap">
                  <span className="flex items-center gap-1"><Calendar size={10} />{paper.year || 'N/A'}</span>
                  <span className="flex items-center gap-1"><Star size={10} />{paper.citations}</span>
                  {paper.score > 0 && <span className="flex items-center gap-1 text-brand-400"><BarChart2 size={10} />{paper.score.toFixed(2)}</span>}
                  {paper.github_url && <span className="text-emerald-400 text-[10px]">has code</span>}
                  <span className={paper.source === 'manual' ? 'badge-yellow' : paper.source === 'arxiv' ? 'badge-blue' : 'badge-purple'}>
                    {paper.source?.replace('_', ' ')}
                  </span>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Detail */}
        <div className="lg:col-span-5 hidden lg:block">
          <div className="card sticky top-4">
            {!selected ? (
              <div className="flex flex-col items-center justify-center min-h-[300px] text-center">
                <BookOpen size={28} className="text-[var(--text-muted)] mb-2" />
                <p className="text-sm text-[var(--text-secondary)]">Select a paper to view details</p>
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[var(--text-primary)] leading-snug">{selected.title}</h3>
                <div className="flex flex-wrap gap-2 text-xs text-[var(--text-muted)]">
                  <span className="flex items-center gap-1"><Calendar size={10} />{selected.year}</span>
                  <span className="flex items-center gap-1"><Star size={10} />{selected.citations} citations</span>
                  {selected.score > 0 && <span className="flex items-center gap-1 text-brand-400"><BarChart2 size={10} />Relevance: {selected.score.toFixed(2)}</span>}
                </div>
                {selected.authors?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-[var(--text-muted)] mb-1 flex items-center gap-1"><Users size={10} /> Authors</p>
                    <p className="text-xs text-[var(--text-secondary)]">{Array.isArray(selected.authors) ? selected.authors.join(', ') : selected.authors}</p>
                  </div>
                )}
                <div>
                  <p className="text-xs font-medium text-[var(--text-muted)] mb-1">Abstract</p>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{selected.abstract || 'No abstract available.'}</p>
                </div>
                <div className="flex gap-2 flex-wrap">
                  {selected.url && <a href={selected.url} target="_blank" rel="noopener" className="btn-secondary text-xs"><ExternalLink size={12} /> View Paper</a>}
                  {selected.github_url && <a href={selected.github_url} target="_blank" rel="noopener" className="btn-secondary text-xs text-emerald-400"><Github size={12} /> Code</a>}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PapersPage() {
  return <ErrorBoundary><PapersPageInner /></ErrorBoundary>;
}
