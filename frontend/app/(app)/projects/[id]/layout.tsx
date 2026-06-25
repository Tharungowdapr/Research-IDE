'use client';

import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Brain, BookOpen, Search, Lightbulb, Cpu, BookOpenCheck,
  FileText, ChevronRight, ArrowLeft, Zap, Menu, Target, Database,
  Code2, FlaskConical, BarChart3, CheckCircle2, Globe,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import clsx from 'clsx';
import dynamic from 'next/dynamic';

const ChatPanel = dynamic(() => import('@/components/project/ChatPanel'), { ssr: false });

const STEPS = [
  { key: 'analysis',    label: 'NLP Analysis',       icon: Brain,        step: 1,
    desc: 'Deep linguistic analysis of your research topic using spaCy (tokenization, POS, NER, dependency parsing), KeyBERT keyphrase extraction, SentenceTransformers embeddings, and LLM-powered query expansion. This foundational step transforms your raw research idea into structured NLP features that power all downstream steps.' },
  { key: 'papers',      label: 'Literature Review',  icon: BookOpen,     step: 2,
    desc: 'Automated paper retrieval from arXiv and other sources using search queries generated during analysis. Each paper is scored for relevance, and you can expand/collapse abstracts inline to quickly survey the landscape before diving into gap analysis.' },
  { key: 'gaps',        label: 'Research Gap',       icon: Search,        step: 3,
    desc: 'Identify underexplored areas, methodological weaknesses, and dataset limitations by mining the retrieved papers. Gaps are categorized by type (methodological, dataset, evaluation, application, theoretical) with confidence scores and source paper references.' },
  { key: 'ideas',       label: 'Research Ideas',     icon: Lightbulb,     step: 4,
    desc: 'Generate novel research ideas from identified gaps. Each idea is scored by novelty and feasibility, with suggested methods, datasets, and time estimates. Select the best idea to guide your research objectives.' },
  { key: 'objectives',  label: 'Objectives',         icon: Target,        step: 5,
    desc: 'Formulate 3-5 SMART (Specific, Measurable, Achievable, Relevant, Time-bound) research objectives derived from your selected research gap. Each objective includes success criteria and aligns with your overall research direction.' },
  { key: 'planner',     label: 'Methodology',        icon: Cpu,           step: 6,
    desc: 'Design your research methodology — a structured plan covering research design, data requirements, tools/technologies, implementation phases, evaluation strategy, budget/resources, timeline with milestones, and risk mitigation.' },
  { key: 'data',        label: 'Data Pipeline',      icon: Database,      step: 7,
    desc: 'Plan your data acquisition and preprocessing pipeline. Suggests relevant datasets, preprocessing steps (cleaning, augmentation, splitting), tools/libraries, and ethical considerations with severity indicators for responsible research.' },
  { key: 'code',        label: 'Implementation',     icon: Code2,         step: 8,
    desc: 'Browse and manage your implementation code. Upload and view source files with syntax highlighting, or generate boilerplate code based on your methodology and data pipeline specifications.' },
  { key: 'experiments', label: 'Experiments',        icon: FlaskConical,  step: 9,
    desc: 'Design your experimental setup — model configurations, hyperparameter grids, evaluation protocols, baseline comparisons, ablation studies, and statistical testing plans to rigorously validate your approach.' },
  { key: 'results',     label: 'Results Analysis',   icon: BarChart3,     step: 10,
    desc: 'Plan your results analysis strategy. Generate comparison table templates, visualization suggestions (charts, graphs), statistical test recommendations, and discussion points for interpreting your findings.' },
  { key: 'guide',       label: 'Research Guide',     icon: BookOpenCheck, step: 11,
    desc: 'A comprehensive guide to navigate your research journey. Includes writing checklists, presentation slide generation, citation management tips, and conference submission guidelines.' },
  { key: 'report',      label: 'Paper Writing',      icon: FileText,      step: 12,
    desc: 'Write and structure your research paper with section-by-section guidance. Includes abstract, introduction, methodology, results, discussion, and conclusion templates with smooth-scroll navigation between sections.' },
  { key: 'publish',     label: 'Review & Publish',   icon: CheckCircle2,  step: 13,
    desc: 'Final quality checks before submission. Formatting checklist, plagiarism guidelines, suggested venues with deadlines, self-review criteria, cover letter template, and a timeline for your publication roadmap.' },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const [project, setProject] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    projectsAPI.get(id).then(setProject).catch(console.error);
  }, [id]);

  const currentStep = STEPS.find((s) => pathname.includes(`/${s.key}`));

  return (
    <div className="flex min-h-screen">
      {/* Project Step Nav - IDE-like left panel */}
      <aside className={clsx(
        'border-r border-[var(--border)] bg-[var(--bg-secondary)] flex flex-col flex-shrink-0 transition-all duration-200',
        sidebarOpen ? 'w-52' : 'w-0 overflow-hidden'
      )}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
          <Link
            href="/projects"
            className="flex items-center gap-1.5 text-[10px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
          >
            <ArrowLeft size={10} /> Projects
          </Link>
          <button onClick={() => setSidebarOpen(false)} className="btn-icon w-5 h-5">
            <Menu size={12} />
          </button>
        </div>

        <div className="px-4 py-3 border-b border-[var(--border)]">
          <p className="text-xs font-medium text-[var(--text-primary)] truncate" title={project?.title}>
            {project?.title || 'Loading...'}
          </p>
          <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
            Step {currentStep?.step || '?'} of {STEPS.length}
          </p>
        </div>

        <nav className="flex-1 py-2 overflow-y-auto">
          {STEPS.map((step) => {
            const isActive = pathname.includes(`/${step.key}`);
            const Icon = step.icon;
            return (
              <Link
                key={step.key}
                href={`/projects/${id}/${step.key}`}
                className={clsx(
                  'flex items-center gap-2.5 px-4 py-2.5 text-xs transition-all relative',
                  isActive
                    ? 'bg-brand-600/20 text-brand-400 border-r-2 border-brand-500'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                )}
              >
                <div className={clsx(
                  'flex h-5 w-5 items-center justify-center rounded text-[10px] font-bold flex-shrink-0',
                  isActive ? 'bg-brand-600/30 text-brand-400' : 'bg-[var(--bg-card)] text-[var(--text-muted)]'
                )}>
                  {step.step}
                </div>
                <Icon size={12} />
                <span className="truncate">{step.label}</span>
              </Link>
            );
          })}
        </nav>

        <div className="px-3 py-3 border-t border-[var(--border)] space-y-2">
          <Link
            href={`/projects/${id}/analysis#auto-pipeline`}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-[11px] bg-brand-600/20 text-brand-400 hover:bg-brand-600/30 transition-all w-full"
          >
            <Zap size={11} />
            <span>Run Auto-Pipeline</span>
          </Link>
        </div>
      </aside>

      {/* Sidebar toggle when collapsed */}
      {!sidebarOpen && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed left-0 top-1/2 -translate-y-1/2 z-30 flex h-10 w-5 items-center justify-center rounded-r-lg bg-[var(--bg-secondary)] border border-l-0 border-[var(--border)] text-[var(--text-muted)] hover:text-[var(--text-primary)]"
        >
          <ChevronRight size={12} />
        </button>
      )}

      {/* Main Content */}
      <main className="flex-1 overflow-auto min-w-0">
        {/* Step description banner */}
        {currentStep && (
          <div className="px-8 pt-6 pb-0">
            <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]/50 px-5 py-3">
              <div className="flex items-start gap-3">
                <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0 mt-0.5">
                  {currentStep.step}
                </div>
                <div className="min-w-0">
                  <h2 className="text-sm font-semibold text-[var(--text-primary)]">
                    {currentStep.label}
                  </h2>
                  <p className="text-xs text-[var(--text-muted)] mt-1 leading-relaxed">
                    {currentStep.desc}
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
        {children}
        {/* Prev / Next navigation */}
        {currentStep && (
          <div className="px-8 pb-8 pt-4">
            <div className="flex items-center justify-between rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)]/30 px-5 py-3">
              <div>
                {currentStep.step > 1 && (() => {
                  const prev = STEPS[currentStep.step - 2];
                  return (
                    <Link
                      href={`/projects/${id}/${prev.key}`}
                      className="flex items-center gap-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                    >
                      <ChevronRight size={12} className="rotate-180" />
                      <span>Step {prev.step}: {prev.label}</span>
                    </Link>
                  );
                })()}
              </div>
              <div className="text-[10px] text-[var(--text-muted)] font-medium">
                Step {currentStep.step} of {STEPS.length}
              </div>
              <div>
                {currentStep.step < STEPS.length && (() => {
                  const next = STEPS[currentStep.step];
                  return (
                    <Link
                      href={`/projects/${id}/${next.key}`}
                      className="flex items-center gap-2 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] transition-colors"
                    >
                      <span>Step {next.step}: {next.label}</span>
                      <ChevronRight size={12} />
                    </Link>
                  );
                })()}
              </div>
            </div>
          </div>
        )}
      </main>

      <ChatPanel projectId={id} />
    </div>
  );
}
