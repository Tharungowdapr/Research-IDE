'use client';

import { useState, useEffect } from 'react';
import {
  Cpu, Key, Check, X, Loader2, Eye, EyeOff, ExternalLink,
  RefreshCw, Trash2, Zap, Globe, DollarSign,
  Hash, RotateCcw, Leaf, Activity, ChevronDown, ChevronUp,
  Bolt, Brain, Sparkles, Waves, Server, GitMerge,
} from 'lucide-react';
import { llmAPI } from '@/services/api';

interface Provider {
  id: string;
  name: string;
  description: string;
  requires_key: boolean;
  get_key_url: string;
  models: { id: string; name: string; context: string }[];
}

interface KeyStatus {
  configured_providers: string[];
  preferred_provider: string;
  preferred_model: string;
  ollama_base_url: string;
}

interface OllamaModel { id: string; name: string; size: string; }

const PROVIDER_ICON_COMPONENTS: Record<string, React.ElementType> = {
  openai: Cpu, anthropic: Brain, groq: Zap,
  gemini: Sparkles, cohere: Waves, ollama: Server, openrouter: GitMerge,
};

const PROVIDER_COLORS: Record<string, string> = {
  openai: 'emerald', anthropic: 'violet', groq: 'yellow',
  gemini: 'blue', cohere: 'teal', ollama: 'orange', openrouter: 'pink',
};

function fmt(n: number, decimals = 2) { return n.toFixed(decimals); }
function fmtTokens(n: number) {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(2)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}
function fmtEnergy(wh: number) {
  if (wh < 0.001) return `${(wh * 1000).toFixed(3)} mWh`;
  if (wh >= 1000) return `${(wh / 1000).toFixed(3)} kWh`;
  return `${wh.toFixed(4)} Wh`;
}
// CO2 equiv: avg grid ~0.4 kg CO2/kWh
function fmtCO2(wh: number) {
  const g = (wh / 1000) * 0.4 * 1000;
  if (g < 1) return `${(g * 1000).toFixed(1)} μg`;
  if (g < 1000) return `${g.toFixed(2)} g`;
  return `${(g / 1000).toFixed(3)} kg`;
}

