'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard, FolderOpen, Plus, Settings, LogOut,
  Brain, ChevronRight, Cpu,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import clsx from 'clsx';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: FolderOpen },
  { href: '/settings/llm', label: 'AI Settings', icon: Cpu },
  { href: '/settings/profile', label: 'Profile', icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuthStore();

  const handleLogout = () => {
    logout();
    router.push('/auth/login');
  };

  return (
    <aside className="fixed left-0 top-0 h-screen w-60 border-r border-[var(--border)] bg-[var(--bg-secondary)] flex flex-col z-40">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[var(--border)]">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
          <Brain size={16} />
        </div>
        <span className="font-semibold text-[var(--text-primary)]">ResearchIDE</span>
      </div>

      {/* New Project Button */}
      <div className="px-3 py-3">
        <Link
          href="/projects/new"
          className="btn-primary w-full justify-center text-xs"
        >
          <Plus size={14} />
          New Project
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-2 space-y-1 overflow-y-auto">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx('sidebar-item', pathname.startsWith(href) && 'active')}
          >
            <Icon size={16} />
            {label}
          </Link>
        ))}
      </nav>

      {/* User Section */}
      <div className="border-t border-[var(--border)] p-3">
        <div className="flex items-center gap-3 rounded-lg px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-semibold flex-shrink-0">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-[var(--text-primary)] truncate">{user?.name}</p>
            <p className="text-xs text-[var(--text-muted)] truncate">{user?.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-[var(--text-muted)] hover:text-[var(--danger)] transition-colors"
            title="Logout"
          >
            <LogOut size={14} />
          </button>
        </div>
      </div>
    </aside>
  );
}
