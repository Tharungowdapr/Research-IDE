'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { FileText, Download, Loader2, BookOpen, Tag, ExternalLink } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(0);
  const [downloading, setDownloading] = useState<'docx' | 'pdf' | 'md' | null>(null);

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.report) setReport(p.outputs.report);
      else {
        agentsAPI.generateReport(id).then((r) => setReport(r.report)).catch(console.error);
      }
      setLoading(false);
    });
  }, [id]);

  const handleDownload = async (format: 'docx' | 'pdf' | 'md') => {
    if (!report) return;

    if (format === 'md') {
      const content = [
        `# ${report.title}\n\n`,
        `**Keywords:** ${(report.keywords || []).join(', ')}\n\n`,
        `## Abstract\n\n${report.abstract}\n\n`,
        ...(report.sections || []).map((s: any) => `## ${s.heading}\n\n${s.content}\n\n`),
        `## References\n\n${(report.references || []).map((r: any, i: number) => {
          if (typeof r === 'object') return `[${r.id || i + 1}] ${r.authors}, "${r.title}," ${r.venue}, ${r.year}.`;
          return `[${i + 1}] ${r}`;
        }).join('\n')}`,
      ].join('');
      const blob = new Blob([content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'research_paper.md';
      a.click();
      URL.revokeObjectURL(url);
      return;
    }

    setDownloading(format);
    try {
      const accessToken = useAuthStore.getState().accessToken;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${apiUrl}/api/agents/${id}/download/${format}`;
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!response.ok) throw new Error(`Download failed: ${response.status}`);
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = objectUrl;
      link.download = `research_paper.${format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(objectUrl);
    } catch (e) {
      console.error(e);
    } finally {
      setDownloading(null);
    }
  };

  const renderCitationContent = (content: string) => {
    if (!content) return null;
    const parts = content.split(/(\[\d+\])/);
    return parts.map((part, i) =>
      /^\[\d+\]$/.test(part)
        ? <sup key={i} className="text-brand-400 text-xs cursor-pointer hover:underline">{part}</sup>
        : <span key={i}>{part}</span>
    );
  };

  if (loading || !report) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Generating research paper...</p>
      </div>
    );
  }

  const sections = report.sections || [];
  const references = report.references || [];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Paper</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 7 of 7 — Complete</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            disabled={downloading === 'docx'}
            onClick={() => handleDownload('docx')}
            className="btn-secondary"
          >
            {downloading === 'docx' ? <Loader2 className="animate-spin" size={14} /> : <FileText size={14} />}
            {downloading === 'docx' ? 'Generating...' : 'Download DOCX'}
          </button>
          <button
            disabled={downloading === 'pdf'}
            onClick={() => handleDownload('pdf')}
            className="btn-secondary"
          >
            {downloading === 'pdf' ? <Loader2 className="animate-spin" size={14} /> : <Download size={14} />}
            {downloading === 'pdf' ? 'Generating...' : 'Download PDF'}
          </button>
          <button onClick={() => handleDownload('md')} className="btn-ghost text-xs">
            Markdown
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* TOC */}
        <div className="col-span-3">
          <div className="card sticky top-4">
            <p className="text-xs font-medium text-[var(--text-muted)] mb-3 flex items-center gap-1">
              <BookOpen size={11} /> Contents
            </p>
            <nav className="space-y-1">
              {['Abstract', ...sections.map((s: any) => s.heading)].map((heading: string, i: number) => (
                <button
                  key={i}
                  onClick={() => setActiveSection(i)}
                  className={`w-full text-left text-xs px-2 py-1.5 rounded-md transition-all ${
                    activeSection === i
                      ? 'bg-brand-600/20 text-brand-400'
                      : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                  }`}
                >
                  {heading}
                </button>
              ))}
              {references.length > 0 && (
                <button
                  onClick={() => setActiveSection(sections.length + 1)}
                  className="w-full text-left text-xs px-2 py-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-secondary)]"
                >
                  References
                </button>
              )}
            </nav>
          </div>
        </div>

        {/* Paper Content */}
        <div className="col-span-9">
          <div className="card space-y-6">
            {/* Title */}
            <div className="border-b border-[var(--border)] pb-5 text-center">
              <h2 className="text-xl font-bold text-[var(--text-primary)] leading-snug mb-2">
                {report.title}
              </h2>
              {report.authors?.length > 0 && (
                <p className="text-sm italic text-[var(--text-secondary)] mb-3">
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
            <div className="rounded-lg border-l-4 border-brand-500 bg-[var(--bg-secondary)] p-4">
              <span className="italic text-[var(--text-muted)] text-sm">Abstract — </span>
              <span className="text-sm text-[var(--text-secondary)] leading-relaxed">{report.abstract}</span>
            </div>

            {/* Index Terms */}
            {report.keywords?.length > 0 && (
              <p className="text-sm">
                <span className="italic text-[var(--text-muted)]">Index Terms — </span>
                <span className="text-[var(--text-secondary)]">{report.keywords.join(', ')}</span>
              </p>
            )}

            {/* Sections */}
            {sections.map((section: any, i: number) => (
              <div key={i} className="border-t border-[var(--border)] pt-5">
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center uppercase tracking-wide">
                  {section.heading}
                </h3>
                <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                  {renderCitationContent(section.content)}
                </div>
              </div>
            ))}

            {/* Acknowledgements */}
            {report.acknowledgements && (
              <div className="border-t border-[var(--border)] pt-5">
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center uppercase tracking-wide">
                  Acknowledgements
                </h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{report.acknowledgements}</p>
              </div>
            )}

            {/* References */}
            {references.length > 0 && (
              <div className="border-t border-[var(--border)] pt-5">
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center uppercase tracking-wide">
                  References
                </h3>
                <ol className="space-y-2">
                  {references.map((ref: any, i: number) => (
                    <li key={i} className="text-xs text-[var(--text-muted)] flex gap-2">
                      <span className="text-[var(--text-secondary)] font-medium flex-shrink-0">
                        [{typeof ref === 'object' ? ref.id || i + 1 : i + 1}]
                      </span>
                      <span>
                        {typeof ref === 'object'
                          ? `${ref.authors}, "${ref.title}," ${ref.venue}, ${ref.year}.`
                          : ref}
                      </span>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