export default function LLMSettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [keyStatus, setKeyStatus] = useState<KeyStatus | null>(null);
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [usage, setUsage] = useState<any>(null);
  const [resettingUsage, setResettingUsage] = useState(false);
  const [showRecentCalls, setShowRecentCalls] = useState(false);

  // Step 1: selected provider
  const [activeProvider, setActiveProvider] = useState<string>('');

  // Per-provider key state
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [savingKey, setSavingKey] = useState(false);
  const [saveKeyError, setSaveKeyError] = useState('');
  const [savedKey, setSavedKey] = useState(false);
  const [testingProvider, setTestingProvider] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);

  // Step 2: model selection
  const [selectedModel, setSelectedModel] = useState('');
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    setLoadError('');
    try {
      // Providers endpoint is always available (no auth needed)
      const providersData = await llmAPI.listProviders();
      setProviders(providersData.providers);

      // Auth-gated calls — handle independently
      try {
        const [statusData, usageData] = await Promise.all([
          llmAPI.getKeysStatus(),
          llmAPI.getUsage().catch(() => null),
        ]);
        setKeyStatus(statusData);
        const pref = statusData.preferred_provider || 'ollama';
        setActiveProvider(pref);
        setSelectedModel(statusData.preferred_model || '');
        setOllamaUrl(statusData.ollama_base_url || 'http://localhost:11434');
        if (usageData) setUsage(usageData);
        if (pref === 'ollama') loadOllamaModels(statusData.ollama_base_url || 'http://localhost:11434');
      } catch (authErr: any) {
        // Auth failed — still show providers, just no key status
        setActiveProvider('groq');
        const msg = authErr?.response?.data?.detail || authErr?.message || 'Authentication error';
        setLoadError(msg);
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || 'Could not connect to backend.';
      setLoadError(msg);
    } finally {
      setLoading(false);
    }
  };

  const loadOllamaModels = async (url: string) => {
    try {
      const data = await llmAPI.getOllamaModels(url);
      setOllamaModels(data.models || []);
    } catch { setOllamaModels([]); }
  };

  const handleSelectProvider = (id: string) => {
    setActiveProvider(id);
    setApiKeyInput('');
    setShowKey(false);
    setSaveKeyError('');
    setSavedKey(false);
    setTestResult(null);
    setSelectedModel('');
    if (id === 'ollama') loadOllamaModels(ollamaUrl);
  };

  const handleSaveKey = async () => {
    if (!apiKeyInput.trim()) return;
    setSavingKey(true);
    setSaveKeyError('');
    setSavedKey(false);
    setTestResult(null);
    try {
      await llmAPI.saveApiKey(activeProvider, apiKeyInput.trim());
      setKeyStatus(prev =>
        prev ? { ...prev, configured_providers: Array.from(new Set([...prev.configured_providers, activeProvider])) } : prev
      );
      setApiKeyInput('');
      setSavedKey(true);
      setTimeout(() => setSavedKey(false), 3000);
    } catch (e: any) {
      setSaveKeyError(e?.response?.data?.detail || e?.message || 'Failed to save key');
    } finally {
      setSavingKey(false);
    }
  };

  const handleDeleteKey = async () => {
    try {
      await llmAPI.deleteApiKey(activeProvider);
      setKeyStatus(prev =>
        prev ? { ...prev, configured_providers: prev.configured_providers.filter(p => p !== activeProvider) } : prev
      );
      setTestResult(null);
      setSavedKey(false);
    } catch (e) { console.error(e); }
  };

  const handleTest = async () => {
    setTestingProvider(true);
    setTestResult({ success: false, message: 'Testing connection...' });
    try {
      const result = await llmAPI.testConnection({
        provider: activeProvider,
        ollama_base_url: activeProvider === 'ollama' ? ollamaUrl : undefined,
      });
      const ok = result?.success === true;
      setTestResult({
        success: ok,
        message: ok
          ? `Connected! "${result.response?.slice(0, 60) || 'OK'}"`
          : `Error: ${result.error || 'Unknown error'}`,
      });
    } catch (e: any) {
      setTestResult({ success: false, message: e?.response?.data?.detail || e?.message || 'Network error' });
    } finally {
      setTestingProvider(false);
    }
  };

  const handleSavePreferences = async () => {
    setSavingPrefs(true);
    try {
      await llmAPI.setPreferences(activeProvider, selectedModel, ollamaUrl);
      setPrefsSaved(true);
      setTimeout(() => setPrefsSaved(false), 3000);
    } catch (e) { console.error(e); } finally { setSavingPrefs(false); }
  };

  const handleResetUsage = async () => {
    if (!confirm('Reset all usage stats? This cannot be undone.')) return;
    setResettingUsage(true);
    try {
      await llmAPI.resetUsage();
      setUsage({ total_tokens: 0, prompt_tokens: 0, completion_tokens: 0, total_cost_usd: 0, total_energy_wh: 0, total_calls: 0, by_provider: {}, by_model: [], recent: [] });
    } catch (e) { console.error(e); }
    setResettingUsage(false);
  };

  const currentProvider = providers.find(p => p.id === activeProvider);
  const isConfigured = (id: string) => id === 'ollama' || (keyStatus?.configured_providers.includes(id) ?? false);
  const configured = isConfigured(activeProvider);

  const availableModels = (() => {
    if (!currentProvider) return [];
    if (activeProvider === 'ollama') return ollamaModels.map(m => ({ id: m.id, name: `${m.name} (${m.size})`, context: 'local' }));
    return configured ? currentProvider.models : [];
  })();

  if (loading) return (
    <div className="p-8 flex items-center justify-center min-h-screen">
      <Loader2 size={24} className="animate-spin text-brand-400" />
    </div>
  );

  return (
    <div className="p-8 max-w-3xl mx-auto space-y-6">

      {/* ── Header ── */}
      <div className="flex items-center gap-3">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/20">
          <Cpu size={18} className="text-brand-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-[var(--text-primary)]">AI Model Settings</h1>
          <p className="text-xs text-[var(--text-muted)]">Select provider → enter API key → choose model</p>
        </div>
      </div>

      {loadError && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400 flex items-center justify-between">
          <span><X size={13} className="inline mr-1" />{loadError}</span>
          <button onClick={loadData} className="btn-secondary text-xs"><RefreshCw size={12} /> Retry</button>
        </div>
      )}

      {/* ── Step 1: Provider picker ── */}
      <div className="card">
        <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-3">Step 1 — Select Provider</p>
        <div className="grid grid-cols-4 gap-2">
          {providers.map(p => {
            const conf = isConfigured(p.id);
            const active = activeProvider === p.id;
            return (
              <button
                key={p.id}
                onClick={() => handleSelectProvider(p.id)}
                className={`relative rounded-xl border p-3 text-center transition-all ${
                  active
                    ? 'border-brand-500 bg-brand-600/10'
                    : 'border-[var(--border)] hover:border-brand-500/40 bg-[var(--bg-secondary)]'
                }`}
              >
                {conf && (
                  <span className="absolute top-1.5 right-1.5 flex h-3.5 w-3.5 items-center justify-center rounded-full bg-emerald-500">
                    <Check size={9} className="text-white" />
                  </span>
                )}
                <div className="text-2xl mb-1">{(() => { const IconComp = PROVIDER_ICON_COMPONENTS[p.id] || Cpu; return <IconComp size={20} className="text-[var(--text-primary)]" />; })()}</div>
                <p className="text-[10px] font-medium text-[var(--text-primary)] leading-tight">{p.name.split(' ')[0]}</p>
              </button>
            );
          })}
        </div>
      </div>

      {/* ── Step 2: API Key ── */}
      {currentProvider && (
        <div className="card space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
              Step 2 — {currentProvider.requires_key ? 'API Key' : 'Connection'}
            </p>
            {configured && (
              <span className="flex items-center gap-1 text-xs text-emerald-400 font-medium">
                <Check size={11} /> Configured
              </span>
            )}
          </div>

          {/* Ollama — no key needed */}
          {!currentProvider.requires_key ? (
            <div className="space-y-3">
              <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-3 text-xs text-blue-400">
                <p className="font-medium mb-0.5">No API key required</p>
                <p className="text-blue-300/80">Ollama runs locally on your machine.</p>
                <a href="https://ollama.ai" target="_blank" className="inline-flex items-center gap-1 mt-1.5 underline hover:text-blue-300">
                  <Globe size={10} /> ollama.ai <ExternalLink size={10} />
                </a>
              </div>
              <div className="flex gap-2">
                <input
                  type="text" className="input flex-1 text-xs"
                  placeholder="http://localhost:11434"
                  value={ollamaUrl}
                  onChange={e => setOllamaUrl(e.target.value)}
                />
                <button onClick={() => loadOllamaModels(ollamaUrl)} className="btn-secondary text-xs">
                  <RefreshCw size={12} /> Refresh
                </button>
              </div>
              <button
                onClick={handleTest}
                disabled={testingProvider}
                className="btn-secondary text-xs"
              >
                {testingProvider ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                Test Connection
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <input
                    type={showKey ? 'text' : 'password'}
                    className="input pr-8 text-xs"
                    placeholder={configured ? '••••••••••••••• (key stored)' : `Paste your ${currentProvider.name} API key`}
                    value={apiKeyInput}
                    onChange={e => setApiKeyInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSaveKey()}
                  />
                  <button
                    type="button"
                    onClick={() => setShowKey(v => !v)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                  >
                    {showKey ? <EyeOff size={13} /> : <Eye size={13} />}
                  </button>
                </div>
                <button
                  onClick={handleSaveKey}
                  disabled={!apiKeyInput.trim() || savingKey}
                  className="btn-primary text-xs"
                >
                  {savingKey ? <Loader2 size={13} className="animate-spin" /> : <Key size={13} />}
                  Save
                </button>
                {configured && (
                  <button onClick={handleDeleteKey} className="btn-secondary text-xs text-red-400 hover:text-red-300" title="Remove key">
                    <Trash2 size={13} />
                  </button>
                )}
              </div>

              {saveKeyError && <p className="text-xs text-red-400">{saveKeyError}</p>}
              {savedKey && <p className="text-xs text-emerald-400 flex items-center gap-1"><Check size={11} /> Key saved</p>}

              <div className="flex items-center gap-2">
                <button
                  onClick={handleTest}
                  disabled={testingProvider || !configured}
                  className="btn-secondary text-xs"
                >
                  {testingProvider ? <Loader2 size={12} className="animate-spin" /> : <Zap size={12} />}
                  Test Connection
                </button>
                <a href={currentProvider.get_key_url} target="_blank" className="text-xs text-brand-400 hover:text-brand-300 flex items-center gap-1">
                  Get API key <ExternalLink size={10} />
                </a>
              </div>
            </div>
          )}

          {testResult && (
            <div className={`rounded-lg px-3 py-2 text-xs flex items-start gap-2 ${
              testResult.message === 'Testing connection...'
                ? 'bg-[var(--bg-secondary)] border border-[var(--border)] text-[var(--text-muted)]'
                : testResult.success
                  ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                  : 'bg-red-500/10 border border-red-500/20 text-red-400'
            }`}>
              {testResult.message === 'Testing connection...'
                ? <Loader2 size={12} className="animate-spin mt-0.5 flex-shrink-0" />
                : testResult.success
                  ? <Check size={12} className="mt-0.5 flex-shrink-0" />
                  : <X size={12} className="mt-0.5 flex-shrink-0" />
              }
              {testResult.message}
            </div>
          )}
        </div>
      )}

      {/* ── Step 3: Model selection (only shown when configured) ── */}
      {currentProvider && (configured) && (
        <div className="card space-y-3">
          <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide">
            Step 3 — Select Model
          </p>

          {activeProvider === 'ollama' && ollamaModels.length === 0 ? (
            <p className="text-xs text-yellow-400 flex items-center gap-1.5">
              <Server size={11} /> No local models found. Run <code className="bg-[var(--bg-secondary)] px-1 rounded">ollama pull llama3.2</code> to install one.
            </p>
          ) : availableModels.length === 0 ? (
            <p className="text-xs text-[var(--text-muted)]">No models available.</p>
          ) : (
            <div className="grid grid-cols-2 gap-2">
              {availableModels.map(m => (
                <button
                  key={m.id}
                  onClick={() => setSelectedModel(m.id)}
                  className={`rounded-xl border px-3 py-2.5 text-left transition-all ${
                    selectedModel === m.id
                      ? 'border-brand-500 bg-brand-600/10'
                      : 'border-[var(--border)] hover:border-brand-500/40 bg-[var(--bg-secondary)]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-0.5">
                    <p className="text-xs font-medium text-[var(--text-primary)] truncate">{m.name}</p>
                    {selectedModel === m.id && <Check size={11} className="text-brand-400 flex-shrink-0" />}
                  </div>
                  <p className="text-[10px] text-[var(--text-muted)]">Context: {m.context}</p>
                </button>
              ))}
            </div>
          )}

          {selectedModel && (
            <div className="flex items-center gap-2 pt-1">
              <button
                onClick={handleSavePreferences}
                disabled={savingPrefs}
                className="btn-primary text-xs"
              >
                {savingPrefs ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                {savingPrefs ? 'Saving...' : 'Set as Active Model'}
              </button>
              {prefsSaved && (
                <span className="text-xs text-emerald-400 flex items-center gap-1">
                  <Check size={11} /> Active model updated
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* ── Usage & Energy Dashboard ── */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wide flex items-center gap-1.5">
            <Activity size={12} /> Usage & Energy
          </p>
          <button
            onClick={handleResetUsage}
            disabled={resettingUsage || !usage?.total_calls}
            className="btn-ghost text-xs text-red-400 hover:text-red-300"
          >
            {resettingUsage ? <Loader2 size={11} className="animate-spin" /> : <RotateCcw size={11} />}
            Reset
          </button>
        </div>

        {!usage || usage.total_calls === 0 ? (
          <p className="text-xs text-[var(--text-muted)] text-center py-4">
            No usage data yet. Start using the research pipeline to see stats here.
          </p>
        ) : (
          <>
            {/* Top 4 stat cards */}
            <div className="grid grid-cols-4 gap-3">
              <StatCard
                icon={<Hash size={14} className="text-brand-400" />}
                label="Total Tokens"
                value={fmtTokens(usage.total_tokens)}
                sub={`${fmtTokens(usage.prompt_tokens)} in · ${fmtTokens(usage.completion_tokens)} out`}
              />
              <StatCard
                icon={<DollarSign size={14} className="text-emerald-400" />}
                label="API Cost"
                value={`$${fmt(usage.total_cost_usd, 4)}`}
                sub={`${usage.total_calls} calls`}
              />
              <StatCard
                icon={<Bolt size={14} className="text-yellow-400" />}
                label="Energy Used"
                value={fmtEnergy(usage.total_energy_wh)}
                sub="estimated"
                highlight
              />
              <StatCard
                icon={<Leaf size={14} className="text-green-400" />}
                label="CO₂ Equiv."
                value={fmtCO2(usage.total_energy_wh)}
                sub="avg grid mix"
              />
            </div>

            {/* Per-provider breakdown */}
            {Object.keys(usage.by_provider).length > 0 && (
              <div>
                <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-2">By Provider</p>
                <div className="space-y-1.5">
                  {Object.entries(usage.by_provider).map(([prov, stats]: any) => (
                    <div key={prov} className="flex items-center gap-3 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] px-3 py-2 text-xs">
                      <span className="text-base">{(() => { const IconComp = PROVIDER_ICON_COMPONENTS[prov] || Cpu; return <IconComp size={16} className="text-[var(--text-primary)]" />; })()}</span>
                      <span className="font-medium text-[var(--text-primary)] w-24 truncate capitalize">{prov}</span>
                      <span className="text-[var(--text-muted)] flex-1">{fmtTokens(stats.tokens)} tokens · {stats.calls} calls</span>
                      <span className="text-emerald-400">${fmt(stats.cost_usd, 4)}</span>
                      <span className="text-yellow-400 flex items-center gap-1"><Bolt size={10} />{fmtEnergy(stats.energy_wh)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Per-model breakdown */}
            {usage.by_model?.length > 0 && (
              <div>
                <p className="text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-2">By Model</p>
                <div className="space-y-1">
                  {usage.by_model.map((m: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-[var(--text-secondary)] px-1">
                      <span className="truncate flex-1 text-[var(--text-primary)]">{m.model}</span>
                      <span className="text-[var(--text-muted)]">{fmtTokens(m.tokens)}</span>
                      <span className="text-emerald-400">${fmt(m.cost_usd, 4)}</span>
                      <span className="text-yellow-400 flex items-center gap-1"><Bolt size={9} />{fmtEnergy(m.energy_wh)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recent calls toggle */}
            {usage.recent?.length > 0 && (
              <div>
                <button
                  onClick={() => setShowRecentCalls(v => !v)}
                  className="flex items-center gap-1.5 text-[10px] font-semibold text-[var(--text-muted)] uppercase tracking-wide hover:text-[var(--text-secondary)]"
                >
                  {showRecentCalls ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
                  Recent Calls ({usage.recent.length})
                </button>
                {showRecentCalls && (
                  <div className="mt-2 space-y-1">
                    {usage.recent.map((r: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] px-3 py-1.5 text-xs">
                        <span>{(() => { const IconComp = PROVIDER_ICON_COMPONENTS[r.provider] || Cpu; return <IconComp size={14} className="text-[var(--text-primary)]" />; })()}</span>
                        <span className="truncate flex-1 text-[var(--text-secondary)]">{r.model}</span>
                        <span className="text-[var(--text-muted)]">{fmtTokens(r.total_tokens)} tok</span>
                        <span className="text-emerald-400">${fmt(r.cost_usd, 5)}</span>
                        <span className="text-yellow-400 flex items-center gap-1"><Bolt size={9} />{fmtEnergy(r.energy_wh)}</span>
                        <span className="text-[var(--text-muted)] text-[10px]">{new Date(r.created_at).toLocaleTimeString()}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Energy context note */}
            <p className="text-[10px] text-[var(--text-muted)] border-t border-[var(--border)] pt-3">
              Energy estimates based on published GPU TDP and model size data. Groq LPU is ~10x more efficient than standard GPU inference.
              CO2 equivalent uses avg global grid mix (0.4 kg CO2/kWh). Local Ollama assumes ~0.5 Wh/1M tokens on a consumer GPU.
            </p>
          </>
        )}
      </div>
    </div>
  );
}

function StatCard({ icon, label, value, sub, highlight }: {
  icon: React.ReactNode; label: string; value: string; sub?: string; highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl border px-3 py-2.5 ${highlight ? 'border-yellow-500/30 bg-yellow-500/5' : 'border-[var(--border)] bg-[var(--bg-secondary)]'}`}>
      <div className="flex items-center gap-1.5 mb-1">{icon}<span className="text-[10px] text-[var(--text-muted)] uppercase tracking-wide">{label}</span></div>
      <p className="text-sm font-bold text-[var(--text-primary)]">{value}</p>
      {sub && <p className="text-[10px] text-[var(--text-muted)] mt-0.5">{sub}</p>}
    </div>
  );
}
