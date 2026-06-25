'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { projectsAPI } from '@/services/api';
import { Loader2 } from 'lucide-react';

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  useEffect(() => {
    const STAGE_MAP: Record<string, string> = {
      input: 'analysis', ideas: 'ideas',
    };

    projectsAPI.get(id)
      .then((project) => {
        const raw = project.current_stage || 'input';
        const stage = STAGE_MAP[raw] || raw;
        router.replace(`/projects/${id}/${stage}`);
      })
      .catch(() => {
        router.replace('/projects');
      });
  }, [id, router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 size={24} className="animate-spin text-brand-400" />
    </div>
  );
}
