'use client';

import Link from 'next/link';
import { useParams, usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import {
  Brain, BookOpen, Search, Lightbulb, Cpu, BookOpenCheck,
  FileText, ChevronRight, ArrowLeft, Zap, Menu,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import clsx from 'clsx';
import dynamic from 'next/dynamic';

const ChatPanel = dynamic(() => import('@/components/project/ChatPanel'), { ssr: false });

const STEPS = [
  { key: 'input',   label: 'NLP Analysis',     icon: Brain,     step: 1 },
  { key: 'papers',  label: 'Paper Explorer',   icon: BookOpen,  step: 2 },
  { key: 'gaps',    label: 'Gap Analysis',     icon: Search,    step: 3 },
  { key: 'ideas',   label: 'Ideas',            icon: Lightbulb, step: 4 },
  { key: 'planner', label: 'Execution Plan',   icon: Cpu,       step: 5 },
  { key: 'guide',   label: 'Research Guide',   icon: BookOpenCheck, step: 6 },
  { key: 'report',  label: 'Paper',            icon: FileText,  step: 7 },
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
            Step {currentStep?.step || '?'} of 7
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
            href={`/projects/${id}/input`}
            className="flex items-center gap-2 rounded-lg px-3 py-2 text-[11px] bg-brand-600/20 text-brand-400 hover:bg-brand-600/30 transition-all w-full"
          >
            <Zap size={11} />
            <span>Full Analysis</span>
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
        {children}
      </main>

      <ChatPanel projectId={id} />
    </div>
  );
}
