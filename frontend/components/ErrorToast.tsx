'use client';

import { useEffect, useState } from 'react';
import { X, AlertCircle, CheckCircle, Info, AlertTriangle } from 'lucide-react';

interface Toast {
  id: number;
  message: string;
  type: 'error' | 'success' | 'info' | 'warning';
}

let toastCount = 0;
const listeners: ((toasts: Toast[]) => void)[] = [];
let toasts: Toast[] = [];

export function showToast(message: string, type: Toast['type'] = 'info') {
  const toast: Toast = {
    id: ++toastCount,
    message,
    type,
  };
  toasts = [...toasts, toast];
  listeners.forEach(fn => fn(toasts));
  
  // Auto remove after 5 seconds
  setTimeout(() => {
    toasts = toasts.filter(t => t.id !== toast.id);
    listeners.forEach(fn => fn(toasts));
  }, 5000);
}

export default function ErrorToast() {
  const [localToasts, setLocalToasts] = useState<Toast[]>([]);

  useEffect(() => {
    listeners.push(setLocalToasts);
    return () => {
      const idx = listeners.indexOf(setLocalToasts);
      if (idx > -1) listeners.splice(idx, 1);
    };
  }, []);

  const removeToast = (id: number) => {
    toasts = toasts.filter(t => t.id !== id);
    setLocalToasts([...toasts]);
  };

  const getIcon = (type: Toast['type']) => {
    switch (type) {
      case 'error': return <AlertCircle size={16} className="text-red-400" />;
      case 'success': return <CheckCircle size={16} className="text-green-400" />;
      case 'warning': return <AlertTriangle size={16} className="text-yellow-400" />;
      default: return <Info size={16} className="text-blue-400" />;
    }
  };

  const getBgColor = (type: Toast['type']) => {
    switch (type) {
      case 'error': return 'bg-red-500/10 border-red-500/20';
      case 'success': return 'bg-green-500/10 border-green-500/20';
      case 'warning': return 'bg-yellow-500/10 border-yellow-500/20';
      default: return 'bg-blue-500/10 border-blue-500/20';
    }
  };

  if (localToasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-50 flex flex-col gap-2 max-w-md">
      {localToasts.map(toast => (
        <div
          key={toast.id}
          className={`flex items-center gap-2 p-3 rounded-lg border ${getBgColor(toast.type)} animate-slide-in`}
        >
          {getIcon(toast.type)}
          <p className="flex-1 text-sm text-[var(--text-primary)]">{toast.message}</p>
          <button onClick={() => removeToast(toast.id)} className="text-[var(--text-muted)] hover:text-[var(--text-primary)]">
            <X size={14} />
          </button>
        </div>
      ))}
    </div>
  );
}
