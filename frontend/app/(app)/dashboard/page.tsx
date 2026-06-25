'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  Plus, FolderOpen, ChevronRight, Clock, Cpu, BookOpen,
  Lightbulb, Code2, FileText, Brain, Sparkles, Activity,
  BarChart3, ArrowRight, Search, Target, Database,
  FlaskConical, BookOpenCheck, CheckCircle2,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { formatDistanceToNow } from 'date-fns';

const STAGE_ICONS: Record<string, React.ElementType> = {
  analysis: Brain, papers: BookOpen, gaps: Search,
  objectives: Target, planner: Cpu, data: Database, code: Code2,
  experiments: FlaskConical, results: BarChart3, guide: BookOpenCheck,
  report: FileText, publish: CheckCircle2,
  input: Brain, ideas: Lightbulb,
};

const STAGE_COLORS: Record<string, string> = {
  analysis: 'badge-blue', papers: 'badge-blue', gaps: 'badge-yellow',
  objectives: 'badge-purple', planner: 'badge-purple', data: 'badge-green',
  code: 'badge-green', experiments: 'badge-yellow', results: 'badge-blue',
  guide: 'badge-purple', report: 'badge-green', publish: 'badge-green',
  input: 'badge-blue', ideas: 'badge-purple',
};

const QUICK_ACTIONS = [
  {
    href: '/projects/new',
    icon: Plus,
    color: 'bg-emerald-600/20 text-emerald-400',
    hoverColor: 'group-hover:bg-emerald-600/30',
    title: 'New Project',
    desc: 'Start from a research question',
  },
  {
    href: '/settings/llm',
    icon: Cpu,
    color: 'bg-blue-600/20 text-blue-400',
    hoverColor: 'group-hover:bg-blue-600/30',
    title: 'AI Settings',
    desc: 'Configure LLM providers',
  },
  {
    href: '/projects',
    icon: FolderOpen,
    color: 'bg-purple-600/20 text-purple-400',
    hoverColor: 'group-hover:bg-purple-600/30',
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
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600/20">
              <Brain size={16} className="text-emerald-400" />
            </div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-heading)' }}>
              Welcome back, {user?.name?.split(' ')[0]}
            </h1>
          </div>
          <p className="text-sm text-[var(--text-secondary)] ml-11">
            Continue your research or start something new.
          </p>
        </div>

        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          {[
            { icon: BarChart3, label: 'Total Projects', value: projectCount, bg: 'rgba(34,197,94,0.1)', text: 'text-emerald-400' },
            { icon: Activity, label: 'In Progress', value: inProgress, bg: 'rgba(245,158,11,0.1)', text: 'text-yellow-400' },
            { icon: FileText, label: 'Completed', value: completedCount, bg: 'rgba(59,130,246,0.1)', text: 'text-blue-400' },
          ].map((stat, i) => (
            <div key={i} className="card flex items-center gap-4 hover:border-emerald-500/30 transition-all duration-200 cursor-pointer">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg flex-shrink-0" style={{ background: stat.bg }}>
                <stat.icon size={18} className={stat.text} />
              </div>
              <div>
                <p className="text-2xl font-bold text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-heading)' }}>{stat.value}</p>
                <p className="text-xs text-[var(--text-muted)]">{stat.label}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
          {QUICK_ACTIONS.map((action, i) => (
            <Link key={i} href={action.href}
              className="card flex items-center gap-4 hover:border-emerald-500/40 hover:bg-[var(--bg-hover)] transition-all duration-200 group cursor-pointer">
              <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${action.color} ${action.hoverColor} transition-all duration-200`}>
                <action.icon size={18} />
              </div>
              <div className="flex-1">
                <p className="font-medium text-sm text-[var(--text-primary)]">{action.title}</p>
                <p className="text-xs text-[var(--text-secondary)]">{action.desc}</p>
              </div>
              <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-emerald-400 transition-colors duration-200" />
            </Link>
          ))}
        </div>

        {/* Recent Projects */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <div className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-600/10">
                <Clock size={12} className="text-emerald-400" />
              </div>
              <h2 className="font-semibold text-sm text-[var(--text-primary)]" style={{ fontFamily: 'var(--font-heading)' }}>Recent Projects</h2>
            </div>
            <Link href="/projects" className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors duration-200 flex items-center gap-1 cursor-pointer">
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
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-600/10">
                  <Sparkles size={24} className="text-emerald-400" />
                </div>
              </div>
              <p className="text-sm font-medium text-[var(--text-primary)] mb-1" style={{ fontFamily: 'var(--font-heading)' }}>No projects yet</p>
              <p className="text-xs text-[var(--text-muted)] mb-5 max-w-xs mx-auto">
                Describe your research idea and let AI guide you through all 13 research steps — from NLP analysis to publication.
              </p>
              <Link href="/projects/new" className="btn-primary text-xs cursor-pointer">
                <Plus size={14} /> Start Your First Project
              </Link>
            </div>
          ) : (
            <div className="space-y-2">
              {projects.slice(0, 5).map((project) => {
                const StageIcon = STAGE_ICONS[project.current_stage] || BookOpen;
                return (
                  <Link key={project.id} href={`/projects/${project.id}`}
                    className="card flex items-center gap-4 hover:border-emerald-500/30 hover:bg-[var(--bg-hover)] transition-all duration-200 cursor-pointer group py-4">
                    <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600/10 flex-shrink-0">
                      <StageIcon size={15} className="text-emerald-400" />
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
                    <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-emerald-400 transition-colors duration-200 flex-shrink-0" />
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
