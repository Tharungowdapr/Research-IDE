'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Plus, FolderOpen, Trash2, ChevronRight, Clock, Loader2, Search, Filter } from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { formatDistanceToNow } from 'date-fns';

const STAGES = ['all', 'input', 'papers', 'gaps', 'ideas', 'planner', 'code', 'report'];
const STAGE_COLORS: Record<string, string> = {
  input: 'badge-blue', papers: 'badge-blue', gaps: 'badge-yellow',
  ideas: 'badge-purple', planner: 'badge-purple', code: 'badge-green', report: 'badge-green',
};

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [stageFilter, setStageFilter] = useState('all');

  useEffect(() => {
    projectsAPI.list().then(setProjects).finally(() => setLoading(false));
  }, []);

  const filtered = useMemo(() => {
    return projects.filter(p => {
      const matchSearch = !search ||
        p.title?.toLowerCase().includes(search.toLowerCase()) ||
        p.input_text?.toLowerCase().includes(search.toLowerCase());
      const matchStage = stageFilter === 'all' || p.current_stage === stageFilter;
      return matchSearch && matchStage;
    });
  }, [projects, search, stageFilter]);

  const handleDelete = async (projectId: string, e: React.MouseEvent) => {
    e.preventDefault();
    if (!confirm('Delete this project and all its outputs?')) return;
    setDeleting(projectId);
    try {
      await projectsAPI.delete(projectId);
      setProjects(prev => prev.filter(p => p.id !== projectId));
    } catch (e) { console.error(e); }
    finally { setDeleting(null); }
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-brand-400" /></div>;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-6 flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Projects</h1>
        <Link href="/projects/new" className="btn-primary"><Plus size={14} /> New Project</Link>
      </div>

      {/* Search + Filter bar */}
      {projects.length > 0 && (
        <div className="flex gap-3 mb-5 flex-wrap">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={13} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              type="text"
              className="input pl-8 text-xs"
              placeholder="Search projects..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div className="flex items-center gap-1.5 flex-wrap">
            <Filter size={12} className="text-[var(--text-muted)]" />
            {STAGES.map(stage => (
              <button
                key={stage}
                onClick={() => setStageFilter(stage)}
                className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-all capitalize ${
                  stageFilter === stage
                    ? 'bg-brand-600/20 text-brand-400 border border-brand-500/30'
                    : 'text-[var(--text-muted)] hover:text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]'
                }`}
              >
                {stage === 'all' ? `All (${projects.length})` : stage}
              </button>
            ))}
          </div>
        </div>
      )}

      {filtered.length === 0 ? (
        <div className="card text-center py-16">
          <FolderOpen size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">
            {search || stageFilter !== 'all' ? 'No projects match your filter' : 'No projects yet'}
          </p>
          {!search && stageFilter === 'all' && (
            <Link href="/projects/new" className="btn-primary mt-4 inline-flex"><Plus size={14} /> Create first project</Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map(project => (
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
                  <span className={STAGE_COLORS[project.current_stage] || 'badge-blue'}>{project.current_stage}</span>
                  <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Clock size={10} />
                    {project.updated_at ? formatDistanceToNow(new Date(project.updated_at), { addSuffix: true }) : 'just now'}
                  </span>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0">
                <button
                  onClick={e => handleDelete(project.id, e)}
                  className="p-1.5 text-[var(--text-muted)] hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                  disabled={deleting === project.id}
                >
                  {deleting === project.id ? <Loader2 size={14} className="animate-spin" /> : <Trash2 size={14} />}
                </button>
                <ChevronRight size={14} className="text-[var(--text-muted)] group-hover:text-brand-400 transition-colors" />
              </div>
            </Link>
          ))}
          {filtered.length < projects.length && (
            <p className="text-xs text-center text-[var(--text-muted)] pt-2">
              Showing {filtered.length} of {projects.length} projects
            </p>
          )}
        </div>
      )}
    </div>
  );
}
