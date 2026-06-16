'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus, FolderOpen, ChevronRight, Clock, Cpu, BookOpen,
  Lightbulb, Code2, FileText, Brain, Sparkles, Activity,
  BarChart3, ArrowRight, Search,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { formatDistanceToNow } from 'date-fns';

const STAGE_ICONS: Record<string, React.ElementType> = {
  input: Brain, papers: BookOpen, gaps: Search,
  ideas: Lightbulb, planner: Cpu, code: Code2, report: FileText,
};

const STAGE_COLORS: Record<string, string> = {
  input: 'badge-blue', papers: 'badge-blue', gaps: 'badge-yellow',
  ideas: 'badge-purple', planner: 'badge-purple', code: 'badge-green', report: 'badge-green',
};

const QUICK_ACTIONS = [
  {
    href: '/projects/new',
    icon: Plus,
    color: 'bg-brand-600/20 text-brand-400',
    title: 'New Project',
    desc: 'Start from a research question',
  },
  {
    href: '/settings/llm',
    icon: Cpu,
    color: 'bg-emerald-600/20 text-emerald-400',
    title: 'AI Settings',
    desc: 'Configure LLM providers',
  },
  {
    href: '/projects',
    icon: FolderOpen,
    color: 'bg-purple-600/20 text-purple-400',
    title: 'All Projects',
    desc: 'Browse your research projects',
  },
];

export default function DashboardPage() {
  const { user } = useAuthStore();
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    projectsAPI.list()
      .then(setProjects)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (!mounted) return null;

  const projectCount = projects.length;
  const inProgress = projects.filter(p => p.current_stage && p.current_stage !== 'report').length;
  const completedCount = projects.filter(p => p.current_stage === 'report').length;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      <div className="p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8 animate-fade-in-down">
          <div className="flex items-center gap-3 mb-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600/20">
              <Brain size={16} className="text-brand-400" />
            </div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">
              Welcome back, {user?.name?.split(' ')[0]}
            </h1>
          </div>
          <p className="text-sm text-[var(--text-secondary)] ml-11">
            Continue your research or start something new.
          </p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-4 mb-8 animate-fade-in-up">
          {[
            { icon: BarChart3, label: 'Total Projects', value: projectCount, color: 'brand' },
            { icon: Activity, label: 'In Progress', value: inProgress, color: 'yellow' },
            { icon: FileText, label: 'Completed', value: completedCount, color: 'green' },
          ].map((stat, i) => (
            <div key={i} className="card flex items-center gap-4 hover:border-[var(--border-light)] transition-all">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg bg-${stat.color}-600/10 flex-shrink-0`}
                style={{ background: stat.color === 'brand' ? 'rgba(99,102,241,0.1)' : stat.color === 'yellow' ? 'rgba(245,158,11,0.1)' : 'rgba(16,185,129,0.1)' }}>
                <stat.icon size={18} className={stat.color === 'brand' ? 'text-brand-400' : stat.color === 'yellow' ? 'text-yellow-400' : 'text-emerald-400'} />
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--text-primary)]">{stat.value}</p>
                <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10 animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          {QUICK_ACTIONS.map((action, i) => (
            <Link key={i} href={action.href}
              className="card flex items-center gap-4 hover:border-brand-500/40 hover:bg-[var(--bg-hover)] transition-all group cursor-pointer">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${action.color}`}>
                <action.icon size={18} />
              </div>
              <div className="flex-1">
                <p className="font-medium text-sm text-[var(--text-primary)]">{action.title}</p>
                <p className="text-xs text-[var(--text-secondary)]">{action.desc}</p>
              </div>
              <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-brand-400 transition-colors" />
            </Link>
          ))}
        </div>

        {/* Recent Projects */}
        <div className="animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-brand-600/10">
                <Clock size={12} className="text-brand-400" />
              </div>
              <h2 className="font-semibold text-sm text-[var(--text-primary)]">Recent Projects</h2>
            </div>
            <Link href="/projects" className="text-xs text-brand-400 hover:text-brand-300 transition-colors flex items-center gap-1">
              View all <ArrowRight size={10} />
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="card animate-pulse h-[68px] opacity-50" />
              ))}
            </div>
          ) : projects.length === 0 ? (
            <div className="card text-center py-12">
              <div className="flex justify-center mb-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600/10">
                  <Sparkles size={24} className="text-brand-400" />
                </div>
              </div>
              <p className="text-sm font-medium text-[var(--text-primary)] mb-1">No projects yet</p>
              <p className="text-xs text-[var(--text-muted)] mb-5 max-w-xs mx-auto">
                Describe your research idea and let AI guide you through papers, gaps, ideas, and paper writing.
              </p>
              <Link href="/projects/new" className="btn-primary text-xs">
                <Plus size={14} /> Start Your First Project
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {projects.slice(0, 5).map((project) => {
                const StageIcon = STAGE_ICONS[project.current_stage] || BookOpen;
                return (
                  <Link key={project.id} href={`/projects/${project.id}`}
                    className="card flex items-center gap-4 hover:border-brand-500/30 hover:bg-[var(--bg-hover)] transition-all cursor-pointer group py-4">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/10 flex-shrink-0">
                      <StageIcon size={15} className="text-brand-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[var(--text-primary)] truncate">{project.title}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={STAGE_COLORS[project.current_stage] || 'badge-blue'}>
                          {project.current_stage}
                        </span>
                        <span className="flex items-center gap-1 text-[11px] text-[var(--text-muted)]">
                          <Clock size={10} />
                          {project.updated_at
                            ? formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })
                            : 'recently'}
                        </span>
                      </div>
                    </div>
                    <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-brand-400 transition-colors flex-shrink-0" />
                  </Link>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
