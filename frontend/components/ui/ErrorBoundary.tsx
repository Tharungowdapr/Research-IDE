'use client';

import React from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface State { hasError: boolean; error: string }

export class ErrorBoundary extends React.Component<
  { children: React.ReactNode; fallbackHref?: string },
  State
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: '' };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error: error.message };
  }

  render() {
    if (!this.state.hasError) return this.props.children;
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] text-center">
        <AlertTriangle size={32} className="text-yellow-400 mb-3" />
        <h2 className="font-semibold text-[var(--text-primary)] mb-1">Something went wrong</h2>
        <p className="text-xs text-[var(--text-muted)] mb-5 max-w-sm">{this.state.error}</p>
        <div className="flex gap-3">
          <button onClick={() => this.setState({ hasError: false, error: '' })} className="btn-secondary text-xs">
            <RefreshCw size={12} /> Try Again
          </button>
          <Link href={this.props.fallbackHref || '/projects'} className="btn-primary text-xs">
            Back to Projects
          </Link>
        </div>
      </div>
    );
  }
}
