'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuthStore } from '@/store/useAuthStore';
import {
  Brain, BookOpen, Search, Lightbulb, Cpu, BookOpenCheck,
  FileText, ArrowRight, ChevronDown, Menu, X, Github,
  Star, Users, FileCode2, Sparkles, Layers, Zap,
} from 'lucide-react';

const STEPS = [
  { icon: Brain, label: 'NLP Analysis', desc: 'Extract research intent and key concepts from your problem statement using LLMs.', color: 'from-blue-500 to-indigo-500' },
  { icon: BookOpen, label: 'Paper Explorer', desc: 'Automatically retrieve and analyze relevant papers from multiple sources.', color: 'from-indigo-500 to-purple-500' },
  { icon: Search, label: 'Gap Analysis', desc: 'Identify research gaps and under-explored areas with AI-powered literature analysis.', color: 'from-purple-500 to-pink-500' },
  { icon: Lightbulb, label: 'Idea Generation', desc: 'Generate novel research ideas ranked by feasibility, novelty, and impact.', color: 'from-pink-500 to-rose-500' },
  { icon: Cpu, label: 'Execution Plan', desc: 'Get a step-by-step research plan with methodology, timeline, and resource estimates.', color: 'from-rose-500 to-orange-500' },
  { icon: BookOpenCheck, label: 'Research Guide', desc: 'Generate comprehensive guides, presentations, and documented code.', color: 'from-orange-500 to-amber-500' },
  { icon: FileText, label: 'Paper Writing', desc: 'Export a complete research paper with citations in DOCX or PDF format.', color: 'from-amber-500 to-green-500' },
];

const FEATURES = [
  { icon: Layers, title: 'Multi-LLM Support', desc: 'Works with OpenAI, Anthropic, Groq, Gemini, Ollama, and more.' },
  { icon: FileCode2, title: 'Code Generation', desc: 'Get ready-to-run code with proper structure and documentation.' },
  { icon: Zap, title: 'Streaming Output', desc: 'Watch your research plan, code, and paper being generated in real-time.' },
  { icon: Star, title: 'Citation Management', desc: 'Zotero integration and automatic citation formatting for your papers.' },
];

const STATS = [
  { icon: Star, value: '7', label: 'Research Steps' },
  { icon: Users, value: '1000+', label: 'Active Researchers' },
  { icon: FileCode2, value: '10K+', label: 'Papers Analyzed' },
  { icon: Layers, value: '7', label: 'LLM Providers' },
];

