'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, FolderOpen, ChevronRight, Clock, Cpu, BookOpen, Lightbulb, Code2, FileText } from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';
import { formatDistanceToNow } from 'date-fns';

const STAGE_ICONS: Record<string, React.ElementType> = {
  input: BookOpen, papers: BookOpen, gaps: BookOpen,
  ideas: Lightbulb, planner: Cpu, code: Code2, report: FileText,
};

const STAGE_COLORS: Record<string, string> = {
  input: 'badge-blue', papers: 'badge-blue', gaps: 'badge-yellow',
  ideas: 'badge-purple', planner: 'badge-purple', code: 'badge-green', report: 'badge-green',
};

export default function DashboardPage() {
  const { user } = useAuthStore();
  const router = useRouter();
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    projectsAPI.list()
      .then(setProjects)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">
          Welcome back, {user?.name?.split(' ')[0]} 👋
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mt-1">
          Continue a project or start a new research journey.
        </p>
      </div>

      {/* Quick Start */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
        <Link href="/projects/new"
          className="card hover:border-brand-500/50 hover:bg-[var(--bg-hover)] transition-all group cursor-pointer">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/20">
              <Plus size={18} className="text-brand-400" />
            </div>
            <span className="font-medium text-[var(--text-primary)]">New Project</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">
            Start from a research question and let AI guide you to ideas and code.
          </p>
        </Link>

        <Link href="/settings/llm"
          className="card hover:border-brand-500/50 hover:bg-[var(--bg-hover)] transition-all cursor-pointer">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-emerald-600/20">
              <Cpu size={18} className="text-emerald-400" />
            </div>
            <span className="font-medium text-[var(--text-primary)]">AI Settings</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">
            Configure OpenAI, Anthropic, Groq, Gemini, or run Ollama locally.
          </p>
        </Link>

        <Link href="/projects"
          className="card hover:border-brand-500/50 hover:bg-[var(--bg-hover)] transition-all cursor-pointer">
          <div className="flex items-center gap-3 mb-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-purple-600/20">
              <FolderOpen size={18} className="text-purple-400" />
            </div>
            <span className="font-medium text-[var(--text-primary)]">All Projects</span>
          </div>
          <p className="text-xs text-[var(--text-secondary)]">
            Browse and resume all your research projects.
          </p>
        </Link>
      </div>

      {/* Recent Projects */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-semibold text-[var(--text-primary)]">Recent Projects</h2>
          <Link href="/projects" className="text-xs text-brand-400 hover:text-brand-300">
            View all
          </Link>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1,2,3].map(i => (
              <div key={i} className="card animate-pulse h-20 opacity-50" />
            ))}
          </div>
        ) : projects.length === 0 ? (
          <div className="card text-center py-12">
            <FolderOpen size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
            <p className="text-sm text-[var(--text-secondary)]">No projects yet</p>
            <p className="text-xs text-[var(--text-muted)] mt-1">Create your first project to get started</p>
            <Link href="/projects/new" className="btn-primary mt-4 inline-flex">
              <Plus size={14} /> New Project
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {projects.slice(0, 5).map((project) => {
              const StageIcon = STAGE_ICONS[project.current_stage] || BookOpen;
              return (
                <Link key={project.id} href={`/projects/${project.id}`}
                  className="card flex items-center gap-4 hover:border-brand-500/30 hover:bg-[var(--bg-hover)] transition-all cursor-pointer group">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600/10 flex-shrink-0">
                    <StageIcon size={16} className="text-brand-400" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm text-[var(--text-primary)] truncate">{project.title}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={STAGE_COLORS[project.current_stage] || 'badge-blue'}>
                        {project.current_stage}
                      </span>
                      <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                        <Clock size={10} />
                        {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
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
  );
}
