'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Lightbulb, ArrowRight, Loader2, Sparkles } from 'lucide-react';
import { projectsAPI } from '@/services/api';

const EXAMPLES = [
  'Crop yield prediction in India using satellite imagery with low compute requirements',
  'Multilingual sentiment analysis for low-resource African languages',
  'Real-time anomaly detection in industrial IoT sensor data using edge AI',
  'Medical image segmentation for rural clinics with limited GPU resources',
];

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim()) return;
    setError('');
    setLoading(true);
    try {
      const project = await projectsAPI.create({
        title: title.trim() || inputText.slice(0, 60) + (inputText.length > 60 ? '...' : ''),
        input_text: inputText.trim(),
      });
      router.push(`/projects/${project.id}/input`);
    } catch (e: any) {
      setError(e.response?.data?.detail || 'Failed to create project');
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/20">
            <Sparkles size={18} className="text-brand-400" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">New Research Project</h1>
        </div>
        <p className="text-sm text-[var(--text-secondary)] ml-12">
          Describe your research idea or problem. Be specific about domain, constraints, and goals.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-5">
        {error && (
          <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        <div className="card">
          <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
            Project Title <span className="text-[var(--text-muted)]">(optional — auto-generated if empty)</span>
          </label>
          <input
            type="text"
            className="input"
            placeholder="e.g. Crop Yield Prediction with Satellite Data"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </div>

        <div className="card">
          <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
            Research Description <span className="text-red-400">*</span>
          </label>
          <textarea
            className="input min-h-[180px] resize-none font-sans text-sm leading-relaxed"
            placeholder="Describe your research problem in detail. Include:
• The domain (e.g., NLP, computer vision, healthcare AI)
• The specific problem you want to solve
• Any constraints (compute budget, region, dataset size)
• What kind of contribution you aim to make
• Your skill level and available resources"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            required
            autoFocus
          />
          <div className="flex justify-between mt-1.5">
            <span className="text-xs text-[var(--text-muted)]">Be as specific as possible for better results</span>
            <span className={`text-xs ${inputText.length < 50 ? 'text-yellow-400' : 'text-[var(--text-muted)]'}`}>
              {inputText.length} chars {inputText.length < 50 ? '(too short)' : ''}
            </span>
          </div>
        </div>

        {/* Examples */}
        <div>
          <p className="text-xs font-medium text-[var(--text-secondary)] mb-2 flex items-center gap-1">
            <Lightbulb size={12} className="text-yellow-400" /> Example prompts
          </p>
          <div className="grid gap-2">
            {EXAMPLES.map((ex) => (
              <button
                key={ex}
                type="button"
                onClick={() => setInputText(ex)}
                className="text-left rounded-lg border border-[var(--border)] px-3 py-2.5 text-xs text-[var(--text-secondary)] hover:border-brand-500/40 hover:text-brand-400 transition-all"
              >
                {ex}
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={loading || inputText.trim().length < 20}
          className="btn-primary w-full justify-center py-3 text-sm"
        >
          {loading ? (
            <><Loader2 size={16} className="animate-spin" /> Creating project...</>
          ) : (
            <>Start Research Journey <ArrowRight size={16} /></>
          )}
        </button>
      </form>
    </div>
  );
}
