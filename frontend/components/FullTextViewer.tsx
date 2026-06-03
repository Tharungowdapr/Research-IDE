'use client';

import React, { useState, useCallback } from 'react';
import { X, Download, Copy, Search, Loader2, AlertCircle } from 'lucide-react';

interface FullTextViewerProps {
    paperId: string;
    projectId: string;
    title: string;
    onClose: () => void;
}

export const FullTextViewer: React.FC<FullTextViewerProps> = ({
    paperId,
    projectId,
    title,
    onClose,
}) => {
    const [fullText, setFullText] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [searchTerm, setSearchTerm] = useState('');

    React.useEffect(() => {
        const fetchFullText = async () => {
            try {
                setLoading(true);
                setError(null);
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
                const token = localStorage.getItem('research-ide-auth')
                    ? JSON.parse(localStorage.getItem('research-ide-auth')!)?.state?.accessToken || ''
                    : '';

                const response = await fetch(`${apiUrl}/api/projects/${projectId}/papers/${paperId}/full-text`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error(`Failed to fetch full text: ${response.statusText}`);
                }

                const data = await response.json();
                setFullText(data.full_text || 'No full text available');
            } catch (err) {
                setError(err instanceof Error ? err.message : 'Unknown error');
                setFullText('');
            } finally {
                setLoading(false);
            }
        };
        fetchFullText();
    }, [paperId, projectId]);

    const highlightText = (text: string, term: string) => {
        if (!term) return text;
        const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        const parts = text.split(regex);
        return parts.map((part, index) =>
            regex.test(part)
                ? `<mark class="bg-yellow-500/30 text-[var(--text-primary)] rounded px-0.5">${part}</mark>`
                : part
        ).join('');
    };

    const copyToClipboard = () => {
        navigator.clipboard.writeText(fullText);
    };

    const downloadAsText = () => {
        const element = document.createElement('a');
        element.setAttribute(
            'href',
            'data:text/plain;charset=utf-8,' + encodeURIComponent(fullText)
        );
        element.setAttribute('download', `${title.replace(/\s+/g, '_')}_fulltext.txt`);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    };

    return (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 p-4">
            <div className="bg-[var(--bg-card)] rounded-xl shadow-2xl max-w-4xl w-full h-[90vh] flex flex-col border border-[var(--border)]">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
                    <div className="flex-1 min-w-0">
                        <h2 className="text-lg font-bold text-[var(--text-primary)] truncate">{title}</h2>
                        <p className="text-xs text-[var(--text-muted)] mt-0.5">Full Text</p>
                    </div>
                    <button onClick={onClose} className="p-1.5 hover:bg-[var(--bg-hover)] rounded-lg transition ml-2">
                        <X size={18} className="text-[var(--text-muted)]" />
                    </button>
                </div>

                {/* Search Bar */}
                <div className="px-4 py-2.5 border-b border-[var(--border)] bg-[var(--bg-secondary)] flex items-center gap-2">
                    <Search size={14} className="text-[var(--text-muted)] flex-shrink-0" />
                    <input
                        type="text"
                        placeholder="Search in text..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="flex-1 bg-transparent text-xs text-[var(--text-primary)] placeholder-[var(--text-muted)] outline-none"
                    />
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-4">
                    {loading ? (
                        <div className="flex items-center justify-center h-full gap-2">
                            <Loader2 size={20} className="animate-spin text-brand-400" />
                            <p className="text-sm text-[var(--text-secondary)]">Loading full text...</p>
                        </div>
                    ) : error ? (
                        <div className="flex flex-col items-center justify-center h-full gap-2">
                            <AlertCircle size={24} className="text-red-400" />
                            <p className="text-sm text-red-400">Error loading full text</p>
                            <p className="text-xs text-[var(--text-muted)]">{error}</p>
                        </div>
                    ) : (
                        <div
                            className="text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap"
                            dangerouslySetInnerHTML={{
                                __html: highlightText(fullText, searchTerm)
                            }}
                        />
                    )}
                </div>

                {/* Footer Actions */}
                <div className="px-4 py-3 border-t border-[var(--border)] bg-[var(--bg-secondary)] flex justify-end gap-2">
                    <button
                        onClick={copyToClipboard}
                        disabled={!fullText || loading}
                        className="btn-ghost text-xs flex items-center gap-1.5"
                    >
                        <Copy size={13} /> Copy
                    </button>
                    <button
                        onClick={downloadAsText}
                        disabled={!fullText || loading}
                        className="btn-primary text-xs flex items-center gap-1.5"
                    >
                        <Download size={13} /> Download
                    </button>
                </div>
            </div>
        </div>
    );
};

export default FullTextViewer;
