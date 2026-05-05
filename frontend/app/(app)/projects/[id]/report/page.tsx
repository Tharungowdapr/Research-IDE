'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams } from 'next/navigation';
import { FileText, Download, Loader2, BookOpen, Tag, AlertCircle, Package } from 'lucide-react';
import { projectsAPI, agentsAPI, downloadAPI, getAuthToken } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const triggered = useRef(false);
  const [streamLog, setStreamLog] = useState<string[]>([]);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.report) {
        setReport(p.outputs.report);
        setLoading(false);
      } else {
        setLoading(false);
        handleGenerate();
      }
    }).catch(() => setLoading(false));
  }, [id]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    setStreamLog([]);
    try {
      const freshToken = getAuthToken();
      const response = await fetch(`${API_URL}/api/agents/stream/${id}/report`, {
        headers: { Authorization: `Bearer ${freshToken}` },
      });
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error('No stream');
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        for (const line of text.split('\n')) {
          if (!line.startsWith('data:')) continue;
          try {
            const evt = JSON.parse(line.slice(5).trim());
            if (evt.type === 'progress') setStreamLog(l => [...l, evt.message]);
            if (evt.type === 'result' && evt.data?.report) setReport(evt.data.report);
            if (evt.type === 'error') setError(evt.message);
          } catch {}
        }
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = async (format: 'docx' | 'pdf' | 'md') => {
    if (format === 'md') {
      if (!report) return;
      const content = [
        `# ${report.title}\n\n`,
        `**Keywords:** ${(report.keywords || []).join(', ')}\n\n`,
        `## Abstract\n\n${report.abstract}\n\n`,
        ...(report.sections || []).map((s: any) => `## ${s.heading}\n\n${s.content}\n\n`),
        `## References\n\n${(report.references || []).map((r: any) => `[${r.id}] ${r.authors} (${r.year}). "${r.title}." ${r.venue}.`).join('\n')}`,
      ].join('');
      const blob = new Blob([content], { type: 'text/markdown' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = 'research_paper.md';
      link.click();
      URL.revokeObjectURL(link.href);
      return;
    }
    setDownloading(format);
    try {
      const url = `${API_URL}/api/agents/${id}/download/${format}`;
      // Always get the freshest token at call time, not at render time
      const freshToken = getAuthToken();
      const response = await fetch(url, { headers: { Authorization: `Bearer ${freshToken}` } });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Download failed: ${response.status}`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = `research_paper.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(objectUrl);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setDownloading(null);
    }
  };

  const handleExportProject = async () => {
    setDownloading('zip');
    try {
      const url = downloadAPI.fullProject(id);
      const freshToken = getAuthToken();
      const response = await fetch(url, { headers: { Authorization: `Bearer ${freshToken}` } });
      if (!response.ok) {
        const err = await response.json().catch(() => ({}));
        throw new Error(err.detail || `Export failed: ${response.status}`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = `project_export.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(objectUrl);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setDownloading(null);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Paper</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 7 of 7 — IEEE Format</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <button onClick={handleGenerate} disabled={generating} className="btn-ghost text-xs">
            {generating ? <Loader2 size={13} className="animate-spin" /> : null}
            Regenerate
          </button>
          <button onClick={handleExportProject} disabled={!!downloading} className="btn-secondary text-sm">
            <Package size={14} /> Export Project (ZIP)
          </button>
          <button onClick={() => handleDownload('md')} disabled={!!downloading} className="btn-ghost text-xs">
            <FileText size={13} /> Markdown
          </button>
          <button onClick={() => handleDownload('docx')} disabled={!!downloading} className="btn-secondary text-sm">
            {downloading === 'docx' ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            {downloading === 'docx' ? 'Generating...' : 'Download DOCX'}
          </button>
          <button onClick={() => handleDownload('pdf')} disabled={!!downloading} className="btn-primary text-sm">
            {downloading === 'pdf' ? <Loader2 size={14} className="animate-spin" /> : <Download size={14} />}
            {downloading === 'pdf' ? 'Generating...' : 'Download PDF'}
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex gap-2">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" /> {error}
        </div>
      )}

      {/* Stream log */}
      {(generating || streamLog.length > 0) && (
        <div className="mb-5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-4 font-mono text-xs space-y-1 max-h-40 overflow-auto">
          {streamLog.map((msg, i) => (
            <div key={i} className="flex items-center gap-2 text-[var(--text-secondary)]">
              <span className="text-brand-400">▸</span> {msg}
            </div>
          ))}
          {generating && (
            <div className="flex items-center gap-2 text-brand-400">
              <Loader2 size={10} className="animate-spin" /> Processing...
            </div>
          )}
        </div>
      )}

      {!report ? (
        <div className="card text-center py-16">
          <FileText size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">Generating your research paper...</p>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-5">
          {/* TOC */}
          <div className="col-span-3">
            <div className="card sticky top-4">
              <p className="text-xs font-medium text-[var(--text-muted)] mb-3 flex items-center gap-1">
                <BookOpen size={11} /> Contents
              </p>
              <nav className="space-y-1">
                {['Abstract', ...(report.sections || []).map((s: any) => s.heading)].map((heading: string, i: number) => (
                  <a key={i} href={`#section-${i}`}
                    className="block text-xs px-2 py-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-all truncate">
                    {heading}
                  </a>
                ))}
                {(report.references || []).length > 0 && (
                  <a href="#references" className="block text-xs px-2 py-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-secondary)]">
                    References
                  </a>
                )}
              </nav>
            </div>
          </div>

          {/* Paper content */}
          <div className="col-span-9">
            <div className="card space-y-6">
              {/* Title */}
              <div className="border-b border-[var(--border)] pb-5">
                <h2 className="text-xl font-bold text-[var(--text-primary)] leading-snug mb-3 text-center">
                  {report.title}
                </h2>
                {report.authors?.length > 0 && (
                  <p className="text-sm italic text-[var(--text-muted)] text-center mb-3">
                    {report.authors.join(', ')}
                  </p>
                )}
                {report.keywords?.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 justify-center">
                    {report.keywords.map((kw: string) => (
                      <span key={kw} className="badge-blue flex items-center gap-1">
                        <Tag size={9} /> {kw}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Abstract */}
              <div id="section-0">
                <div className="rounded-lg border-l-4 border-brand-500 bg-[var(--bg-secondary)] p-4">
                  <span className="italic text-[var(--text-muted)] text-sm">Abstract — </span>
                  <span className="text-sm text-[var(--text-secondary)] leading-relaxed">{report.abstract}</span>
                </div>
                {report.keywords?.length > 0 && (
                  <p className="text-xs mt-2 text-[var(--text-muted)]">
                    <span className="italic">Index Terms — </span>
                    {report.keywords.join(', ')}
                  </p>
                )}
              </div>

              {/* Sections */}
              {(report.sections || []).map((section: any, i: number) => (
                <div key={i} id={`section-${i + 1}`} className="border-t border-[var(--border)] pt-5">
                  <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center tracking-wide">
                    {section.heading}
                  </h3>
                  <div className="space-y-3">
                    {(section.content || '').split('\n\n').filter(Boolean).map((para: string, j: number) => (
                      <p key={j} className="text-sm text-[var(--text-secondary)] leading-relaxed text-justify">
                        {para.split(/(\[\d+\])/).map((part: string, k: number) =>
                          /^\[\d+\]$/.test(part) ? (
                            <sup key={k} className="text-brand-400 text-xs cursor-pointer hover:underline">{part}</sup>
                          ) : (
                            <span key={k}>{part}</span>
                          )
                        )}
                      </p>
                    ))}
                  </div>
                </div>
              ))}

              {/* References */}
              {(report.references || []).length > 0 && (
                <div id="references" className="border-t border-[var(--border)] pt-5">
                  <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center tracking-wide">REFERENCES</h3>
                  <ol className="space-y-2">
                    {report.references.map((ref: any) => (
                      <li key={ref.id} className="text-xs text-[var(--text-muted)] flex gap-2">
                        <span className="text-[var(--text-secondary)] font-medium flex-shrink-0 font-mono">[{ref.id}]</span>
                        <span>
                          {ref.authors} ({ref.year}). &ldquo;{ref.title}.&rdquo; {ref.venue}.
                          {ref.url && <a href={ref.url} target="_blank" className="ml-1 text-brand-400 hover:underline">↗</a>}
                        </span>
                      </li>
                    ))}
                  </ol>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
