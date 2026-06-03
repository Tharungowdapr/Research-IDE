'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  BookOpen, ExternalLink, Users, Calendar, Star, ArrowRight,
  Loader2, Search, Filter, AlertCircle, FileText, ChevronDown, ChevronUp,
  BookMarked, Share2,
} from 'lucide-react';
import { projectsAPI, agentsAPI, papersAPI } from '@/services/api';
import { showToast } from '@/components/ErrorToast';
import { LiteratureReview } from '@/components/LiteratureReview';
import CitationGraph from '@/components/CitationGraph';

export default function PapersPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  const [papers, setPapers] = useState<any[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [showFullText, setShowFullText] = useState(false);
  const [showLiteratureReview, setShowLiteratureReview] = useState(false);
  const [showCitationGraph, setShowCitationGraph] = useState(false);

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      setPapers(p.outputs?.papers?.papers || []);
      setLoading(false);
    });
  }, [id]);

  const fetchFullText = async (paper: any) => {
    if (paper.full_text) return; // Already have it
    try {
      const data = await papersAPI.getFullText(id, paper.id);
      if (data?.full_text) {
        setPapers(prev => prev.map(p => 
          p.id === paper.id ? { ...p, full_text: data.full_text } : p
        ));
        if (selectedPaper?.id === paper.id) {
          setSelectedPaper({ ...selectedPaper, full_text: data.full_text });
        }
        if (data.source === 'cache') {
          showToast('Full text loaded from cache', 'success');
        }
      } else {
        showToast('Full text not available, using abstract', 'warning');
      }
    } catch (e: any) {
      console.error('Failed to fetch full text:', e);
      showToast('Failed to fetch full text: ' + e.message, 'error');
    }
  };

  const handleAnalyzeGaps = async () => {
    setAnalyzing(true);
    setError('');
    try {
      await agentsAPI.analyzeGaps(id);
      router.push(`/projects/${id}/gaps`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Gap analysis failed.');
      setAnalyzing(false);
    }
  };

  const filtered = papers.filter(
    (p) =>
      !search ||
      p.title?.toLowerCase().includes(search.toLowerCase()) ||
      p.abstract?.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Paper Explorer</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Step 2 of 7 — {papers.length} papers retrieved
          </p>
        </div>
        <button
          onClick={handleAnalyzeGaps}
          disabled={analyzing || papers.length === 0}
          className="btn-primary"
        >
          {analyzing ? <Loader2 size={14} className="animate-spin" /> : <ArrowRight size={14} />}
          {analyzing ? 'Analyzing...' : 'Analyze Gaps'}
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </div>
      )}

      {/* Analysis Tools */}
      {papers.length > 0 && (
        <div className="mb-4 flex items-center gap-2">
          <button
            onClick={() => { setShowLiteratureReview(!showLiteratureReview); setShowCitationGraph(false); }}
            className={`btn-ghost text-xs flex items-center gap-1.5 ${showLiteratureReview ? 'bg-brand-600/20 text-brand-400' : ''}`}
          >
            <BookMarked size={13} /> Literature Review
          </button>
          <button
            onClick={() => { setShowCitationGraph(!showCitationGraph); setShowLiteratureReview(false); }}
            className={`btn-ghost text-xs flex items-center gap-1.5 ${showCitationGraph ? 'bg-brand-600/20 text-brand-400' : ''}`}
          >
            <Share2 size={13} /> Citation Graph
          </button>
        </div>
      )}

      {showLiteratureReview && (
        <div className="mb-5">
          <LiteratureReview projectId={id} />
        </div>
      )}

      {showCitationGraph && (
        <div className="mb-5">
          <CitationGraph projectId={id} />
        </div>
      )}

      {/* 3-Column Layout */}
      <div className="grid grid-cols-12 gap-5">
        {/* Filters */}
        <div className="col-span-2">
          <div className="card sticky top-4">
            <p className="text-xs font-medium text-[var(--text-secondary)] mb-3 flex items-center gap-1">
              <Filter size={11} /> Filters
            </p>
            <div className="space-y-3 text-xs text-[var(--text-muted)]">
              <div>
                <p className="font-medium text-[var(--text-secondary)] mb-1">Source</p>
                <div className="space-y-1">
                  {['arxiv', 'semantic_scholar'].map((src) => {
                    const count = papers.filter((p) => p.source === src).length;
                    return (
                      <div key={src} className="flex justify-between">
                        <span className="capitalize">{src.replace('_', ' ')}</span>
                        <span className="badge-blue">{count}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div>
                <p className="font-medium text-[var(--text-secondary)] mb-1">Total</p>
                <span className="text-brand-400 font-semibold">{papers.length}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Paper List */}
        <div className="col-span-5 space-y-2">
          <div className="relative mb-3">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              className="input pl-8 text-xs"
              placeholder="Search papers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>

                {filtered.length === 0 ? (
              <div className="card text-center py-10">
                <BookOpen size={28} className="mx-auto mb-2 text-[var(--text-muted)]" />
                <p className="text-sm text-[var(--text-secondary)]">No papers found</p>
              </div>
            ) : (
              filtered.map((paper) => (
                <button
                  key={paper.id}
                  onClick={() => {
                    setSelectedPaper(paper);
                    fetchFullText(paper);
                  }}
                  className={`w-full text-left card hover:border-brand-500/30 transition-all ${
                    selectedPaper?.id === paper.id ? 'border-brand-500/50 bg-brand-600/5' : ''
                  }`}
                >
                  <p className="text-sm font-medium text-[var(--text-primary)] leading-snug mb-2">
                    {paper.title}
                  </p>
                  <div className="flex items-center gap-3 text-xs text-[var(--text-muted)]">
                    <span className="flex items-center gap-1">
                      <Calendar size={10} /> {paper.year || 'N/A'}
                    </span>
                    <span className="flex items-center gap-1">
                      <Star size={10} /> {paper.citations}
                    </span>
                    <span className={paper.source === 'arxiv' ? 'badge-blue' : 'badge-purple'}>
                      {paper.source}
                    </span>
                    {paper.full_text && (
                      <span className="badge-green text-[10px]">Full Text</span>
                    )}
                  </div>
                </button>
              ))
            )}
        </div>

        {/* Paper Detail */}
        <div className="col-span-5">
          <div className="card sticky top-4">
            {!selectedPaper ? (
              <div className="flex flex-col items-center justify-center min-h-[300px] text-center">
                <BookOpen size={28} className="text-[var(--text-muted)] mb-2" />
                <p className="text-sm text-[var(--text-secondary)]">Select a paper to view details</p>
              </div>
            ) : (
              <div className="space-y-4">
                <h3 className="font-semibold text-sm text-[var(--text-primary)] leading-snug">
                  {selectedPaper.title}
                </h3>

                <div className="flex flex-wrap gap-2 text-xs text-[var(--text-muted)]">
                  <span className="flex items-center gap-1"><Calendar size={10} /> {selectedPaper.year}</span>
                  <span className="flex items-center gap-1"><Star size={10} /> {selectedPaper.citations} citations</span>
                  <span className={selectedPaper.source === 'arxiv' ? 'badge-blue' : 'badge-purple'}>
                    {selectedPaper.source}
                  </span>
                </div>

                {selectedPaper.authors?.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-[var(--text-muted)] mb-1 flex items-center gap-1">
                      <Users size={10} /> Authors
                    </p>
                    <p className="text-xs text-[var(--text-secondary)]">{selectedPaper.authors.join(', ')}</p>
                  </div>
                )}

                <div>
                  <p className="text-xs font-medium text-[var(--text-muted)] mb-1">Abstract</p>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{selectedPaper.abstract}</p>
                </div>

                {/* Full Text Section */}
                <div>
                  <button
                    onClick={() => setShowFullText(!showFullText)}
                    className="flex items-center gap-1 text-xs font-medium text-[var(--text-muted)] mb-1 hover:text-[var(--text-primary)] transition-colors"
                  >
                    <FileText size={10} />
                    Full Text {showFullText ? <ChevronUp size={10} /> : <ChevronDown size={10} />}
                    {selectedPaper.full_text ? (
                      <span className="badge-green text-[10px]">Available</span>
                    ) : (
                      <span className="badge-yellow text-[10px]">Not fetched</span>
                    )}
                  </button>
                  {showFullText && (
                    <div className="max-h-[400px] overflow-y-auto p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
                      <pre className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed">
                        {selectedPaper.full_text || selectedPaper.abstract}
                      </pre>
                    </div>
                  )}
                </div>

                <div className="flex gap-2">
                  {selectedPaper.url && (
                    <a
                      href={selectedPaper.url}
                      target="_blank"
                      className="btn-secondary text-xs"
                    >
                      <ExternalLink size={12} /> View Paper
                    </a>
                  )}
                  {selectedPaper.full_text && (
                    <button
                      onClick={() => {
                        navigator.clipboard.writeText(selectedPaper.full_text);
                        alert('Full text copied to clipboard!');
                      }}
                      className="btn-secondary text-xs"
                    >
                      <FileText size={12} /> Copy Full Text
                    </button>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
