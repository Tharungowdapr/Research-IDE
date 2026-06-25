'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function InputRedirect() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();

  useEffect(() => {
    router.replace(`/projects/${id}/analysis`);
  }, [id, router]);

  return null;
}
