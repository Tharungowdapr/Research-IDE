'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sidebar } from '@/components/layout/Sidebar';
import { useAuthStore } from '@/store/useAuthStore';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const [isMounted, setIsMounted] = useState(false);

  useEffect(() => {
    setIsMounted(true);
    if (!isAuthenticated()) {
      router.replace('/auth/login');
    }
  }, [isAuthenticated, router]);

  if (!isMounted) {
    return null; // Return null on server, matching initial client render until mounted
  }

  if (!isAuthenticated()) return null;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <main className="lg:ml-60 flex-1 min-h-screen overflow-auto">
        {children}
      </main>
    </div>
  );
}

