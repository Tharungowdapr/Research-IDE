'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { FileText, Download, Loader2, BookOpen, Tag, ChevronDown, AlertCircle, ArrowRight, Save, CheckCircle2, Pencil, X, Plus, Trash2 } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';

export default function ReportPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [report, setReport] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [activeSection, setActiveSection] = useState(0);
  const [showToc, setShowToc] = useState(false);
  const [downloading, setDownloading] = useState<'docx' | 'pdf' | 'md' | null>(null);
  const [editing, setEditing] = useState(false);
  const [editTitle, setEditTitle] = useState('');
  const [editAuthors, setEditAuthors] = useState<string[]>([]);
  const [editAbstract, setEditAbstract] = useState('');
  const [editKeywords, setEditKeywords] = useState<string[]>([]);
  const [editSections, setEditSections] = useState<{ heading: string; content: string }[]>([]);
  const [editReferences, setEditReferences] = useState<string[]>([]);
  const [editAffiliations, setEditAffiliations] = useState<string[]>([]);
  const [editEmails, setEditEmails] = useState<string[]>([]);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const tocRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.report) {
          const r = p.outputs.report;
          setReport(r);
          setEditTitle(r.title || '');
          setEditAuthors(Array.isArray(r.authors) ? [...r.authors] : []);
          setEditAbstract(r.abstract || '');
          setEditKeywords(Array.isArray(r.keywords) ? [...r.keywords] : []);
          setEditSections((r.sections || []).map((s: any) => ({ heading: s.heading || '', content: s.content || '' })));
          setEditReferences((r.references || []).map((ref: any) =>
            typeof ref === 'object' ? `${ref.authors}, "${ref.title}," ${ref.venue}, ${ref.year}.` : String(ref)
          ));
          setEditAffiliations(Array.isArray(r.affiliations) ? [...r.affiliations] : []);
          setEditEmails(Array.isArray(r.emails) ? [...r.emails] : []);
        }
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Failed to load project');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const r = await agentsAPI.generateReport(id);
      setReport(r.report);
      setEditTitle(r.report.title || '');
      setEditAuthors(Array.isArray(r.report.authors) ? [...r.report.authors] : []);
      setEditAbstract(r.report.abstract || '');
      setEditKeywords(Array.isArray(r.report.keywords) ? [...r.report.keywords] : []);
      setEditSections((r.report.sections || []).map((s: any) => ({ heading: s.heading || '', content: s.content || '' })));
      setEditReferences((r.report.references || []).map((ref: any) =>
        typeof ref === 'object' ? `${ref.authors}, "${ref.title}," ${ref.venue}, ${ref.year}.` : String(ref)
      ));
      setEditAffiliations(Array.isArray(r.report.affiliations) ? [...r.report.affiliations] : []);
      setEditEmails(Array.isArray(r.report.emails) ? [...r.report.emails] : []);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Report generation failed.');
    }
    setGenerating(false);
  };

  const handleSaveEdits = async () => {
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      const updatedReport = {
        title: editTitle,
        authors: editAuthors.filter(a => a.trim()),
        affiliations: editAffiliations.filter(a => a.trim()),
        emails: editEmails.filter(e => e.trim()),
        abstract: editAbstract,
        keywords: editKeywords.filter(k => k.trim()),
        sections: editSections.filter(s => s.heading.trim() || s.content.trim()),
        references: editReferences.filter(r => r.trim()),
      };
      await agentsAPI.saveReport(id, updatedReport);
      setReport(updatedReport);
      setEditing(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to save edits.');
    } finally {
      setSaving(false);
    }
  };

  const handleDownload = async (format: 'docx' | 'pdf' | 'md') => {
    if (!report) return;

    if (format === 'md') {
      const r = editing ? { ...report, title: editTitle, authors: editAuthors, affiliations: editAffiliations, emails: editEmails, abstract: editAbstract, keywords: editKeywords, sections: editSections, references: editReferences } : report;
      const content = [
        `# ${r.title}\n\n`,
        `**Authors:** ${(r.authors || []).join(', ')}\n\n`,
        ...(r.affiliations?.length ? [`**Affiliations:** ${r.affiliations.join('; ')}\n\n`] : []),
        ...(r.emails?.length ? [`**Emails:** ${r.emails.join(', ')}\n\n`] : []),
        `**Keywords:** ${(r.keywords || []).join(', ')}\n\n`,
        `## Abstract\n\n${r.abstract}\n\n`,
        ...(r.sections || []).map((s: any) => `## ${s.heading}\n\n${s.content}\n\n`),
        `## References\n\n${(r.references || []).map((ref: any, i: number) => {
          if (typeof ref === 'object') return `[${ref.id || i + 1}] ${ref.authors}, "${ref.title}," ${ref.venue}, ${ref.year}.`;
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
    setError('');
    try {
      const accessToken = useAuthStore.getState().accessToken;
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const url = `${apiUrl}/api/agents/${id}/download/${format}`;
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), 30000);
      const response = await fetch(url, {
        headers: { Authorization: `Bearer ${accessToken}` },
        signal: ctrl.signal,
      });
      clearTimeout(timer);
      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
        throw new Error(err.detail || `Download failed: ${response.status}`);
      }
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = `research_paper.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(objectUrl);
    } catch (e: any) {
      const msg = e?.name === 'AbortError' ? 'Download timed out. Try again.' : (e?.message || 'Download failed');
      setError(msg);
      console.error('Download error:', e);
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

  const addAuthor = () => setEditAuthors([...editAuthors, '']);
  const removeAuthor = (idx: number) => setEditAuthors(editAuthors.filter((_, i) => i !== idx));
  const addKeyword = () => setEditKeywords([...editKeywords, '']);
  const removeKeyword = (idx: number) => setEditKeywords(editKeywords.filter((_, i) => i !== idx));
  const addSection = () => setEditSections([...editSections, { heading: '', content: '' }]);
  const removeSection = (idx: number) => setEditSections(editSections.filter((_, i) => i !== idx));
  const addRef = () => setEditReferences([...editReferences, '']);
  const removeRef = (idx: number) => setEditReferences(editReferences.filter((_, i) => i !== idx));
  const addAffiliation = () => setEditAffiliations([...editAffiliations, '']);
  const removeAffiliation = (idx: number) => setEditAffiliations(editAffiliations.filter((_, i) => i !== idx));
  const addEmail = () => setEditEmails([...editEmails, '']);
  const removeEmail = (idx: number) => setEditEmails(editEmails.filter((_, i) => i !== idx));

  if (loading) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Loading...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-8 max-w-6xl mx-auto">
        {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2"><AlertCircle size={14} /> {String(error)}</div>}
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <FileText size={32} className="text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No research paper generated yet.</p>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary">
            {generating ? <><Loader2 size={14} className="animate-spin" /> Generating...</> : 'Generate Report'}
          </button>
        </div>
      </div>
    );
  }

  const displayReport = editing ? {
    ...report,
    title: editTitle,
    authors: editAuthors.filter(a => a.trim()),
    affiliations: editAffiliations.filter(a => a.trim()),
    emails: editEmails.filter(e => e.trim()),
    abstract: editAbstract,
    keywords: editKeywords.filter(k => k.trim()),
    sections: editSections.filter(s => s.heading.trim() || s.content.trim()),
    references: editReferences.filter(r => r.trim()),
  } : report;

  const sections = displayReport.sections || [];
  const references = displayReport.references || [];
  const tocItems = ['Abstract', ...sections.map((s: any) => s.heading)];
  if (references.length > 0) tocItems.push('References');

  const scrollToSection = (index: number) => {
    setActiveSection(index);
    setShowToc(false);
    const el = document.getElementById(`section-${index}`);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Research Paper</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 12 of 13 — {editing ? 'Editing mode' : 'Complete'}</p>
        </div>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <button onClick={handleSaveEdits} disabled={saving}
                className="btn-primary flex items-center gap-1.5">
                {saving ? <Loader2 size={14} className="animate-spin" /> :
                  saved ? <CheckCircle2 size={14} className="text-green-400" /> :
                    <Save size={14} />}
                {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Edits'}
              </button>
              <button onClick={() => setEditing(false)}
                className="btn-ghost text-xs flex items-center gap-1">
                <X size={13} /> Cancel
              </button>
            </>
          ) : (
            <>
              <button onClick={() => setEditing(true)}
                className="btn-secondary flex items-center gap-1.5">
                <Pencil size={14} /> Edit
              </button>
              <button disabled={downloading === 'docx'} onClick={() => handleDownload('docx')} className="btn-secondary">
                {downloading === 'docx' ? <Loader2 className="animate-spin" size={14} /> : <FileText size={14} />}
                {downloading === 'docx' ? 'Generating...' : 'DOCX'}
              </button>
              <button disabled={downloading === 'pdf'} onClick={() => handleDownload('pdf')} className="btn-secondary">
                {downloading === 'pdf' ? <Loader2 className="animate-spin" size={14} /> : <Download size={14} />}
                {downloading === 'pdf' ? 'Generating...' : 'PDF'}
              </button>
              <button onClick={() => handleDownload('md')} className="btn-ghost text-xs">MD</button>
            </>
          )}
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2"><AlertCircle size={14} /> {String(error)}</div>}

      {/* TOC */}
      <div className="relative mb-4" ref={tocRef}>
        <button onClick={() => setShowToc(!showToc)}
          className="card flex items-center gap-2 py-2.5 px-4 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] w-full">
          <BookOpen size={13} />
          <span className="font-medium">Jump to section</span>
          <span className="text-[var(--text-muted)] mx-1">·</span>
          <span className="text-[var(--text-muted)]">{tocItems[activeSection]}</span>
          <ChevronDown size={12} className={`ml-auto transition-transform ${showToc ? 'rotate-180' : ''}`} />
        </button>
        {showToc && (
          <>
            <div className="fixed inset-0 z-10" onClick={() => setShowToc(false)} />
            <div className="absolute left-0 right-0 top-full mt-1 z-20 card p-1.5 shadow-xl border border-[var(--border)]">
              {tocItems.map((heading, i) => (
                <button key={i} onClick={() => scrollToSection(i)}
                  className={`w-full text-left text-xs px-3 py-2 rounded-md transition-all ${
                    activeSection === i ? 'bg-brand-600/20 text-brand-400 font-medium' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-secondary)]'
                  }`}>
                  {heading}
                </button>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Paper Content */}
      <div className="card space-y-6">
        {/* Title */}
        <div className="border-b border-[var(--border)] pb-5 text-center" id="section-0">
          {editing ? (
            <input type="text" value={editTitle} onChange={e => setEditTitle(e.target.value)}
              className="w-full text-xl font-bold text-[var(--text-primary)] text-center bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 pb-2" />
          ) : (
            <h2 className="text-xl font-bold text-[var(--text-primary)] leading-snug mb-2">{displayReport.title}</h2>
          )}

          {editing ? (
            <div className="mt-3 space-y-2">
              {editAuthors.map((a, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input type="text" value={a} onChange={e => { const n = [...editAuthors]; n[i] = e.target.value; setEditAuthors(n); }}
                    className="flex-1 text-sm italic text-[var(--text-secondary)] bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 py-1" />
                  <button onClick={() => removeAuthor(i)} className="text-red-400 hover:text-red-300"><Trash2 size={12} /></button>
                </div>
              ))}
              <button onClick={addAuthor} className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1"><Plus size={11} /> Add author</button>
            </div>
          ) : (
            displayReport.authors?.length > 0 && (
              <p className="text-sm italic text-[var(--text-secondary)] mb-3">{displayReport.authors.join(', ')}</p>
            )
          )}

          {editing ? (
            <div className="mt-2 space-y-1.5">
              {editAffiliations.map((a, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[10px] text-[var(--text-muted)] w-16 text-right">Affil.</span>
                  <input type="text" value={a} onChange={e => { const n = [...editAffiliations]; n[i] = e.target.value; setEditAffiliations(n); }}
                    className="flex-1 text-xs text-[var(--text-secondary)] bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 py-0.5" />
                  <button onClick={() => removeAffiliation(i)} className="text-red-400 hover:text-red-300"><Trash2 size={10} /></button>
                </div>
              ))}
              <button onClick={addAffiliation} className="text-[10px] text-brand-400 hover:text-brand-300 flex items-center gap-1"><Plus size={9} /> Add affiliation</button>
            </div>
          ) : (
            displayReport.affiliations?.length > 0 && (
              <p className="text-xs text-[var(--text-muted)] mb-2">{displayReport.affiliations.join('; ')}</p>
            )
          )}

          {editing ? (
            <div className="mt-2 space-y-1.5">
              {editEmails.map((e, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[10px] text-[var(--text-muted)] w-16 text-right">Email</span>
                  <input type="email" value={e} onChange={ev => { const n = [...editEmails]; n[i] = ev.target.value; setEditEmails(n); }}
                    className="flex-1 text-xs text-[var(--text-secondary)] bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 py-0.5" />
                  <button onClick={() => removeEmail(i)} className="text-red-400 hover:text-red-300"><Trash2 size={10} /></button>
                </div>
              ))}
              <button onClick={addEmail} className="text-[10px] text-brand-400 hover:text-brand-300 flex items-center gap-1"><Plus size={9} /> Add email</button>
            </div>
          ) : (
            displayReport.emails?.length > 0 && (
              <p className="text-[10px] text-[var(--text-muted)] mb-2">{displayReport.emails.join(', ')}</p>
            )
          )}

          {editing ? (
            <div className="mt-3 flex flex-wrap gap-1.5 justify-center">
              {editKeywords.map((kw, i) => (
                <div key={i} className="flex items-center gap-1">
                  <input type="text" value={kw} onChange={e => { const n = [...editKeywords]; n[i] = e.target.value; setEditKeywords(n); }}
                    className="w-24 text-[10px] bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 text-center" />
                  <button onClick={() => removeKeyword(i)} className="text-red-400 hover:text-red-300"><X size={10} /></button>
                </div>
              ))}
              <button onClick={addKeyword} className="text-[10px] text-brand-400">+tag</button>
            </div>
          ) : (
            displayReport.keywords?.length > 0 && (
              <div className="flex flex-wrap gap-1.5 justify-center">
                {displayReport.keywords.map((kw: string) => (
                  <span key={kw} className="badge-blue flex items-center gap-1"><Tag size={9} /> {kw}</span>
                ))}
              </div>
            )
          )}
        </div>

        {/* Abstract */}
        <div id="section-1" className="rounded-lg border-l-4 border-brand-500 bg-[var(--bg-secondary)] p-4">
          <span className="italic text-[var(--text-muted)] text-sm">Abstract — </span>
          {editing ? (
            <textarea value={editAbstract} onChange={e => setEditAbstract(e.target.value)} rows={6}
              className="w-full mt-2 text-sm text-[var(--text-secondary)] leading-relaxed bg-transparent border border-[var(--border)] rounded-lg p-2 focus:outline-none focus:border-brand-500 resize-none" />
          ) : (
            <span className="text-sm text-[var(--text-secondary)] leading-relaxed">{displayReport.abstract}</span>
          )}
        </div>

        {/* Index Terms */}
        {displayReport.keywords?.length > 0 && !editing && (
          <p className="text-sm">
            <span className="italic text-[var(--text-muted)]">Index Terms — </span>
            <span className="text-[var(--text-secondary)]">{displayReport.keywords.join(', ')}</span>
          </p>
        )}

        {/* Sections */}
        {sections.map((section: any, i: number) => {
          const sectionIndex = i + 2;
          return (
            <div key={i} id={`section-${sectionIndex}`} className="border-t border-[var(--border)] pt-5">
              {editing ? (
                <div className="mb-3 flex items-center gap-2">
                  <input type="text" value={editSections[i]?.heading ?? ''} placeholder="Section heading"
                    onChange={e => { const n = [...editSections]; n[i] = { ...n[i], heading: e.target.value }; setEditSections(n); }}
                    className="flex-1 text-sm font-bold text-[var(--text-primary)] text-center uppercase tracking-wide bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 pb-1" />
                  <button onClick={() => removeSection(i)} className="text-red-400 hover:text-red-300"><Trash2 size={12} /></button>
                </div>
              ) : (
                <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center uppercase tracking-wide">{section.heading}</h3>
              )}

              {editing ? (
                <textarea value={editSections[i]?.content ?? ''} rows={12} placeholder="Section content..."
                  onChange={e => { const n = [...editSections]; n[i] = { ...n[i], content: e.target.value }; setEditSections(n); }}
                  className="w-full text-sm text-[var(--text-secondary)] leading-relaxed bg-transparent border border-[var(--border)] rounded-lg p-3 focus:outline-none focus:border-brand-500 resize-y whitespace-pre-wrap" />
              ) : (
                <div className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-line">
                  {renderCitationContent(section.content)}
                </div>
              )}
            </div>
          );
        })}

        {editing && (
          <button onClick={addSection}
            className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors pt-2">
            <Plus size={13} /> Add section
          </button>
        )}

        {/* References */}
        {references.length > 0 && (
          <div id={`section-${tocItems.length - 1}`} className="border-t border-[var(--border)] pt-5">
            <h3 className="text-sm font-bold text-[var(--text-primary)] mb-3 text-center uppercase tracking-wide">References</h3>
            <ol className="space-y-2">
              {references.map((ref: any, i: number) => (
                <li key={i} className="text-xs text-[var(--text-muted)] flex gap-2 items-start">
                  <span className="text-[var(--text-secondary)] font-medium flex-shrink-0">[{i + 1}]</span>
                  {editing ? (
                    <div className="flex-1 flex gap-1">
                      <input type="text" value={editReferences[i] ?? ''} placeholder="Reference..."
                        onChange={e => { const n = [...editReferences]; n[i] = e.target.value; setEditReferences(n); }}
                        className="flex-1 bg-transparent border-b border-[var(--border)] focus:outline-none focus:border-brand-500 py-0.5 text-xs" />
                      <button onClick={() => removeRef(i)} className="text-red-400 hover:text-red-300"><X size={10} /></button>
                    </div>
                  ) : (
                    <span>{typeof ref === 'object' ? `${ref.authors}, "${ref.title}," ${ref.venue}, ${ref.year}.` : ref}</span>
                  )}
                </li>
              ))}
            </ol>
            {editing && (
              <button onClick={addRef}
                className="mt-2 flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors">
                <Plus size={11} /> Add reference
              </button>
            )}
          </div>
        )}
      </div>

      <div className="mt-6 flex justify-center">
        <button onClick={() => router.push(`/projects/${id}/publish`)} className="btn-primary">
          Proceed to Review & Publish <ArrowRight size={14} />
        </button>
      </div>
    </div>
  );
}
