'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { projectsAPI } from '@/services/api';
import { Loader2 } from 'lucide-react';

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  useEffect(() => {
    if (!id) { router.replace('/projects'); return; }
    projectsAPI.get(id)
      .then((project) => {
        const stage = project?.current_stage || 'input';
        router.replace(`/projects/${id}/${stage}`);
      })
      .catch((err) => {
        // Invalid project ID or unauthorized — redirect to projects list
        console.error('Project not found:', err);
        router.replace('/projects');
      });
  }, [id, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <Loader2 size={24} className="animate-spin text-brand-400" />
        <p className="text-xs text-[var(--text-muted)]">Loading project...</p>
      </div>
    </div>
  );
}