function useHydrated() {
  const [hydrated, setHydrated] = useState(false);
  useEffect(() => { setHydrated(true); }, []);
  return hydrated;
}

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);
  const hydrated = useHydrated();
  const isAuthenticated = useAuthStore((s) => hydrated ? s.isAuthenticated() : false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const showAuth = hydrated && isAuthenticated;

  return (
    <div className="min-h-screen bg-[var(--bg-primary)]">
      {/* ─── Navbar ─── */}
      <nav className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${scrolled ? 'bg-[var(--bg-primary)]/90 backdrop-blur-xl border-b border-[var(--border)]' : 'bg-transparent'}`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
                <Brain size={16} />
              </div>
              <span className="font-semibold text-[var(--text-primary)]">ResearchIDE</span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <a href="#how-it-works" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">How It Works</a>
              <a href="#features" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">Features</a>
              <a href="#pipeline" className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">Pipeline</a>
            </div>

            <div className="hidden md:flex items-center gap-3">
              {showAuth ? (
                <Link href="/dashboard" className="btn-primary text-xs">
                  Dashboard <ArrowRight size={12} />
                </Link>
              ) : (
                <>
                  <Link href="/auth/login" className="btn-ghost text-xs">Sign In</Link>
                  <Link href="/auth/register" className="btn-primary text-xs">
                    Get Started <ArrowRight size={12} />
                  </Link>
                </>
              )}
            </div>

            <button className="md:hidden btn-icon" onClick={() => setMenuOpen(!menuOpen)}>
              {menuOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
          </div>
        </div>

        {menuOpen && (
          <div className="md:hidden border-t border-[var(--border)] bg-[var(--bg-primary)]/95 backdrop-blur-xl">
            <div className="px-4 py-4 space-y-3">
              <a href="#how-it-works" onClick={() => setMenuOpen(false)} className="block text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]">How It Works</a>
              <a href="#features" onClick={() => setMenuOpen(false)} className="block text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Features</a>
              <a href="#pipeline" onClick={() => setMenuOpen(false)} className="block text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)]">Pipeline</a>
              <div className="pt-2 flex gap-2">
                <Link href="/auth/login" onClick={() => setMenuOpen(false)} className="btn-ghost flex-1 justify-center text-xs">Sign In</Link>
                <Link href="/auth/register" onClick={() => setMenuOpen(false)} className="btn-primary flex-1 justify-center text-xs">Get Started</Link>
              </div>
            </div>
          </div>
        )}
      </nav>

      {/* ─── Hero ─── */}
      <section className="relative min-h-screen flex items-center justify-center overflow-hidden pt-16">
        <div className="absolute inset-0 bg-mesh" />
        <div className="absolute inset-0 bg-grid opacity-30" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-brand-500/10 rounded-full blur-[128px]" />
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-[128px]" />

        <div className="relative z-10 max-w-5xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-brand-500/20 bg-brand-500/10 text-brand-400 text-xs mb-8">
            <Sparkles size={12} />
            AI-Powered Research Platform
          </div>

          <h1 className="text-4xl sm:text-5xl md:text-7xl font-bold leading-tight mb-6">
            From{' '}
            <span className="text-gradient">Idea</span>
            {' '}to{' '}
            <span className="text-gradient">Research Paper</span>
            <br />
            in One Workflow
          </h1>

          <p className="text-lg text-[var(--text-secondary)] max-w-2xl mx-auto mb-10">
            ResearchIDE automates literature review, gap analysis, idea generation, and paper writing
            so you can focus on what matters — your research.
          </p>

          <div className="flex items-center justify-center gap-4">
            {showAuth ? (
              <Link href="/dashboard" className="btn-primary text-base px-8 py-3">
                Go to Dashboard <ArrowRight size={18} />
              </Link>
            ) : (
              <>
                <Link href="/auth/register" className="btn-primary text-base px-8 py-3">
                  Start Researching <ArrowRight size={18} />
                </Link>
                <a href="#how-it-works" className="btn-secondary text-base px-8 py-3">
                  See How It Works
                </a>
              </>
            )}
          </div>

          <div className="mt-12 flex items-center justify-center gap-8 text-xs text-[var(--text-muted)]">
            <span className="flex items-center gap-1.5"><Star size={12} /> No credit card</span>
            <span className="flex items-center gap-1.5"><Github size={12} /> Open source</span>
            <span className="flex items-center gap-1.5"><Layers size={12} /> 7+ LLM providers</span>
          </div>

          <div className="mt-16">
            <div className="relative max-w-4xl mx-auto rounded-2xl border border-[var(--border)] bg-[var(--bg-secondary)]/80 backdrop-blur-sm overflow-hidden shadow-2xl shadow-black/40">
              <div className="flex items-center gap-2 px-4 py-3 border-b border-[var(--border)] bg-[var(--bg-card)]">
                <div className="flex gap-1.5">
                  <div className="w-3 h-3 rounded-full bg-red-500/80" />
                  <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                  <div className="w-3 h-3 rounded-full bg-green-500/80" />
                </div>
                <div className="flex-1 flex justify-center">
                  <div className="flex items-center gap-2 px-3 py-1 rounded-md bg-[var(--bg-primary)] border border-[var(--border)]">
                    <Brain size={10} className="text-brand-400" />
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">research-ide — analyzing gaps...</span>
                  </div>
                </div>
              </div>
              <div className="p-6 text-left">
                <div className="flex items-center gap-2 mb-4">
                  <div className="flex h-6 w-6 items-center justify-center rounded bg-brand-600/20 text-brand-400">
                    <Search size={12} />
                  </div>
                  <span className="text-xs font-medium text-[var(--text-primary)]">Gap Analysis Results</span>
                  <span className="badge-green text-[10px]">completed</span>
                </div>
                <div className="space-y-3">
                  {[
                    'Limited research on low-resource NLP for Dravidian languages',
                    'No existing benchmark datasets for Kannada-English code-mixed text',
                    'Transfer learning approaches unexplored for this specific domain',
                  ].map((gap, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-[var(--text-secondary)]">
                      <div className="w-1.5 h-1.5 rounded-full bg-brand-400 mt-1.5 flex-shrink-0" />
                      {gap}
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t border-[var(--border)] flex items-center gap-2 text-xs text-[var(--text-muted)]">
                  <div className="h-1.5 flex-1 rounded-full bg-[var(--border)] overflow-hidden">
                    <div className="h-full w-2/3 rounded-full bg-gradient-to-r from-brand-500 to-purple-500" />
                  </div>
                  <span>Step 3 of 7</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 animate-bounce">
          <ChevronDown size={20} className="text-[var(--text-muted)]" />
        </div>
      </section>

      {/* ─── Stats ─── */}
      <section className="py-20 border-t border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {STATS.map((stat, i) => (
              <div key={i} className="text-center">
                <div className="flex justify-center mb-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-600/10">
                    <stat.icon size={18} className="text-brand-400" />
                  </div>
                </div>
                <div className="text-3xl font-bold text-[var(--text-primary)]">{stat.value}</div>
                <div className="text-xs text-[var(--text-muted)] mt-1">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── How It Works ─── */}
      <section id="how-it-works" className="py-24 relative">
        <div className="absolute inset-0 bg-mesh opacity-50" />
        <div className="relative z-10 max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[var(--text-primary)] mb-4">
              How It Works
            </h2>
            <p className="text-[var(--text-secondary)] max-w-2xl mx-auto">
              From a simple research question to a complete paper — ResearchIDE guides you through every step.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6">
            {[
              { step: '01', title: 'Describe Your Idea', desc: 'Write your research problem in natural language. Our AI extracts the core concepts, domain, and constraints.', color: 'from-brand-500 to-purple-500' },
              { step: '02', title: 'AI-Powered Analysis', desc: 'ResearchIDE automatically retrieves papers, identifies gaps, generates ideas, and creates an execution plan.', color: 'from-purple-500 to-pink-500' },
              { step: '03', title: 'Get Your Output', desc: 'Receive a complete research guide, presentation, code, and a formatted paper ready for submission.', color: 'from-pink-500 to-rose-500' },
            ].map((item, i) => (
              <div key={i} className="card relative group">
                <div className={`absolute inset-0 rounded-xl bg-gradient-to-br ${item.color} opacity-0 group-hover:opacity-5 transition-opacity duration-500`} />
                <div className="relative">
                  <div className="flex items-center gap-3 mb-4">
                    <div className={`flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br ${item.color} text-white text-xs font-bold`}>
                      {item.step}
                    </div>
                  </div>
                  <h3 className="font-semibold text-[var(--text-primary)] mb-2">{item.title}</h3>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{item.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Pipeline ─── */}
      <section id="pipeline" className="py-24 border-t border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[var(--text-primary)] mb-4">
              7-Step Research Pipeline
            </h2>
            <p className="text-[var(--text-secondary)] max-w-2xl mx-auto">
              Each step builds on the previous, creating a seamless end-to-end research workflow.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {STEPS.map((step, i) => (
              <div key={i} className="card group hover:border-brand-500/30 transition-all">
                <div className="flex items-center gap-3 mb-3">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br ${step.color} text-white`}>
                    <step.icon size={15} />
                  </div>
                  <div>
                    <span className="text-[10px] text-[var(--text-muted)] font-mono">Step {i + 1}</span>
                  </div>
                </div>
                <h3 className="font-medium text-sm text-[var(--text-primary)] mb-1.5">{step.label}</h3>
                <p className="text-xs text-[var(--text-secondary)] leading-relaxed">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── Features ─── */}
      <section id="features" className="py-24 border-t border-[var(--border)]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-[var(--text-primary)] mb-4">
              Built for Researchers
            </h2>
            <p className="text-[var(--text-secondary)] max-w-2xl mx-auto">
              Everything you need to accelerate your research workflow.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {FEATURES.map((feat, i) => (
              <div key={i} className="card-elevated flex items-start gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-600/10 flex-shrink-0">
                  <feat.icon size={18} className="text-brand-400" />
                </div>
                <div>
                  <h3 className="font-medium text-sm text-[var(--text-primary)] mb-1">{feat.title}</h3>
                  <p className="text-xs text-[var(--text-secondary)]">{feat.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-transparent via-brand-600/5 to-transparent" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-brand-500/5 rounded-full blur-[128px]" />
        <div className="relative z-10 max-w-3xl mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-brand-500/20 bg-brand-500/10 text-brand-400 text-xs mb-6">
            <Sparkles size={12} />
            Get Started Free
          </div>
          <h2 className="text-3xl sm:text-5xl font-bold text-[var(--text-primary)] mb-4">
            Ready to Accelerate Your Research?
          </h2>
          <p className="text-[var(--text-secondary)] mb-10 max-w-xl mx-auto">
            Join researchers who are using AI to go from idea to paper faster.
            No credit card required.
          </p>
          <div className="flex items-center justify-center gap-4">
            {showAuth ? (
              <Link href="/dashboard" className="btn-primary text-base px-10 py-3">
                Go to Dashboard <ArrowRight size={18} />
              </Link>
            ) : (
              <>
                <Link href="/auth/register" className="btn-primary text-base px-10 py-3">
                  Create Free Account <ArrowRight size={18} />
                </Link>
                <a href="#how-it-works" className="btn-secondary text-base px-8 py-3">
                  Learn More
                </a>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ─── Footer ─── */}
      <footer className="border-t border-[var(--border)] py-12">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-600 text-white">
                <Brain size={12} />
              </div>
              <span className="font-semibold text-sm text-[var(--text-primary)]">ResearchIDE</span>
            </div>
            <div className="flex items-center gap-6 text-xs text-[var(--text-muted)]">
              <span>AI-Powered Research Platform</span>
              <span>&copy; {new Date().getFullYear()}</span>
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="hover:text-[var(--text-secondary)] transition-colors">
                <Github size={14} />
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
