'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  BarChart3, ArrowRight, Loader2, AlertCircle, Table,
  LineChart, AlertTriangle, Lightbulb, Target, Settings,
  Save, Plus, Trash2, CheckCircle2,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

type MetricEntry = { key: string; value: string; };

export default function ResultsPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [analysis, setAnalysis] = useState<any>(null);
  const [userResults, setUserResults] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [saved, setSaved] = useState(false);
  const [metrics, setMetrics] = useState<MetricEntry[]>([
    { key: 'accuracy', value: '' },
    { key: 'f1_score', value: '' },
    { key: 'precision', value: '' },
    { key: 'recall', value: '' },
  ]);
  const [extraNotes, setExtraNotes] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.analysis_template) setAnalysis(p.outputs.analysis_template);
        if (p.outputs?.user_results) {
          setUserResults(p.outputs.user_results);
          const existing = p.outputs.user_results;
          const entries = Object.entries(existing)
            .filter(([k]) => k !== 'notes')
            .map(([k, v]) => ({ key: k, value: String(v) }));
          if (entries.length > 0) setMetrics(entries);
          if (existing.notes) setExtraNotes(existing.notes);
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
      const r = await agentsAPI.generateAnalysis(id);
      setAnalysis(r.analysis);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleSaveResults = async () => {
    setSaving(true);
    setError('');
    setSaved(false);
    try {
      const metricsObj: Record<string, any> = {};
      for (const m of metrics) {
        if (m.key.trim()) {
          const num = parseFloat(m.value);
          metricsObj[m.key.trim()] = isNaN(num) ? m.value : num;
        }
      }
      if (extraNotes.trim()) metricsObj.notes = extraNotes.trim();

      const payload: any = { project_id: id, metrics: metricsObj };
      await agentsAPI.uploadResults(id, metricsObj);
      setUserResults(metricsObj);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to save results.');
    } finally {
      setSaving(false);
    }
  };

  const addMetric = () => setMetrics([...metrics, { key: '', value: '' }]);
  const removeMetric = (idx: number) => setMetrics(metrics.filter((_, i) => i !== idx));
  const updateMetric = (idx: number, field: 'key' | 'value', val: string) => {
    const next = [...metrics];
    next[idx] = { ...next[idx], [field]: val };
    setMetrics(next);
  };

  const handleProceed = () => router.push(`/projects/${id}/guide`);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="min-h-screen bg-background text-foreground p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Results Analysis</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 10 of 13 — Enter metrics and plan analysis</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleSaveResults} disabled={saving}
            className="btn-secondary flex items-center gap-1.5">
            {saving ? <Loader2 size={14} className="animate-spin" /> :
              saved ? <CheckCircle2 size={14} className="text-green-400" /> :
                <Save size={14} />}
            {saved ? 'Saved!' : saving ? 'Saving...' : 'Save Results'}
          </button>
          {analysis && (
            <button onClick={handleProceed} className="btn-primary"><ArrowRight size={14} /> Research Guide</button>
          )}
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2"><AlertCircle size={14} /> {String(error)}</div>}

      <div className="card mb-5">
        <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
          <Settings size={14} className="text-brand-400" /> Experimental Results
        </h2>
        <p className="text-xs text-[var(--text-muted)] mb-4">
          Enter your experimental metrics (accuracy, F1, inference time, etc.). These will be saved and used in report generation.
        </p>
        <div className="space-y-2">
          {metrics.map((m, i) => (
            <div key={i} className="flex items-center gap-2">
              <input
                type="text"
                placeholder="metric name"
                value={m.key}
                onChange={e => updateMetric(i, 'key', e.target.value)}
                className="flex-1 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-brand-500"
              />
              <input
                type="text"
                placeholder="value"
                value={m.value}
                onChange={e => updateMetric(i, 'value', e.target.value)}
                className="w-32 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-brand-500"
              />
              <button onClick={() => removeMetric(i)}
                className="p-2 rounded-lg text-[var(--text-muted)] hover:text-red-400 hover:bg-red-500/10 transition-colors">
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
        <button onClick={addMetric}
          className="mt-3 flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors">
          <Plus size={13} /> Add metric
        </button>
        <div className="mt-4">
          <textarea
            placeholder="Additional notes (optional)..."
            value={extraNotes}
            onChange={e => setExtraNotes(e.target.value)}
            rows={3}
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2 text-xs text-[var(--text-primary)] focus:outline-none focus:border-brand-500 resize-none"
          />
        </div>
      </div>

      {!analysis && !generating ? (
        <div className="card text-center py-16">
          <BarChart3 size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No analysis plan yet.</p>
          <button onClick={handleGenerate} disabled={generating} className="btn-primary mt-4">
            {generating ? <><Loader2 size={14} className="animate-spin" /> Generating...</> : <><LineChart size={14} /> Generate Analysis Plan</>}
          </button>
        </div>
      ) : (
        <div className="space-y-5">
          {generating && !analysis && (
            <div className="card text-center py-12"><Loader2 className="animate-spin text-brand-400 mx-auto" size={24} /><p className="text-sm mt-3 text-[var(--text-secondary)]">Generating analysis plan...</p></div>
          )}

          {analysis?.comparison_tables?.map((t: any, i: number) => (
            <div key={i} className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Table size={14} className="text-brand-400" /> {t.table_name}
              </h2>
              {t.caption && <p className="text-xs text-[var(--text-muted)] mb-2">{t.caption}</p>}
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-[var(--border)]">
                      {t.columns?.map((col: string, j: number) => (
                        <th key={j} className="text-left px-3 py-2 text-[var(--text-muted)] font-medium">{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {t.rows?.map((row: any[], j: number) => (
                      <tr key={j} className="border-b border-[var(--border)]/50">
                        {row.map((cell: any, k: number) => (
                          <td key={k} className={`px-3 py-2 text-[var(--text-secondary)] ${k === 0 ? 'font-medium text-[var(--text-primary)]' : ''}`}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {t.footnote && <p className="text-xs text-[var(--text-muted)] mt-2">{t.footnote}</p>}
            </div>
          ))}

          {analysis?.baseline_establishment && (
            <div className="card border-brand-500/20 bg-brand-600/5">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Target size={14} className="text-brand-400" /> Baseline Establishment
              </h2>
              {analysis.baseline_establishment.baselines?.map((b: any, i: number) => (
                <div key={i} className="rounded-lg border border-[var(--border)] p-3 mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-[var(--text-primary)]">{b.name}</span>
                    <span className="badge-blue text-[10px]">{b.source}</span>
                  </div>
                  <p className="text-xs text-[var(--text-muted)] mb-1">{b.justification}</p>
                  <div className="flex flex-wrap gap-2 text-[10px] text-[var(--text-secondary)]">
                    {Object.entries(b.expected_metrics || {}).map(([k, v]) => (
                      <span key={k} className="badge-purple">{k}: {String(v)}</span>
                    ))}
                  </div>
                </div>
              ))}
              {analysis.baseline_establishment.evaluation_protocol && (
                <div className="rounded-lg bg-[var(--bg-secondary)] p-3">
                  <p className="font-medium text-[11px] text-[var(--text-muted)] mb-1">Evaluation Protocol</p>
                  <p className="text-xs text-[var(--text-secondary)]">{analysis.baseline_establishment.evaluation_protocol}</p>
                </div>
              )}
              {analysis.baseline_establishment.significance_threshold && (
                <div className="text-xs text-[var(--text-muted)] mt-2">
                  Significance: {analysis.baseline_establishment.significance_threshold}
                </div>
              )}
            </div>
          )}

          {analysis?.visualization_suggestions?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <LineChart size={14} className="text-brand-400" /> Visualization Suggestions
              </h2>
              <div className="space-y-2">
                {analysis.visualization_suggestions.map((v: any, i: number) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    <span className="badge-purple capitalize">{v.type.replace(/_/g, ' ')}</span>
                    <span className="text-[var(--text-secondary)]">{v.title}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {analysis?.discussion_points?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <Lightbulb size={14} className="text-brand-400" /> Discussion Points
              </h2>
              <ul className="space-y-1">
                {analysis.discussion_points.map((p: string, i: number) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)]">• {p}</li>
                ))}
              </ul>
            </div>
          )}

          {analysis?.limitations?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <AlertTriangle size={14} className="text-yellow-400" /> Limitations
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {analysis.limitations.map((l: any, i: number) => {
                  const text = typeof l === 'string' ? l : l?.limitation || JSON.stringify(l);
                  return <span key={i} className="badge-yellow text-[10px]">{String(text)}</span>;
                })}
              </div>
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <button onClick={handleGenerate} disabled={generating} className="btn-ghost text-xs">Regenerate</button>
            <button onClick={handleProceed} className="btn-primary"><ArrowRight size={14} /> Research Guide</button>
          </div>
        </div>
      )}
    </div>
  );
}
