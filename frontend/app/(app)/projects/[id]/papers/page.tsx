'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  BookOpen, ExternalLink, Users, Calendar, Star, ArrowRight,
  Loader2, Search, AlertCircle, FileText, ChevronDown, ChevronUp,
  BookMarked, Share2, Filter,
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
  const [expandedPaperId, setExpandedPaperId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [search, setSearch] = useState('');
  const [error, setError] = useState('');
  const [showFullText, setShowFullText] = useState(false);
  const [showLiteratureReview, setShowLiteratureReview] = useState(false);
  const [showCitationGraph, setShowCitationGraph] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        setPapers(p.outputs?.papers?.papers || []);
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const fetchFullText = async (paper: any) => {
    if (paper.full_text) return;
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

  const handlePaperClick = (paper: any) => {
    if (expandedPaperId === paper.id) {
      setExpandedPaperId(null);
      setSelectedPaper(null);
      setShowFullText(false);
    } else {
      setExpandedPaperId(paper.id);
      setSelectedPaper(paper);
      setShowFullText(false);
      fetchFullText(paper);
    }
  };

  const filtered = papers.filter(
    (p) =>
      !search ||
      p.title?.toLowerCase().includes(search.toLowerCase()) ||
      p.abstract?.toLowerCase().includes(search.toLowerCase())
  );

  const arxivCount = papers.filter(p => p.source === 'arxiv').length;
  const ssCount = papers.filter(p => p.source === 'semantic_scholar').length;

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="min-h-screen bg-background text-foreground p-8 max-w-6xl mx-auto">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Paper Explorer</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">
            Step 2 of 13 — {papers.length} papers retrieved
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
          <AlertCircle size={14} /> {String(error)}
        </div>
      )}

      {/* Analysis Tools */}
      {papers.length > 0 && (
        <div className="mb-3 flex items-center gap-2">
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
        <div className="mb-4">
          <LiteratureReview projectId={id} />
        </div>
      )}

      {showCitationGraph && (
        <div className="mb-4">
          <CitationGraph projectId={id} />
        </div>
      )}

      {/* Filter Bar */}
      <div className="card mb-4 flex items-center gap-4 py-3 px-4">
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-muted)]">
          <Filter size={12} />
          <span className="font-medium text-[var(--text-secondary)]">Filters</span>
        </div>
        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="badge-blue">arXiv</span>
            <span className="text-[var(--text-secondary)] font-medium">{arxivCount}</span>
          </span>
          <span className="flex items-center gap-1.5">
            <span className="badge-purple">Semantic Scholar</span>
            <span className="text-[var(--text-secondary)] font-medium">{ssCount}</span>
          </span>
          <span className="w-px h-4 bg-[var(--border)]" />
          <span className="text-[var(--text-muted)]">Total</span>
          <span className="text-brand-400 font-semibold">{papers.length}</span>
        </div>
        <div className="flex-1" />
        <div className="relative w-56">
          <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
          <input
            type="text"
            className="input pl-8 text-xs py-1.5"
            placeholder="Search papers..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
      </div>

      {/* Paper List */}
      {filtered.length === 0 ? (
        <div className="card text-center py-16">
          <BookOpen size={32} className="mx-auto mb-2 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No papers found</p>
        </div>
      ) : (
        <div className="space-y-2">
          {filtered.map((paper) => {
            const isExpanded = expandedPaperId === paper.id;
            return (
              <div key={paper.id}
                className={`card transition-all cursor-pointer ${
                  isExpanded ? 'border-brand-500/50 bg-brand-600/5' : 'hover:border-brand-500/30'
                }`}
                onClick={() => handlePaperClick(paper)}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
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
                      {/* Full-text status badge */}
                      {(() => {
                        const status = paper.full_text_status || (paper.full_text ? 'full' : 'abstract');
                        const badgeCls = status === 'full' || status === 'cached'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                          : status === 'abstract'
                            ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400';
                        return (
                          <span className={`px-2 py-0.5 rounded text-[10px] font-medium ${badgeCls}`}>
                            {status === 'full' || status === 'cached' ? 'Full Text' : status === 'abstract' ? 'Abstract Only' : 'Not Found'}
                          </span>
                        );
                      })()}
                    </div>
                  </div>
                  <ChevronDown
                    size={14}
                    className={`text-[var(--text-muted)] flex-shrink-0 mt-1 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
                  />
                </div>

                {/* Expanded Detail */}
                {isExpanded && selectedPaper && (
                  <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-4" onClick={(e) => e.stopPropagation()}>
                    {selectedPaper.authors?.length > 0 && (
                      <div className="flex items-start gap-2 text-xs">
                        <Users size={12} className="text-[var(--text-muted)] mt-0.5 flex-shrink-0" />
                        <span className="text-[var(--text-secondary)]">{selectedPaper.authors.join(', ')}</span>
                      </div>
                    )}

                    <div>
                      <p className="text-xs font-medium text-[var(--text-muted)] mb-1">Abstract</p>
                      <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{selectedPaper.abstract}</p>
                    </div>

                    {/* Full Text Toggle */}
                    <div>
                      <button
                        onClick={() => setShowFullText(!showFullText)}
                        className="flex items-center gap-1 text-xs font-medium text-[var(--text-muted)] hover:text-[var(--text-primary)] transition-colors"
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
                        <div className="mt-2 max-h-[400px] overflow-y-auto p-3 bg-[var(--bg-secondary)] rounded-lg border border-[var(--border)]">
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
                          onClick={(e) => e.stopPropagation()}
                        >
                          <ExternalLink size={12} /> View Paper
                        </a>
                      )}
                      {selectedPaper.full_text && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            navigator.clipboard.writeText(selectedPaper.full_text);
                            showToast('Full text copied to clipboard!', 'success');
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
            );
          })}
        </div>
      )}
    </div>
  );
}