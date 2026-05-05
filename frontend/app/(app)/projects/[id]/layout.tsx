'use client';

import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Brain, BookOpen, Search, Lightbulb, Cpu,
  FileText, ChevronRight, ArrowLeft, Check, Lock,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import clsx from 'clsx';

const STEPS = [
  { key: 'input',   label: 'NLP Analysis',     icon: Brain,     step: 1, outputKey: 'intent' },
  { key: 'papers',  label: 'Paper Explorer',   icon: BookOpen,  step: 2, outputKey: 'papers' },
  { key: 'gaps',    label: 'Gap Analysis',     icon: Search,    step: 3, outputKey: 'gaps' },
  { key: 'ideas',   label: 'Ideas',            icon: Lightbulb, step: 4, outputKey: 'ideas' },
  { key: 'planner', label: 'Execution Plan',   icon: Cpu,       step: 5, outputKey: 'plan' },
  { key: 'code',    label: 'Build Guide',      icon: BookOpen,  step: 6, outputKey: 'code' },
  { key: 'report',  label: 'Paper',            icon: FileText,  step: 7, outputKey: 'report' },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const [project, setProject] = useState<any>(null);

  useEffect(() => {
    projectsAPI.get(id).then(setProject).catch(console.error);
  }, [id]);

  const currentStep = STEPS.find((s) => pathname?.includes(`/${s.key}`));
  const completedSteps = new Set<string>();
  if (project?.outputs) {
    for (const step of STEPS) {
      if (project.outputs[step.outputKey]) {
        completedSteps.add(step.key);
      }
    }
  }

  const completedCount = completedSteps.size;
  const progressPct = Math.round((completedCount / STEPS.length) * 100);

  return (
    <div className="flex min-h-screen">
      {/* Project Step Nav */}
      <aside className="hidden lg:flex w-56 border-r border-[var(--border)] bg-[var(--bg-secondary)] flex-col flex-shrink-0">
        {/* Back to projects */}
        <Link
          href="/projects"
          className="flex items-center gap-2 px-4 py-3 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] border-b border-[var(--border)] transition-colors font-mono uppercase tracking-wider"
        >
          <ArrowLeft size={12} /> Back
        </Link>

        {/* Project title + progress */}
        <div className="px-4 py-3 border-b border-[var(--border)]">
          <p className="text-xs font-medium text-[var(--text-primary)] truncate font-mono" title={project?.title}>
            {project?.title || 'Loading...'}
          </p>
          <div className="mt-2">
            <div className="flex justify-between text-[10px] text-[var(--text-muted)] font-mono mb-1">
              <span>Progress</span>
              <span>{progressPct}%</span>
            </div>
            <div className="h-1 bg-[var(--bg-primary)] overflow-hidden">
              <div
                className="h-full bg-brand-500 transition-all duration-500"
                style={{ width: `${progressPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Steps */}
        <nav className="flex-1 py-2">
          {STEPS.map((step) => {
            const isActive = pathname?.includes(`/${step.key}`);
            const isCompleted = completedSteps.has(step.key);
            const Icon = step.icon;
            return (
              <Link
                key={step.key}
                href={`/projects/${id}/${step.key}`}
                className={clsx(
                  'flex items-center gap-2.5 px-4 py-2.5 text-xs transition-all font-mono',
                  isActive
                    ? 'bg-brand-600/20 text-brand-500 border-r-2 border-brand-500'
                    : isCompleted
                    ? 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-hover)]'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                )}
              >
                <div className={clsx(
                  'flex h-5 w-5 items-center justify-center text-[10px] font-bold flex-shrink-0',
                  isActive
                    ? 'bg-brand-600/30 text-brand-500'
                    : isCompleted
                    ? 'bg-emerald-500/20 text-emerald-400'
                    : 'bg-[var(--bg-card)] text-[var(--text-muted)]'
                )}>
                  {isCompleted && !isActive ? <Check size={10} /> : step.step}
                </div>
                <Icon size={13} />
                <span className="flex-1">{step.label}</span>
                {isCompleted && !isActive && (
                  <span className="text-emerald-400 text-[10px]">✓</span>
                )}
              </Link>
            );
          })}
        </nav>

        {/* Step count */}
        <div className="px-4 py-3 border-t border-[var(--border)] text-[10px] text-[var(--text-muted)] font-mono">
          {completedCount}/{STEPS.length} steps complete
        </div>
      </aside>

      {/* Page Content */}
      <main className="flex-1 overflow-auto min-w-0">
        {children}
      </main>
    </div>
  );
}
