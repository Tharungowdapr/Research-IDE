'use client';

import { useState, useEffect, useRef } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  BookOpen, ArrowRight, Loader2, CheckCircle2, Clock,
  Terminal, Package, ChevronDown, ChevronRight as ChevronRightIcon,
  AlertTriangle, ExternalLink, Lightbulb, RefreshCw,
  Download, FileText, Layers, FlaskConical, BarChart2,
  Cpu, GitBranch, Bug, Rocket, Star,
} from 'lucide-react';
import { projectsAPI } from '@/services/api';
import { useStream } from '@/hooks/useStream';
import { StreamLog } from '@/components/ui/StreamLog';
import { ErrorBoundary } from '@/components/ui/ErrorBoundary';

// ── Collapsible section ───────────────────────────────────────────────────────
function Section({ icon: Icon, title, badge, color = 'text-brand-400', children, defaultOpen = true }: any) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-[var(--border)] rounded-none overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-5 py-3.5 bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-all text-left"
      >
        <Icon size={15} className={color} />
        <span className="font-semibold text-sm text-[var(--text-primary)] flex-1">{title}</span>
        {badge && <span className="badge-blue text-[10px]">{badge}</span>}
        {open
          ? <ChevronDown size={13} className="text-[var(--text-muted)] flex-shrink-0" />
          : <ChevronRightIcon size={13} className="text-[var(--text-muted)] flex-shrink-0" />}
      </button>
      {open && <div className="p-5 bg-[var(--bg-card)] space-y-4">{children}</div>}
    </div>
  );
}

// ── Code block ────────────────────────────────────────────────────────────────
function CodeBlock({ code, label }: { code: string; label?: string }) {
  const [copied, setCopied] = useState(false);
  if (!code) return null;
  return (
    <div className="rounded-lg border border-[var(--border)] overflow-hidden">
      {label && (
        <div className="flex items-center justify-between px-3 py-1.5 bg-[var(--bg-secondary)] border-b border-[var(--border)]">
          <span className="text-[10px] font-mono text-[var(--text-muted)]">{label}</span>
          <button
            onClick={() => { navigator.clipboard.writeText(code); setCopied(true); setTimeout(() => setCopied(false), 2000); }}
            className="text-[10px] text-[var(--text-muted)] hover:text-brand-400 transition-colors"
          >
            {copied ? '✓ Copied' : 'Copy'}
          </button>
        </div>
      )}
      <pre className="p-3 text-xs font-mono text-emerald-400 bg-[var(--bg-primary)] overflow-x-auto whitespace-pre-wrap leading-relaxed">
        {code}
      </pre>
    </div>
  );
}

