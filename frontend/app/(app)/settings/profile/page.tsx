'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/store/useAuthStore';
import { authAPI } from '@/services/api';
import { User, Save, Loader2, Check } from 'lucide-react';

const SKILL_LEVELS = ['beginner', 'intermediate', 'advanced'];

export default function ProfilePage() {
  const { user, setAuth, accessToken, refreshToken } = useAuthStore();
  const [mounted, setMounted] = useState(false);
  const [form, setForm] = useState({
    name: user?.name || '',
    skill_level: user?.skill_level || 'intermediate',
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (user) {
      setForm({
        name: user.name || '',
        skill_level: user.skill_level || 'intermediate',
      });
    }
  }, [user]);

  if (!mounted) return null;

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const updated = await authAPI.updateMe(form);
      if (accessToken && refreshToken) {
        setAuth(updated, accessToken, refreshToken);
      }
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-8 max-w-xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/20">
          <User size={18} className="text-brand-400" />
        </div>
        <h1 className="text-2xl font-bold text-[var(--text-primary)]">Profile</h1>
      </div>

      <div className="card mb-4">
        <div className="flex items-center gap-4 mb-6">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-2xl font-bold">
            {user?.name?.charAt(0).toUpperCase()}
          </div>
          <div>
            <p className="font-semibold text-[var(--text-primary)]">{user?.name}</p>
            <p className="text-sm text-[var(--text-muted)]">{user?.email}</p>
          </div>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Full Name</label>
            <input
              type="text" className="input"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Experience Level</label>
            <div className="flex gap-2">
              {SKILL_LEVELS.map((level) => (
                <button
                  key={level} type="button"
                  onClick={() => setForm({ ...form, skill_level: level })}
                  className={`flex-1 rounded-lg border py-2 text-xs font-medium capitalize transition-all ${
                    form.skill_level === level
                      ? 'border-brand-500 bg-brand-600/10 text-brand-400'
                      : 'border-[var(--border)] text-[var(--text-secondary)] hover:border-[var(--text-muted)]'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button type="submit" className="btn-primary" disabled={saving}>
              {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
            {saved && (
              <span className="flex items-center gap-1 text-xs text-emerald-400">
                <Check size={12} /> Saved!
              </span>
            )}
          </div>
        </form>
      </div>

      <div className="card">
        <p className="text-xs font-medium text-[var(--text-secondary)] mb-1">Account Info</p>
        <p className="text-xs text-[var(--text-muted)]">Email: {user?.email}</p>
        <p className="text-xs text-[var(--text-muted)] mt-1">Member since account creation</p>
      </div>
    </div>
  );
}
