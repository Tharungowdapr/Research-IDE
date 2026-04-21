'use client';

import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Brain, BookOpen, Search, Lightbulb, Cpu, Code2,
  FileText, ChevronRight, ArrowLeft,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import clsx from 'clsx';

const STEPS = [
  { key: 'input',   label: 'NLP Analysis',     icon: Brain,     step: 1 },
  { key: 'papers',  label: 'Paper Explorer',   icon: BookOpen,  step: 2 },
  { key: 'gaps',    label: 'Gap Analysis',     icon: Search,    step: 3 },
  { key: 'ideas',   label: 'Ideas',            icon: Lightbulb, step: 4 },
  { key: 'planner', label: 'Execution Plan',   icon: Cpu,       step: 5 },
  { key: 'code',    label: 'Code',             icon: Code2,     step: 6 },
  { key: 'report',  label: 'Paper',            icon: FileText,  step: 7 },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const { id } = useParams<{ id: string }>();
  const pathname = usePathname();
  const [project, setProject] = useState<any>(null);

  useEffect(() => {
    projectsAPI.get(id).then(setProject).catch(console.error);
  }, [id]);

  const currentStep = STEPS.find((s) => pathname.includes(`/${s.key}`));

  return (
    <div className="flex min-h-screen">
      {/* Project Step Nav */}
      <aside className="w-52 border-r border-[var(--border)] bg-[var(--bg-secondary)] flex flex-col flex-shrink-0">
        {/* Back to projects */}
        <Link
          href="/projects"
          className="flex items-center gap-2 px-4 py-3 text-xs text-[var(--text-muted)] hover:text-[var(--text-secondary)] border-b border-[var(--border)] transition-colors"
        >
          <ArrowLeft size={12} /> Back to Projects
        </Link>

        {/* Project title */}
        <div className="px-4 py-3 border-b border-[var(--border)]">
          <p className="text-xs font-medium text-[var(--text-primary)] truncate" title={project?.title}>
            {project?.title || 'Loading...'}
          </p>
          <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
            Step {currentStep?.step || '?'} of 7
          </p>
        </div>

        {/* Steps */}
        <nav className="flex-1 py-2">
          {STEPS.map((step) => {
            const isActive = pathname.includes(`/${step.key}`);
            const Icon = step.icon;
            return (
              <Link
                key={step.key}
                href={`/projects/${id}/${step.key}`}
                className={clsx(
                  'flex items-center gap-2.5 px-4 py-2.5 text-xs transition-all',
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
                <Icon size={13} />
                <span>{step.label}</span>
              </Link>
            );
          })}
        </nav>
      </aside>

      {/* Page Content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
