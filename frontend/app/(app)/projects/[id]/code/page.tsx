'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Code2, ArrowRight, Loader2, AlertCircle, Copy, CheckCircle2 } from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function CodePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [files, setFiles] = useState<{ path: string; content: string }[]>([]);
  const [activeFile, setActiveFile] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.code) {
          const c = p.outputs.code;
          const list = c.file_structure || c.files || (c.code ? [{ path: 'main.py', content: c.code }] : []);
          if (list.length > 0) {
            setFiles(list);
            setActiveFile(list[0].path);
          }
        }
      } catch (e: any) {
        setError(e.response?.data?.detail || 'Could not load project data');
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const handleGenerate = async () => {
    setGenerating(true);
    setError('');
    try {
      const r = await agentsAPI.generateCode(id);
      const list = r.code?.file_structure || r.code?.files || (r.code?.code ? [{ path: 'main.py', content: r.code.code }] : []);
      if (list.length > 0) {
        setFiles(list);
        setActiveFile(list[0].path);
      }
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Generation failed');
    } finally {
      setGenerating(false);
    }
  };

  const handleCopy = async (path: string) => {
    const f = files.find(f => f.path === path);
    if (f?.content) {
      await navigator.clipboard.writeText(f.content);
      setCopied(path);
      setTimeout(() => setCopied(''), 2000);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Implementation</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 8 of 13 — {files.length > 0 ? 'Generated code for your solution' : 'Generate code from your methodology plan'}</p>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleGenerate} disabled={generating} className="btn-secondary text-xs">
            {generating ? <Loader2 size={12} className="animate-spin" /> : <Code2 size={12} />}
            {generating ? 'Generating...' : files.length > 0 ? 'Regenerate' : 'Generate Code'}
          </button>
          {files.length > 0 && (
            <button onClick={() => router.push(`/projects/${id}/experiments`)} className="btn-primary">
              <ArrowRight size={14} /> Experiments
            </button>
          )}
        </div>
      </div>

      {error && <ErrorBanner msg={error} />}

      {files.length === 0 ? (
        <div className="card p-12 text-center">
          <Code2 size={48} className="mx-auto mb-4 text-[var(--text-muted)] opacity-30" />
          <h2 className="text-lg font-semibold text-[var(--text-primary)] mb-2">No Code Generated Yet</h2>
            <p className="text-sm text-[var(--text-muted)] mb-6 max-w-md mx-auto">
              Click &ldquo;Generate Code&rdquo; to have the AI create implementation files based on your methodology plan, project structure, and research context.
            </p>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary">
            {generating ? <Loader2 size={14} className="animate-spin" /> : <Code2 size={14} />}
            {generating ? 'Generating...' : 'Generate Code'}
          </button>
        </div>
      ) : (
        <div className="flex gap-4">
          {files.length > 1 && (
            <div className="w-48 flex-shrink-0 space-y-1">
              {files.map((f) => (
                <button
                  key={f.path}
                  onClick={() => setActiveFile(f.path)}
                  className={`w-full text-left text-xs px-3 py-2 rounded-md transition-all ${
                    activeFile === f.path ? 'bg-brand-600/20 text-brand-400' : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)]'
                  }`}
                >
                  <Code2 size={10} className="inline mr-1.5" />{f.path.split('/').pop()}
                </button>
              ))}
            </div>
          )}
          <div className="flex-1 card p-0 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-[var(--border)] bg-[var(--bg-secondary)]">
              <span className="text-xs font-mono text-[var(--text-muted)]">{activeFile}</span>
              <button onClick={() => handleCopy(activeFile)} className="text-[10px] text-[var(--text-muted)] hover:text-brand-400">
                {copied === activeFile ? <><CheckCircle2 size={12} /> Copied</> : <><Copy size={12} /> Copy</>}
              </button>
            </div>
            <pre className="p-4 text-xs text-[var(--text-secondary)] overflow-auto max-h-[600px] leading-relaxed font-mono">
              {String(files.find(f => f.path === activeFile)?.content || '// No code generated')}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function ErrorBanner({ msg }: any) {
  return (
    <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2">
      <AlertCircle size={14} /> {String(msg)}
    </div>
  );
}
