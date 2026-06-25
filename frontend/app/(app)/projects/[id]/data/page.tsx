'use client';

import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  Database, ArrowRight, Loader2, AlertCircle, CheckCircle2,
  Server, HardDrive, Shield, FileText,
} from 'lucide-react';
import { projectsAPI, agentsAPI } from '@/services/api';

export default function DataPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [dataPlan, setDataPlan] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const p = await projectsAPI.get(id);
        if (p.outputs?.data_plan) setDataPlan(p.outputs.data_plan);
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
      const r = await agentsAPI.generateDataPlan(id);
      setDataPlan(r.data_plan);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed.');
    } finally {
      setGenerating(false);
    }
  };

  const handleProceed = () => router.push(`/projects/${id}/code`);

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Data Pipeline</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 7 of 13 — Plan your data collection and preprocessing</p>
        </div>
        {dataPlan && (
          <button onClick={handleProceed} className="btn-primary"><ArrowRight size={14} /> Implementation</button>
        )}
      </div>

      {error && <ErrorBanner msg={error} />}

      {!dataPlan && !generating ? (
        <EmptyState icon={Database} title="No data plan yet" action={handleGenerate} loading={generating} />
      ) : (
        <div className="space-y-5">
          {generating && !dataPlan && <Loader className="mx-auto" />}

          {dataPlan?.suggested_datasets?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Database size={14} className="text-brand-400" /> Suggested Datasets
              </h2>
              <div className="space-y-3">
                {dataPlan.suggested_datasets.map((ds: any, i: number) => (
                  <div key={i} className="rounded-lg border border-[var(--border)] p-3 text-sm">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-[var(--text-primary)]">{ds.name}</span>
                      {ds.licensing && <span className="badge-blue text-[10px]">{ds.licensing}</span>}
                    </div>
                    <p className="text-xs text-[var(--text-secondary)]">{ds.description}</p>
                    <div className="flex flex-wrap gap-2 mt-1.5 text-[10px] text-[var(--text-muted)]">
                      {ds.source && <span>Source: {ds.source}</span>}
                      {ds.size && <span>Size: {ds.size}</span>}
                      {ds.format && <span>Format: {ds.format}</span>}
                    </div>
                    {ds.why_suitable && (
                      <p className="text-xs text-brand-400 mt-1">→ {ds.why_suitable}</p>
                    )}
                    {ds.preprocessing_needed && (
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">Preprocessing: {ds.preprocessing_needed}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {dataPlan?.preprocessing?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-3 flex items-center gap-2">
                <Server size={14} className="text-brand-400" /> Preprocessing Pipeline
              </h2>
              <div className="space-y-2">
                {dataPlan.preprocessing.map((step: any, i: number) => (
                  <div key={i} className="flex items-start gap-3 text-sm">
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-[10px] font-bold flex-shrink-0">{step.step || i + 1}</span>
                    <div>
                      <p className="text-[var(--text-primary)]">{step.task}</p>
                      <p className="text-xs text-[var(--text-muted)]">{step.technique}</p>
                      {step.tools?.length > 0 && (
                        <div className="flex gap-1 mt-0.5">
                          {step.tools.map((t: string) => <span key={t} className="badge-blue text-[10px]">{t}</span>)}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {dataPlan?.data_pipeline_tools?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <HardDrive size={14} className="text-brand-400" /> Tools & Technologies
              </h2>
              <div className="flex flex-wrap gap-1.5">
                {dataPlan.data_pipeline_tools.map((t: string) => <span key={t} className="badge-purple">{t}</span>)}
              </div>
              {dataPlan.storage_recommendation && (
                <p className="text-xs text-[var(--text-muted)] mt-2">Storage: {dataPlan.storage_recommendation}</p>
              )}
            </div>
          )}

          {dataPlan?.ethical_considerations?.length > 0 && (
            <div className="card">
              <h2 className="font-semibold text-sm text-[var(--text-primary)] mb-2 flex items-center gap-2">
                <Shield size={14} className="text-brand-400" /> Ethical Considerations
              </h2>
              <div className="space-y-2">
                {dataPlan.ethical_considerations.map((e: any, i: number) => (
                  <div key={i} className="rounded-lg border border-[var(--border)] p-3">
                    <p className="text-sm font-medium text-[var(--text-primary)]">{e.concern || e}</p>
                    {e.mitigation && <p className="text-xs text-[var(--text-muted)] mt-1">Mitigation: {e.mitigation}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex gap-2 justify-end">
            <button onClick={handleGenerate} disabled={generating} className="btn-ghost text-xs">Regenerate</button>
            <button onClick={handleProceed} className="btn-primary"><ArrowRight size={14} /> Implementation</button>
          </div>
        </div>
      )}
    </div>
  );
}

function ErrorBanner({ msg }: { msg: string }) {
  return <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400 flex items-center gap-2"><AlertCircle size={14} /> {String(msg)}</div>;
}

function EmptyState({ icon: Icon, title, action, loading }: any) {
  return (
    <div className="card text-center py-16">
      <Icon size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
      <p className="text-sm text-[var(--text-secondary)]">{title}</p>
      <button onClick={action} disabled={loading} className="btn-primary mt-4">
        {loading ? <><Loader2 size={14} className="animate-spin" /> Generating...</> : <><Database size={14} /> Generate Data Plan</>}
      </button>
    </div>
  );
}

function Loader({ className }: { className?: string }) {
  return <div className={`card text-center py-12 ${className}`}><Loader2 className="animate-spin text-brand-400 mx-auto" size={24} /><p className="text-sm text-[var(--text-secondary)] mt-3">Generating data plan...</p></div>;
}
