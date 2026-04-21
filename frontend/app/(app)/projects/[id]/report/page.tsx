'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { FileText, Download, Loader2, BookOpen, Tag } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(0);

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.report) setReport(p.outputs.report);
      else {
        agentsAPI.generateReport(id).then((r) => setReport(r.report)).catch(console.error);
      }
      setLoading(false);
    });
  }, [id]);

  const handleDownload = () => {
    if (!report) return;
    const content = [
      `# ${report.title}\n\n`,
      `**Keywords:** ${(report.keywords || []).join(', ')}\n\n`,
      `## Abstract\n\n${report.abstract}\n\n`,
      ...(report.sections || []).map((s: any) => `## ${s.heading}\n\n${s.content}\n\n`),
      `## References\n\n${(report.references || []).map((r: string, i: number) => `[${i + 1}] ${r}`).join('\n')}`,
    ].join('');

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'research_paper.md';
    a.click();
    URL.revokeObjectURL(url);
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

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Paper</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 7 of 7 — Complete</p>
        </div>
        <button onClick={handleDownload} className="btn-primary">
          <Download size={14} /> Download Markdown
        </button>
      </div>

      <div className="grid grid-cols-12 gap-5">
        {/* TOC */}
        <div className="col-span-3">
          <div className="card sticky top-4">
            <p className="text-xs font-medium text-[var(--text-muted)] mb-3 flex items-center gap-1">
              <BookOpen size={11} /> Contents
            </p>
            <nav className="space-y-1">
              {['Abstract', ...sections.map((s: any) => s.heading)].map((heading, i) => (
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
              {report.references?.length > 0 && (
                <button
                  onClick={() => setActiveSection(sections.length + 1)}
                  className={`w-full text-left text-xs px-2 py-1.5 rounded-md text-[var(--text-muted)] hover:text-[var(--text-secondary)]`}
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
            <div className="border-b border-[var(--border)] pb-5">
              <h2 className="text-xl font-bold text-[var(--text-primary)] leading-snug mb-3">
                {report.title}
              </h2>
              {report.keywords?.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {report.keywords.map((kw: string) => (
                    <span key={kw} className="badge-blue flex items-center gap-1">
                      <Tag size={9} /> {kw}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* Abstract */}
            <div>
              <h3 className="text-sm font-bold text-[var(--text-primary)] mb-2">Abstract</h3>
              <p className="text-sm text-[var(--text-secondary)] leading-relaxed italic">
                {report.abstract}
              </p>
            </div>

            {/* Sections */}
            {sections.map((section: any, i: number) => (
              <div key={i} className="border-t border-[var(--border)] pt-5">
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">{section.heading}</h3>
                <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                  {section.content}
                </div>
              </div>
            ))}

            {/* References */}
            {report.references?.length > 0 && (
              <div className="border-t border-[var(--border)] pt-5">
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3">References</h3>
                <ol className="space-y-2">
                  {report.references.map((ref: string, i: number) => (
                    <li key={i} className="text-xs text-[var(--text-muted)] flex gap-2">
                      <span className="text-[var(--text-secondary)] font-medium flex-shrink-0">[{i + 1}]</span>
                      <span>{ref}</span>
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
