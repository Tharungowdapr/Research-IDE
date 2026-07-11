'use client';

import React, { useState } from 'react';
import { BookOpen, RefreshCw, Download, Loader2, AlertCircle } from 'lucide-react';

interface LiteratureReviewProps {
    projectId: string;
}

interface ReviewData {
    title?: string;
    introduction?: string;
    themes?: { name: string; description: string; papers: string[]; key_findings: string }[];
    methodology_comparison?: string;
    gaps_identified?: string[];
    future_directions?: string[];
    conclusion?: string;
}

export const LiteratureReview: React.FC<LiteratureReviewProps> = ({ projectId }) => {
    const [review, setReview] = useState<ReviewData | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [bibliography, setBibliography] = useState<string[]>([]);

    const token = typeof window !== 'undefined'
        ? (() => {
            try {
                const stored = localStorage.getItem('research-ide-auth');
                if (stored) return JSON.parse(stored)?.state?.accessToken || '';
            } catch { }
            return '';
        })()
        : '';

    const generateReview = async () => {
        try {
            setLoading(true);
            setError(null);
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

            const reviewResponse = await fetch(`${apiUrl}/api/agents/${projectId}/literature-review`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (!reviewResponse.ok) {
                const errData = await reviewResponse.json().catch(() => ({}));
                throw new Error(errData.detail || 'Failed to generate literature review');
            }

            const reviewData = await reviewResponse.json();
            setReview(reviewData);

            const bibResponse = await fetch(`${apiUrl}/api/agents/${projectId}/annotated-bibliography`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
            });

            if (bibResponse.ok) {
                const bibData = await bibResponse.json();
                setBibliography(bibData.annotations || []);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    };

    const downloadAsMarkdown = () => {
        if (!review) return;

        let markdown = '# Literature Review\n\n';

        if (review.introduction) {
            markdown += `## Introduction\n\n${review.introduction}\n\n`;
        }

        if (review.themes && review.themes.length > 0) {
            markdown += '## Research Themes\n\n';
            review.themes.forEach((theme, i) => {
                markdown += `### ${i + 1}. ${theme.name}\n`;
                markdown += `${theme.description}\n\n`;
                if (theme.key_findings) markdown += `Key findings: ${theme.key_findings}\n\n`;
                if (theme.papers.length > 0) markdown += `Papers: ${theme.papers.join(', ')}\n\n`;
            });
        }

        if (review.methodology_comparison) {
            markdown += `## Methodology Comparison\n\n${review.methodology_comparison}\n\n`;
        }

        if (review.gaps_identified && review.gaps_identified.length > 0) {
            markdown += '## Research Gaps\n\n';
            review.gaps_identified.forEach((gap, i) => { markdown += `${i + 1}. ${gap}\n`; });
            markdown += '\n';
        }

        if (review.future_directions && review.future_directions.length > 0) {
            markdown += '## Future Directions\n\n';
            review.future_directions.forEach((direction, i) => { markdown += `${i + 1}. ${direction}\n`; });
            markdown += '\n';
        }

        if (review.conclusion) {
            markdown += `## Conclusion\n\n${review.conclusion}\n\n`;
        }

        if (bibliography.length > 0) {
            markdown += '## Annotated Bibliography\n\n';
            bibliography.forEach((entry: any, i) => {
                const summary = entry.summary || '';
                markdown += `[${i + 1}] ${entry.citation || ''}\n   ${summary}\n\n`;
            });
        }

        const blob = new Blob([markdown], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `literature_review_${projectId}.md`;
        a.click();
        URL.revokeObjectURL(url);
    };

    return (
        <div className="card p-5">
            <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-2.5">
                    <BookOpen size={22} className="text-brand-400" />
                    <div>
                        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Literature Review</h3>
                        <p className="text-xs text-[var(--text-muted)]">Automated review generated from your papers</p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {review && (
                        <button onClick={downloadAsMarkdown} className="btn-ghost text-xs flex items-center gap-1.5">
                            <Download size={13} /> Download
                        </button>
                    )}
                    <button
                        onClick={generateReview}
                        disabled={loading}
                        className="btn-primary text-xs flex items-center gap-1.5"
                    >
                        {loading ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />}
                        {loading ? 'Generating...' : 'Generate Review'}
                    </button>
                </div>
            </div>

            {error && (
                <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-3 py-2 text-xs text-red-400 flex items-center gap-1.5">
                    <AlertCircle size={12} /> {error}
                </div>
            )}

            {!review && !loading && (
                <div className="text-center py-10 text-[var(--text-muted)]">
                    <BookOpen size={36} className="mx-auto mb-2 opacity-40" />
                    <p className="text-sm">No literature review generated yet.</p>
                    <p className="text-xs mt-1">Click &quot;Generate Review&quot; to create one from your papers.</p>
                </div>
            )}

            {review && (
                <div className="space-y-6">
                    {review.introduction && (
                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{String(review.introduction)}</p>
                    )}

                    {review.themes && review.themes.length > 0 && (
                        <section>
                            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">Research Themes</h4>
                            <div className="space-y-2">
                                {review.themes.map((theme: any, i: number) => (
                                    <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                                        <p className="text-xs font-semibold text-[var(--text-primary)] mb-1">{String(theme.name || '')}</p>
                                        <p className="text-xs text-[var(--text-secondary)]">{String(theme.description || '')}</p>
                                        {theme.key_findings && (
                                            <p className="text-xs text-brand-400 mt-1">Key findings: {String(theme.key_findings)}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}

                    {review.methodology_comparison && (
                        <section>
                            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">Methodology Comparison</h4>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{String(review.methodology_comparison)}</p>
                        </section>
                    )}

                    {review.gaps_identified && review.gaps_identified.length > 0 && (
                        <section>
                            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">Research Gaps</h4>
                            <ul className="space-y-1">
                                {review.gaps_identified.map((gap: any, i: number) => {
                                    const text = typeof gap === 'string' ? gap
                                        : typeof gap === 'object' ? (gap?.gap || JSON.stringify(gap))
                                        : String(gap);
                                    return (
                                    <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                                        <span className="text-yellow-400 flex-shrink-0">•</span>
                                        <span>{text}</span>
                                    </li>
                                    );
                                })}
                            </ul>
                        </section>
                    )}

                    {review.future_directions && review.future_directions.length > 0 && (
                        <section>
                            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">Future Directions</h4>
                            <ul className="space-y-1">
                                {review.future_directions.map((dir: any, i: number) => {
                                    const text = typeof dir === 'string' ? dir
                                        : typeof dir === 'object' ? (dir?.direction || JSON.stringify(dir))
                                        : String(dir);
                                    return (
                                    <li key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                                        <span className="text-green-400 flex-shrink-0">→</span>
                                        <span>{text}</span>
                                    </li>
                                    );
                                })}
                            </ul>
                        </section>
                    )}

                    {review.conclusion && (
                        <section>
                            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">Conclusion</h4>
                            <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{String(review.conclusion)}</p>
                        </section>
                    )}

                    {bibliography.length > 0 && (
                        <section>
                            <h4 className="text-xs font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">Annotated Bibliography</h4>
                            <div className="space-y-2">
                                {bibliography.map((entry: any, i) => (
                                    <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                                        <p className="text-xs font-medium text-[var(--text-primary)] mb-1">{String(entry.citation || '')}</p>
                                        <p className="text-xs text-[var(--text-secondary)]">{String(entry.summary || '')}</p>
                                        {entry.relevance && (
                                            <p className="text-xs text-brand-400 mt-1">Relevance: {String(entry.relevance)}</p>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </section>
                    )}
                </div>
            )}
        </div>
    );
};

export default LiteratureReview;
