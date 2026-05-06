'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import { useAuthStore } from '@/store/useAuthStore';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted && !isAuthenticated()) {
      router.replace('/auth/login');
    }
  }, [mounted, isAuthenticated, router]);

  if (!mounted) return null;
  if (!isAuthenticated()) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="ml-60 flex-1 min-h-screen overflow-auto">
        {children}
      </main>
    </div>
  );
}
