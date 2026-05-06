'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, FolderOpen, Trash2, ChevronRight, Clock, Loader2 } from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';

const STAGE_LABELS: Record<string, string> = {
  input: 'Input', papers: 'Papers', gaps: 'Gaps',
  ideas: 'Ideas', planner: 'Planning', code: 'Code', report: 'Report',
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    projectsAPI.list().then(setProjects).finally(() => setLoading(false));
  }, []);

  const handleDelete = async (projectId: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (!confirm('Delete this project?')) return;
    setDeleting(projectId);
    try {
      await projectsAPI.delete(projectId);
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (e) {
      console.error(e);
    } finally {
      setDeleting(null);
    }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Projects</h1>
        <Link href="/projects/new" className="btn-primary">
          <Plus size={14} /> New Project
        </Link>
      </div>

      {projects.length === 0 ? (
        <div className="card text-center py-16">
          <FolderOpen size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No projects yet</p>
          <Link href="/projects/new" className="btn-primary mt-4 inline-flex">
            <Plus size={14} /> Create first project
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {projects.map((project) => (
            <Link
              key={project.id}
              href={`/projects/${project.id}/${project.current_stage || 'input'}`}
              className="card flex items-center gap-4 hover:border-brand-500/30 hover:bg-[var(--bg-hover)] transition-all cursor-pointer group"
            >
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600/10 flex-shrink-0">
                <FolderOpen size={16} className="text-brand-400" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-medium text-sm text-[var(--text-primary)] truncate">{project.title}</p>
                <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-1">{project.input_text}</p>
                <div className="flex items-center gap-2 mt-1.5">
                  <span className="badge-blue">{STAGE_LABELS[project.current_stage] || project.current_stage}</span>
                  <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Clock size={10} />
                    {formatDistanceToNow(new Date(project.updated_at), { addSuffix: true })}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={(e) => handleDelete(project.id, e)}
                  className="p-1.5 text-[var(--text-muted)] hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                  disabled={deleting === project.id}
                >
                  {deleting === project.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                </button>
                <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-brand-400 transition-colors" />
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
