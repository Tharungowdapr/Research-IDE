'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Code2, Download, Copy, Check, Loader2, ArrowRight, FileText } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function CodePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [codeData, setCodeData] = useState<any>(null);
  const [activeFile, setActiveFile] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.code) setCodeData(p.outputs.code);
      else {
        agentsAPI.generateCode(id).then((r) => setCodeData(r.code)).catch(console.error);
      }
      setLoading(false);
    });
  }, [id]);

  const handleCopy = () => {
    const file = codeData?.files?.[activeFile];
    if (file) {
      navigator.clipboard.writeText(file.code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!codeData?.files) return;
    // Create a simple text download of all files
    const content = codeData.files
      .map((f: any) => `# ===== ${f.filename} =====\n\n${f.code}`)
      .join('\n\n');
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'research_project_code.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleGenerateReport = async () => {
    setGenerating(true);
    try {
      await agentsAPI.generateReport(id);
      router.push(`/projects/${id}/report`);
    } catch (e) {
      console.error(e);
      setGenerating(false);
    }
  };

  if (loading || !codeData) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-3">
        <Loader2 className="animate-spin text-brand-400" size={24} />
        <p className="text-sm text-[var(--text-secondary)]">Generating starter code...</p>
      </div>
    );
  }

  const files = codeData.files || [];
  const activeFileData = files[activeFile];

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Generated Code</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 6 of 7 — Starter code for your project</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleDownload} className="btn-secondary">
            <Download size={14} /> Download All
          </button>
          <button onClick={handleGenerateReport} disabled={generating} className="btn-primary">
            {generating ? <Loader2 size={14} className="animate-spin" /> : <FileText size={14} />}
            {generating ? 'Generating...' : 'Write Paper'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-4">
        {/* File List */}
        <div className="col-span-3 space-y-1">
          <p className="text-xs font-medium text-[var(--text-muted)] px-2 mb-2">Files</p>
          {files.map((file: any, i: number) => (
            <button
              key={i}
              onClick={() => setActiveFile(i)}
              className={`w-full text-left rounded-lg px-3 py-2 text-xs transition-all ${
                activeFile === i
                  ? 'bg-brand-600/20 text-brand-400 border border-brand-500/30'
                  : 'text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
              }`}
            >
              <p className="font-mono font-medium">{file.filename}</p>
              <p className="text-[var(--text-muted)] mt-0.5 truncate">{file.description}</p>
            </button>
          ))}

          {/* Setup Instructions */}
          {codeData.setup_instructions?.length > 0 && (
            <div className="mt-4 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] p-3">
              <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">Setup</p>
              <ol className="space-y-1">
                {codeData.setup_instructions.map((step: string, i: number) => (
                  <li key={i} className="text-xs text-[var(--text-muted)]">{i + 1}. {step}</li>
                ))}
              </ol>
              {codeData.run_command && (
                <div className="mt-2 rounded bg-[var(--bg-primary)] px-2 py-1.5">
                  <p className="text-[10px] text-[var(--text-muted)] mb-0.5">Run:</p>
                  <code className="text-xs text-emerald-400 font-mono">{codeData.run_command}</code>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Code View */}
        <div className="col-span-9">
          <div className="rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] overflow-hidden">
            {/* Code Header */}
            <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--border)] bg-[var(--bg-card)]">
              <span className="text-xs font-mono text-[var(--text-secondary)]">
                {activeFileData?.filename}
              </span>
              <button onClick={handleCopy} className="btn-ghost text-xs py-1 px-2">
                {copied ? <><Check size={12} className="text-emerald-400" /> Copied</> : <><Copy size={12} /> Copy</>}
              </button>
            </div>
            {/* Code Content */}
            <pre className="p-4 overflow-auto max-h-[600px] text-xs font-mono text-[var(--text-secondary)] leading-relaxed">
              <code>{activeFileData?.code || ''}</code>
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}