// ── Phase step card ───────────────────────────────────────────────────────────
function StepCard({ step }: { step: any }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-[var(--border)] rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-all text-left"
      >
        <div className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-600/20 text-brand-400 text-xs font-bold flex-shrink-0">
          {step.step}
        </div>
        <span className="font-medium text-sm text-[var(--text-primary)] flex-1">{step.title}</span>
        {open
          ? <ChevronDown size={12} className="text-[var(--text-muted)]" />
          : <ChevronRightIcon size={12} className="text-[var(--text-muted)]" />}
      </button>
      {open && (
        <div className="px-4 pb-4 pt-2 space-y-3 bg-[var(--bg-card)]">
          <p className="text-sm text-[var(--text-secondary)] leading-relaxed">{step.description}</p>
          {step.command_or_code && (
            <CodeBlock code={step.command_or_code} label="Command / Code" />
          )}
          {step.expected_output && (
            <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2">
              <p className="text-[10px] font-medium text-emerald-400 mb-1">✓ Expected Output</p>
              <p className="text-xs text-[var(--text-secondary)]">{step.expected_output}</p>
            </div>
          )}
          {step.common_issues?.length > 0 && (
            <div className="rounded-lg bg-yellow-500/10 border border-yellow-500/20 px-3 py-2">
              <p className="text-[10px] font-medium text-yellow-400 mb-1.5 flex items-center gap-1">
                <AlertTriangle size={10} /> Common Issues
              </p>
              <ul className="space-y-1">
                {step.common_issues.map((issue: string, i: number) => (
                  <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                    <span className="text-yellow-400 flex-shrink-0">→</span>{issue}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Phase card ────────────────────────────────────────────────────────────────
function PhaseCard({ phase, index }: { phase: any; index: number }) {
  const [open, setOpen] = useState(index === 0);
  const PHASE_COLORS = [
    'bg-blue-500/20 text-blue-400', 'bg-purple-500/20 text-purple-400',
    'bg-teal-500/20 text-teal-400', 'bg-orange-500/20 text-orange-400',
    'bg-emerald-500/20 text-emerald-400', 'bg-pink-500/20 text-pink-400',
  ];
  const colorClass = PHASE_COLORS[index % PHASE_COLORS.length];

  return (
    <div className="border border-[var(--border)] rounded-none overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-4 px-5 py-4 bg-[var(--bg-secondary)] hover:bg-[var(--bg-hover)] transition-all text-left"
      >
        <div className={`flex h-9 w-9 items-center justify-center rounded-none text-sm font-bold flex-shrink-0 ${colorClass}`}>
          {phase.phase}
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-sm text-[var(--text-primary)]">{phase.title}</p>
          <div className="flex items-center gap-3 mt-0.5">
            <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
              <Clock size={10} />{phase.duration}
            </span>
            <span className="text-xs text-[var(--text-muted)] truncate">{phase.goal}</span>
          </div>
        </div>
        <span className="badge-blue flex-shrink-0">{phase.steps?.length || 0} steps</span>
        {open
          ? <ChevronDown size={13} className="text-[var(--text-muted)] flex-shrink-0" />
          : <ChevronRightIcon size={13} className="text-[var(--text-muted)] flex-shrink-0" />}
      </button>

      {open && (
        <div className="p-5 bg-[var(--bg-card)] space-y-3">
          {/* Goal */}
          <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] px-3 py-2">
            <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-1">Goal</p>
            <p className="text-xs text-[var(--text-secondary)]">{phase.goal}</p>
          </div>

          {/* Steps */}
          <div className="space-y-2">
            {(phase.steps || []).map((step: any) => (
              <StepCard key={step.step} step={step} />
            ))}
          </div>

          {/* Deliverable */}
          {phase.phase_deliverable && (
            <div className="rounded-lg bg-brand-600/10 border border-brand-500/20 px-4 py-3">
              <p className="text-[10px] font-medium text-brand-400 mb-1 flex items-center gap-1">
                <CheckCircle2 size={10} /> Phase Deliverable
              </p>
              <p className="text-xs text-[var(--text-secondary)]">{phase.phase_deliverable}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
function BuildGuidePageInner() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [guide, setGuide] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const triggered = useRef(false);
  const { stream, streaming, log, error } = useStream();
  const reportStream = useStream();

  useEffect(() => {
    projectsAPI.get(id).then((p) => {
      if (p.outputs?.code) { setGuide(p.outputs.code); setLoading(false); }
      else { setLoading(false); if (!triggered.current) { triggered.current = true; handleGenerate(); } }
    }).catch(() => setLoading(false));
  }, [id]);

  const handleGenerate = () => {
    triggered.current = true;
    stream(id, 'code', { onResult: (data) => { if (data?.code) setGuide(data.code); } });
  };

  const handleWritePaper = () => {
    reportStream.stream(id, 'report', { onDone: () => router.push(`/projects/${id}/report`) });
  };

  const handleDownloadGuide = () => {
    if (!guide) return;
    const lines: string[] = [];
    lines.push(`# ${guide.project_name || 'Build Guide'}`);
    lines.push(`**${guide.one_line_summary || ''}**`);
    lines.push(`\n> Time: ${guide.estimated_total_time} | Difficulty: ${guide.difficulty}\n`);

    lines.push('## Prerequisites');
    lines.push(`**Knowledge:** ${guide.prerequisites?.knowledge?.join(', ')}`);
    lines.push(`**Tools:** ${guide.prerequisites?.tools?.join(', ')}`);

    if (guide.environment_setup?.steps?.length) {
      lines.push('\n## Environment Setup');
      for (const s of guide.environment_setup.steps) {
        lines.push(`\n### ${s.step}. ${s.title}`);
        if (s.command) lines.push(`\`\`\`bash\n${s.command}\n\`\`\``);
        if (s.note) lines.push(`> ${s.note}`);
      }
    }

    if (guide.phases?.length) {
      lines.push('\n## Build Phases');
      for (const phase of guide.phases) {
        lines.push(`\n### Phase ${phase.phase}: ${phase.title}`);
        lines.push(`**Duration:** ${phase.duration} | **Goal:** ${phase.goal}`);
        for (const step of (phase.steps || [])) {
          lines.push(`\n#### Step ${step.step}: ${step.title}`);
          lines.push(step.description);
          if (step.command_or_code) lines.push(`\`\`\`\n${step.command_or_code}\n\`\`\``);
          if (step.expected_output) lines.push(`**Expected:** ${step.expected_output}`);
        }
        if (phase.phase_deliverable) lines.push(`\n**Deliverable:** ${phase.phase_deliverable}`);
      }
    }

    if (guide.resources?.length) {
      lines.push('\n## Resources');
      for (const r of guide.resources) lines.push(`- [${r.title}](${r.url}) — ${r.why}`);
    }

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `${(guide.project_name || 'build-guide').replace(/\s+/g, '-').toLowerCase()}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
  };

  const anyStreaming = streaming || reportStream.streaming;

  if (loading || (streaming && !guide)) {
    return (
      <div className="p-8 flex flex-col items-center justify-center min-h-[400px] gap-4">
        <Loader2 size={28} className="animate-spin text-brand-400" />
        <p className="text-sm text-[var(--text-secondary)]">Generating your detailed build guide...</p>
        <StreamLog log={log} streaming={streaming} label="Building step-by-step guide..." />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">Build Guide</h1>
          <p className="text-xs text-[var(--text-muted)] mt-0.5">Step 6 of 7 — How to build your research project</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          {guide && (
            <>
              <button onClick={handleGenerate} disabled={anyStreaming} className="btn-ghost text-sm">
                <RefreshCw size={13} /> Regenerate
              </button>
              <button onClick={handleDownloadGuide} className="btn-secondary text-sm">
                <Download size={14} /> Download Guide
              </button>
            </>
          )}
          <button onClick={handleWritePaper} disabled={anyStreaming} className="btn-primary">
            {reportStream.streaming
              ? <><Loader2 size={14} className="animate-spin" /> Writing paper...</>
              : <><FileText size={14} /> Write Paper</>}
          </button>
        </div>
      </div>

      {error && <div className="mb-4 rounded-lg bg-red-500/10 border border-red-500/20 px-4 py-3 text-sm text-red-400">{error}</div>}
      <StreamLog log={streaming ? log : reportStream.log} streaming={anyStreaming}
        label={reportStream.streaming ? 'Writing IEEE paper...' : 'Generating build guide...'} />

      {!guide ? (
        <div className="card text-center py-16">
          <BookOpen size={32} className="mx-auto mb-3 text-[var(--text-muted)]" />
          <p className="text-sm text-[var(--text-secondary)]">No build guide yet</p>
          <button onClick={handleGenerate} className="btn-primary mt-4"><Lightbulb size={14} /> Generate Build Guide</button>
        </div>
      ) : (
        <div className="space-y-5">

          {/* Hero card */}
          <div className="card border-brand-500/30 bg-brand-600/5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-bold text-[var(--text-primary)] mb-1">{guide.project_name}</h2>
                <p className="text-sm text-[var(--text-secondary)] mb-3">{guide.one_line_summary}</p>
                <div className="flex flex-wrap gap-2">
                  <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Clock size={11} className="text-brand-400" /> {guide.estimated_total_time}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Star size={11} className="text-yellow-400" /> {guide.difficulty}
                  </span>
                  <span className="flex items-center gap-1 text-xs text-[var(--text-muted)]">
                    <Layers size={11} className="text-purple-400" /> {guide.phases?.length || 0} phases
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Prerequisites */}
          {guide.prerequisites && (
            <Section icon={CheckCircle2} title="Prerequisites" color="text-emerald-400">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {guide.prerequisites.knowledge?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-1.5">Knowledge Needed</p>
                    <ul className="space-y-1">
                      {guide.prerequisites.knowledge.map((k: string, i: number) => (
                        <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                          <CheckCircle2 size={10} className="text-emerald-400 mt-0.5 flex-shrink-0" />{k}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guide.prerequisites.tools?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-1.5">Tools Required</p>
                    <ul className="space-y-1">
                      {guide.prerequisites.tools.map((t: string, i: number) => (
                        <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                          <Terminal size={10} className="text-blue-400 mt-0.5 flex-shrink-0" />{t}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guide.prerequisites.accounts?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-1.5">Free Accounts Needed</p>
                    <ul className="space-y-1">
                      {guide.prerequisites.accounts.map((a: string, i: number) => (
                        <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                          <ExternalLink size={10} className="text-purple-400 mt-0.5 flex-shrink-0" />{a}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Project Structure */}
          {guide.project_structure && (
            <Section icon={Layers} title="Project Structure" color="text-teal-400" defaultOpen={false}>
              <p className="text-xs text-[var(--text-secondary)] mb-3">{guide.project_structure.description}</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {guide.project_structure.directories?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Directories</p>
                    <div className="space-y-1.5">
                      {guide.project_structure.directories.map((d: any, i: number) => (
                        <div key={i} className="flex items-start gap-2">
                          <code className="text-xs text-brand-400 font-mono flex-shrink-0 w-36">{d.path}</code>
                          <span className="text-xs text-[var(--text-muted)]">{d.purpose}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {guide.project_structure.key_files?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Key Files</p>
                    <div className="space-y-1.5">
                      {guide.project_structure.key_files.map((f: any, i: number) => (
                        <div key={i} className="flex items-start gap-2">
                          <code className="text-xs text-emerald-400 font-mono flex-shrink-0 w-40">{f.file}</code>
                          <span className="text-xs text-[var(--text-muted)]">{f.purpose}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Environment Setup */}
          {guide.environment_setup && (
            <Section icon={Terminal} title="Environment Setup" color="text-yellow-400">
              <p className="text-xs text-[var(--text-secondary)] mb-3">{guide.environment_setup.description}</p>
              <div className="space-y-2 mb-3">
                {(guide.environment_setup.steps || []).map((step: any) => (
                  <div key={step.step} className="rounded-lg border border-[var(--border)] p-3 bg-[var(--bg-secondary)]">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-yellow-500/20 text-yellow-400 text-[10px] font-bold flex-shrink-0">{step.step}</span>
                      <span className="font-medium text-xs text-[var(--text-primary)]">{step.title}</span>
                    </div>
                    {step.command && <CodeBlock code={step.command} />}
                    {step.note && <p className="text-[11px] text-[var(--text-muted)] mt-1.5 italic">{step.note}</p>}
                  </div>
                ))}
              </div>
              {guide.environment_setup.requirements?.length > 0 && (
                <div>
                  <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-1.5">requirements.txt</p>
                  <CodeBlock code={guide.environment_setup.requirements.join('\n')} label="requirements.txt" />
                </div>
              )}
            </Section>
          )}

          {/* Build Phases */}
          <Section icon={Rocket} title="Build Phases" badge={`${guide.phases?.length || 0} phases`} color="text-brand-400">
            <div className="space-y-3">
              {(guide.phases || []).map((phase: any, i: number) => (
                <PhaseCard key={phase.phase} phase={phase} index={i} />
              ))}
            </div>
          </Section>

          {/* Architecture Guide */}
          {guide.architecture_guide && (
            <Section icon={GitBranch} title="Architecture Guide" color="text-purple-400" defaultOpen={false}>
              <p className="text-sm text-[var(--text-secondary)] mb-3">{guide.architecture_guide.overview}</p>
              {guide.architecture_guide.data_flow?.length > 0 && (
                <div className="mb-3">
                  <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Data Flow</p>
                  <div className="space-y-1">
                    {guide.architecture_guide.data_flow.map((step: string, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span className="text-brand-400 font-mono flex-shrink-0">{i + 1}.</span>
                        <span className="text-[var(--text-secondary)]">{step}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {guide.architecture_guide.components?.length > 0 && (
                <div className="grid gap-3">
                  {guide.architecture_guide.components.map((comp: any, i: number) => (
                    <div key={i} className="rounded-lg border border-[var(--border)] p-3 bg-[var(--bg-secondary)]">
                      <p className="font-medium text-xs text-[var(--text-primary)] mb-1">{comp.name}</p>
                      <p className="text-xs text-[var(--text-muted)] mb-2">{comp.purpose}</p>
                      {comp.code_sketch && <CodeBlock code={comp.code_sketch} />}
                      {comp.implementation_hint && (
                        <p className="text-[11px] text-brand-400 mt-1.5 italic">💡 {comp.implementation_hint}</p>
                      )}
                    </div>
                  ))}
                </div>
              )}
              {guide.architecture_guide.design_decisions?.length > 0 && (
                <div>
                  <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Design Decisions</p>
                  {guide.architecture_guide.design_decisions.map((d: any, i: number) => (
                    <div key={i} className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-2.5 mb-2">
                      <p className="text-xs font-medium text-[var(--text-primary)]">{d.decision}</p>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">{d.reasoning}</p>
                    </div>
                  ))}
                </div>
              )}
            </Section>
          )}

          {/* Training Guide */}
          {guide.training_guide && (
            <Section icon={FlaskConical} title="Training Guide" color="text-orange-400" defaultOpen={false}>
              <p className="text-sm text-[var(--text-secondary)] mb-3">{guide.training_guide.overview}</p>
              {guide.training_guide.hyperparameters?.length > 0 && (
                <div className="mb-3">
                  <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Hyperparameters</p>
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                      <thead><tr className="border-b border-[var(--border)]">
                        {['Parameter','Recommended','Range','Note'].map(h => (
                          <th key={h} className="text-left py-1.5 pr-4 text-[10px] font-medium text-[var(--text-muted)] uppercase">{h}</th>
                        ))}
                      </tr></thead>
                      <tbody>
                        {guide.training_guide.hyperparameters.map((hp: any, i: number) => (
                          <tr key={i} className="border-b border-[var(--border)]/50">
                            <td className="py-1.5 pr-4 font-mono text-brand-400">{hp.name}</td>
                            <td className="py-1.5 pr-4 font-mono text-emerald-400">{hp.recommended}</td>
                            <td className="py-1.5 pr-4 font-mono text-[var(--text-muted)]">{hp.range}</td>
                            <td className="py-1.5 text-[var(--text-muted)]">{hp.note}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              {guide.training_guide.training_command && (
                <div className="mb-3">
                  <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-1.5">Training Command</p>
                  <CodeBlock code={guide.training_guide.training_command} label="Run this to start training" />
                </div>
              )}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
                {guide.training_guide.monitoring && (
                  <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="font-medium text-[var(--text-muted)] mb-1">Monitoring</p>
                    <p className="text-[var(--text-secondary)]">{guide.training_guide.monitoring}</p>
                  </div>
                )}
                {guide.training_guide.checkpointing && (
                  <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="font-medium text-[var(--text-muted)] mb-1">Checkpointing</p>
                    <p className="text-[var(--text-secondary)]">{guide.training_guide.checkpointing}</p>
                  </div>
                )}
                {guide.training_guide.expected_training_time && (
                  <div className="rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] p-3">
                    <p className="font-medium text-[var(--text-muted)] mb-1">Expected Time</p>
                    <p className="text-[var(--text-secondary)]">{guide.training_guide.expected_training_time}</p>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Evaluation Guide */}
          {guide.evaluation_guide && (
            <Section icon={BarChart2} title="Evaluation Guide" color="text-teal-400" defaultOpen={false}>
              {guide.evaluation_guide.metrics?.length > 0 && (
                <div className="mb-3">
                  <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Metrics</p>
                  <div className="space-y-2">
                    {guide.evaluation_guide.metrics.map((m: any, i: number) => (
                      <div key={i} className="rounded-lg border border-[var(--border)] p-3 bg-[var(--bg-secondary)]">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-medium text-xs text-[var(--text-primary)]">{m.metric}</span>
                          <span className="text-[10px] text-[var(--text-muted)]">— {m.why}</span>
                        </div>
                        {m.how_to_compute && <CodeBlock code={m.how_to_compute} />}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {guide.evaluation_guide.evaluation_command && (
                <CodeBlock code={guide.evaluation_guide.evaluation_command} label="Evaluation command" />
              )}
              {guide.evaluation_guide.how_to_interpret && (
                <div className="rounded-lg bg-brand-600/10 border border-brand-500/20 px-3 py-2.5 mt-3">
                  <p className="text-[10px] font-medium text-brand-400 mb-1">Interpreting Results</p>
                  <p className="text-xs text-[var(--text-secondary)]">{guide.evaluation_guide.how_to_interpret}</p>
                </div>
              )}
            </Section>
          )}

          {/* Debugging Guide */}
          {guide.debugging_guide?.length > 0 && (
            <Section icon={Bug} title="Debugging Guide" color="text-red-400" defaultOpen={false}>
              <div className="space-y-3">
                {guide.debugging_guide.map((item: any, i: number) => (
                  <div key={i} className="rounded-lg border border-[var(--border)] p-4 bg-[var(--bg-secondary)]">
                    <p className="font-semibold text-sm text-[var(--text-primary)] mb-2">{item.problem}</p>
                    {item.symptoms && (
                      <p className="text-xs text-[var(--text-muted)] mb-2 flex items-start gap-1.5">
                        <span className="text-yellow-400 flex-shrink-0">Symptoms:</span> {item.symptoms}
                      </p>
                    )}
                    {item.solution && (
                      <div className="rounded-lg bg-emerald-500/10 border border-emerald-500/20 px-3 py-2 mb-2">
                        <p className="text-[10px] font-medium text-emerald-400 mb-0.5">Solution</p>
                        <p className="text-xs text-[var(--text-secondary)]">{item.solution}</p>
                      </div>
                    )}
                    {item.prevention && (
                      <p className="text-xs text-[var(--text-muted)] flex items-start gap-1.5">
                        <span className="text-blue-400 flex-shrink-0">Prevention:</span> {item.prevention}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Next Steps */}
          {guide.next_steps && (
            <Section icon={Rocket} title="Next Steps & Paper Checklist" color="text-emerald-400" defaultOpen={false}>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {guide.next_steps.improvements?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Improvements to Try</p>
                    <ul className="space-y-1.5">
                      {guide.next_steps.improvements.map((item: string, i: number) => (
                        <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                          <span className="text-brand-400 flex-shrink-0">→</span>{item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guide.next_steps.ablation_studies?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Ablation Studies</p>
                    <ul className="space-y-1.5">
                      {guide.next_steps.ablation_studies.map((item: string, i: number) => (
                        <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                          <span className="text-purple-400 flex-shrink-0">◈</span>{item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {guide.next_steps.paper_checklist?.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium text-[var(--text-muted)] uppercase mb-2">Paper Checklist</p>
                    <ul className="space-y-1.5">
                      {guide.next_steps.paper_checklist.map((item: string, i: number) => (
                        <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                          <CheckCircle2 size={10} className="text-emerald-400 mt-0.5 flex-shrink-0" />{item}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Resources */}
          {guide.resources?.length > 0 && (
            <Section icon={BookOpen} title="Learning Resources" color="text-cyan-400" defaultOpen={false}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {guide.resources.map((r: any, i: number) => (
                  <a key={i} href={r.url} target="_blank" rel="noopener"
                    className="flex items-start gap-3 rounded-lg border border-[var(--border)] p-3 bg-[var(--bg-secondary)] hover:border-brand-500/30 hover:bg-[var(--bg-hover)] transition-all group">
                    <ExternalLink size={14} className="text-brand-400 mt-0.5 flex-shrink-0 group-hover:text-brand-300" />
                    <div>
                      <p className="font-medium text-xs text-[var(--text-primary)] group-hover:text-brand-400 transition-colors">{r.title}</p>
                      <p className="text-xs text-[var(--text-muted)] mt-0.5">{r.why}</p>
                    </div>
                  </a>
                ))}
              </div>
            </Section>
          )}
        </div>
      )}
    </div>
  );
}

export default function BuildGuidePage() {
  return <ErrorBoundary><BuildGuidePageInner /></ErrorBoundary>;
}
