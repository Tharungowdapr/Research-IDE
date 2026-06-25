'use client';

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard, FolderOpen, Plus, Settings, LogOut,
  Brain, Cpu, ChevronRight, Search, Users, Activity,
} from 'lucide-react';
import { useAuthStore } from '@/store/useAuthStore';
import { ThemeToggle } from '@/components/layout/ThemeToggle';
import clsx from 'clsx';

const navItems = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/projects', label: 'Projects', icon: FolderOpen },
];

const toolItems = [
  { href: '/settings/llm', label: 'AI Settings', icon: Cpu },
  { href: '/settings/system', label: 'System Monitor', icon: Activity },
  { href: '/settings/profile', label: 'Profile', icon: Users },
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
      <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[var(--border)]">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-lg shadow-emerald-600/20">
          <Brain size={16} />
        </div>
        <span className="font-semibold text-[var(--text-primary)] text-sm" style={{ fontFamily: 'var(--font-heading)' }}>ResearchIDE</span>
      </div>

      <div className="px-3 py-3">
        <Link href="/projects/new" className="btn-primary w-full justify-center text-xs">
          <Plus size={14} />
          New Project
        </Link>
      </div>

      <div className="px-3 mb-1">
        <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider px-3 py-1">
          Navigation
        </p>
      </div>
      <nav className="px-3 space-y-0.5">
        {navItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx('sidebar-item text-xs', pathname.startsWith(href) && 'active')}
          >
            <Icon size={15} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="px-3 mt-4 mb-1">
        <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase tracking-wider px-3 py-1">
          Settings
        </p>
      </div>
      <nav className="px-3 space-y-0.5">
        {toolItems.map(({ href, label, icon: Icon }) => (
          <Link
            key={href}
            href={href}
            className={clsx('sidebar-item text-xs', pathname.startsWith(href) && 'active')}
          >
            <Icon size={15} />
            {label}
          </Link>
        ))}
      </nav>

      <div className="flex-1" />

      <div className="border-t border-[var(--border)] p-3 space-y-2">
        <div className="flex items-center justify-between px-2">
          <span className="text-[10px] text-[var(--text-muted)]">Theme</span>
          <ThemeToggle />
        </div>
        <div className="flex items-center gap-3 rounded-lg px-2 py-2 hover:bg-[var(--bg-hover)] transition-colors duration-200 cursor-pointer">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600/20 text-emerald-400 text-xs font-semibold flex-shrink-0">
            {user?.name?.charAt(0).toUpperCase() || 'U'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-medium text-[var(--text-primary)] truncate">{user?.name || 'User'}</p>
            <p className="text-[10px] text-[var(--text-muted)] truncate">{user?.email || ''}</p>
          </div>
          <button
            onClick={handleLogout}
            className="text-[var(--text-muted)] hover:text-[var(--danger)] transition-colors duration-200 cursor-pointer"
            title="Logout"
          >
            <LogOut size={13} />
          </button>
        </div>
      </div>
    </aside>
  );
}
