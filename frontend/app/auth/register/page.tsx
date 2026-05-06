'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Brain, Eye, EyeOff, Loader2, Check } from 'lucide-react';
import { authAPI } from '@/services/api';
import { useAuthStore } from '@/store/useAuthStore';

const SKILL_LEVELS = [
  { value: 'beginner', label: 'Beginner', desc: 'New to ML/research' },
  { value: 'intermediate', label: 'Intermediate', desc: 'Some experience' },
  { value: 'advanced', label: 'Advanced', desc: 'Experienced researcher' },
];

export default function RegisterPage() {
  const router = useRouter();
  const setAuth = useAuthStore((s) => s.setAuth);
  const [form, setForm] = useState({
    name: '', email: '', password: '', skill_level: 'intermediate',
  });
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const passwordStrength = form.password.length >= 12
    ? 'strong' : form.password.length >= 8 ? 'medium' : 'weak';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    if (form.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    setLoading(true);
    try {
      const data = await authAPI.register(form);
      setAuth(data.user, data.access_token, data.refresh_token);
      router.push('/settings/llm');
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg).join(', '));
      } else {
        setError(detail || 'Registration failed. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--bg-primary)] p-4">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center mb-8">
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 mb-3">
            <Brain size={24} className="text-white" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">Create account</h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">Join ResearchIDE</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Full Name</label>
              <input
                type="text" className="input" placeholder="Your Name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required autoFocus
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Email</label>
              <input
                type="email" className="input" placeholder="you@example.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                required
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  className="input pr-10" placeholder="Min 8 characters"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  required
                />
                <button type="button" onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">
                  {showPassword ? <EyeOff size={14} /> : <Eye size={14} />}
                </button>
              </div>
              {form.password && (
                <div className="mt-1.5 flex gap-1">
                  {['weak', 'medium', 'strong'].map((level) => (
                    <div key={level} className={`h-1 flex-1 rounded-full transition-colors ${
                      passwordStrength === 'weak' && level === 'weak' ? 'bg-red-500' :
                      passwordStrength === 'medium' && ['weak','medium'].includes(level) ? 'bg-yellow-500' :
                      passwordStrength === 'strong' ? 'bg-emerald-500' : 'bg-[var(--border)]'
                    }`} />
                  ))}
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Experience Level</label>
              <div className="grid grid-cols-3 gap-2">
                {SKILL_LEVELS.map((sl) => (
                  <button
                    key={sl.value} type="button"
                    onClick={() => setForm({ ...form, skill_level: sl.value })}
                    className={`relative rounded-lg border p-2.5 text-left text-xs transition-all ${
                      form.skill_level === sl.value
                        ? 'border-brand-500 bg-brand-600/10 text-brand-400'
                        : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--text-muted)]'
                    }`}
                  >
                    {form.skill_level === sl.value && (
                      <Check size={10} className="absolute top-1.5 right-1.5 text-brand-400" />
                    )}
                    <div className="font-medium">{sl.label}</div>
                    <div className="text-[10px] mt-0.5 opacity-70">{sl.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            <button type="submit" className="btn-primary w-full justify-center" disabled={loading}>
              {loading && <Loader2 size={14} className="animate-spin" />}
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>

          <p className="mt-4 text-center text-xs text-[var(--text-muted)]">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-brand-400 hover:text-brand-300">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
