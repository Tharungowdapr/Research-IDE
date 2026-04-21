'use client';

import { useState, useEffect } from 'react';
import {
  Cpu, Key, Check, X, Loader2, Eye, EyeOff, ExternalLink,
  RefreshCw, Trash2, ChevronDown, Zap, Server, Globe,
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

interface OllamaModel {
  id: string;
  name: string;
  size: string;
}

const PROVIDER_ICONS: Record<string, string> = {
  openai: '🤖',
  anthropic: '🧠',
  groq: '⚡',
  gemini: '✨',
  cohere: '🌊',
  ollama: '🦙',
  openrouter: '🔀',
};

export default function LLMSettingsPage() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [keyStatus, setKeyStatus] = useState<KeyStatus | null>(null);
  const [ollamaModels, setOllamaModels] = useState<OllamaModel[]>([]);
  const [ollamaUrl, setOllamaUrl] = useState('http://localhost:11434');
  const [loading, setLoading] = useState(true);
  const [activeProvider, setActiveProvider] = useState<string | null>(null);

  // Per-provider state
  const [apiKeyInputs, setApiKeyInputs] = useState<Record<string, string>>({});
  const [showKeys, setShowKeys] = useState<Record<string, boolean>>({});
  const [savingKey, setSavingKey] = useState<string | null>(null);
  const [testingProvider, setTestingProvider] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { success: boolean; message: string }>>({});

  // Selected model state
  const [selectedProvider, setSelectedProvider] = useState('');
  const [selectedModel, setSelectedModel] = useState('');
  const [savingPrefs, setSavingPrefs] = useState(false);
  const [prefsSaved, setPrefsSaved] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [providersData, statusData] = await Promise.all([
        llmAPI.listProviders(),
        llmAPI.getKeysStatus(),
      ]);
      setProviders(providersData.providers);
      setKeyStatus(statusData);
      setSelectedProvider(statusData.preferred_provider || 'ollama');
      setSelectedModel(statusData.preferred_model || '');
      setOllamaUrl(statusData.ollama_base_url || 'http://localhost:11434');

      // Load Ollama models
      loadOllamaModels(statusData.ollama_base_url || 'http://localhost:11434');
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const loadOllamaModels = async (url: string) => {
    try {
      const data = await llmAPI.getOllamaModels(url);
      setOllamaModels(data.models || []);
    } catch {
      setOllamaModels([]);
    }
  };

  const handleSaveKey = async (provider: string) => {
    const key = apiKeyInputs[provider];
    if (!key?.trim()) return;
    setSavingKey(provider);
    try {
      await llmAPI.saveApiKey(provider, key.trim());
      setKeyStatus((prev) =>
        prev ? { ...prev, configured_providers: [...new Set([...prev.configured_providers, provider])] } : prev
      );
      setApiKeyInputs((prev) => ({ ...prev, [provider]: '' }));
    } catch (e) {
      console.error(e);
    } finally {
      setSavingKey(null);
    }
  };

  const handleDeleteKey = async (provider: string) => {
    try {
      await llmAPI.deleteApiKey(provider);
      setKeyStatus((prev) =>
        prev ? { ...prev, configured_providers: prev.configured_providers.filter((p) => p !== provider) } : prev
      );
    } catch (e) {
      console.error(e);
    }
  };

  const handleTest = async (provider: string) => {
    setTestingProvider(provider);
    setTestResults((prev) => ({ ...prev, [provider]: { success: false, message: 'Testing...' } }));
    try {
      const modelForTest = provider === selectedProvider ? selectedModel : undefined;
      const result = await llmAPI.testConnection({
        provider,
        model: modelForTest || undefined,
        ollama_base_url: provider === 'ollama' ? ollamaUrl : undefined,
      });
      setTestResults((prev) => ({
        ...prev,
        [provider]: {
          success: result.success,
          message: result.success ? `Connected! Response: "${result.response}"` : `Error: ${result.error}`,
        },
      }));
    } catch (e: any) {
      setTestResults((prev) => ({
        ...prev,
        [provider]: { success: false, message: `Failed: ${e.message}` },
      }));
    } finally {
      setTestingProvider(null);
    }
  };

  const handleSavePreferences = async () => {
    setSavingPrefs(true);
    try {
      await llmAPI.setPreferences(selectedProvider, selectedModel, ollamaUrl);
      setPrefsSaved(true);
      setTimeout(() => setPrefsSaved(false), 3000);
    } catch (e) {
      console.error(e);
    } finally {
      setSavingPrefs(false);
    }
  };

  const getAvailableModels = () => {
    const provider = providers.find((p) => p.id === selectedProvider);
    if (!provider) return [];
    if (selectedProvider === 'ollama') return ollamaModels.map((m) => ({ id: m.id, name: `${m.name} (${m.size})`, context: 'local' }));
    return provider.models;
  };

  const isConfigured = (providerId: string) =>
    providerId === 'ollama' || keyStatus?.configured_providers.includes(providerId);

  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center min-h-screen">
        <Loader2 size={24} className="animate-spin text-brand-400" />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600/20">
            <Cpu size={18} className="text-brand-400" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--text-primary)]">AI Model Settings</h1>
        </div>
        <p className="text-sm text-[var(--text-secondary)] ml-12">
          Configure your preferred LLM provider. Your API keys are encrypted and stored securely.
        </p>
      </div>

      {/* Active Model Selector */}
      <div className="card mb-6 border-brand-500/30 bg-brand-600/5">
        <div className="flex items-center gap-2 mb-4">
          <Zap size={16} className="text-brand-400" />
          <h2 className="font-semibold text-[var(--text-primary)]">Active Model</h2>
          <span className="text-xs text-[var(--text-muted)]">— used for all research tasks</span>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Provider</label>
            <select
              value={selectedProvider}
              onChange={(e) => { setSelectedProvider(e.target.value); setSelectedModel(''); }}
              className="input"
            >
              {providers.map((p) => (
                <option key={p.id} value={p.id} disabled={p.requires_key && !isConfigured(p.id)}>
                  {PROVIDER_ICONS[p.id]} {p.name} {p.requires_key && !isConfigured(p.id) ? '(no key)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">Model</label>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="input"
            >
              <option value="">Select model...</option>
              {getAvailableModels().map((m) => (
                <option key={m.id} value={m.id}>{m.name}</option>
              ))}
            </select>
          </div>
        </div>

        {selectedProvider === 'ollama' && (
          <div className="mt-3">
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
              Ollama Server URL
            </label>
            <div className="flex gap-2">
              <input
                type="text" className="input flex-1"
                placeholder="http://localhost:11434"
                value={ollamaUrl}
                onChange={(e) => setOllamaUrl(e.target.value)}
              />
              <button
                onClick={() => loadOllamaModels(ollamaUrl)}
                className="btn-secondary"
                title="Refresh models"
              >
                <RefreshCw size={14} />
              </button>
            </div>
            {ollamaModels.length === 0 && (
              <p className="text-xs text-yellow-400 mt-1.5 flex items-center gap-1">
                <Server size={11} />
                No Ollama models found. Make sure Ollama is running and has models installed.
                <a href="https://ollama.ai" target="_blank" className="underline hover:text-yellow-300">
                  Get Ollama
                </a>
              </p>
            )}
          </div>
        )}

        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={handleSavePreferences}
            disabled={savingPrefs || !selectedProvider || !selectedModel}
            className="btn-primary"
          >
            {savingPrefs ? <Loader2 size={14} className="animate-spin" /> : null}
            {savingPrefs ? 'Saving...' : 'Save Preferences'}
          </button>
          {prefsSaved && (
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <Check size={12} /> Saved!
            </span>
          )}
        </div>
      </div>

      {/* Provider Cards */}
      <h2 className="font-semibold text-[var(--text-primary)] mb-4">API Key Management</h2>
      <div className="space-y-3">
        {providers.map((provider) => {
          const configured = isConfigured(provider.id);
          const isExpanded = activeProvider === provider.id;
          const testResult = testResults[provider.id];

          return (
            <div
              key={provider.id}
              className={`card transition-all ${configured ? 'border-emerald-500/20' : ''}`}
            >
              {/* Provider Header */}
              <button
                onClick={() => setActiveProvider(isExpanded ? null : provider.id)}
                className="w-full flex items-center gap-3 text-left"
              >
                <span className="text-xl">{PROVIDER_ICONS[provider.id]}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-[var(--text-primary)]">{provider.name}</span>
                    {configured ? (
                      <span className="badge-green"><Check size={10} /> Configured</span>
                    ) : provider.requires_key ? (
                      <span className="badge-yellow">Key required</span>
                    ) : (
                      <span className="badge-blue">No key needed</span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--text-muted)] truncate">{provider.description}</p>
                </div>
                <ChevronDown
                  size={16}
                  className={`text-[var(--text-muted)] transition-transform flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
                />
              </button>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="mt-4 pt-4 border-t border-[var(--border)] space-y-4">
                  {/* Ollama: no key needed */}
                  {!provider.requires_key && (
                    <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-3 text-xs text-blue-400">
                      <p className="font-medium mb-1">No API key required</p>
                      <p>Ollama runs completely locally on your machine. Install Ollama, pull models, and configure the URL above.</p>
                      <a
                        href="https://ollama.ai"
                        target="_blank"
                        className="inline-flex items-center gap-1 mt-2 underline hover:text-blue-300"
                      >
                        <Globe size={11} /> Visit ollama.ai <ExternalLink size={11} />
                      </a>
                    </div>
                  )}

                  {/* API Key Input */}
                  {provider.requires_key && (
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <label className="text-xs font-medium text-[var(--text-secondary)]">
                          {configured ? 'Update API Key' : 'Enter API Key'}
                        </label>
                        <a
                          href={provider.get_key_url}
                          target="_blank"
                          className="flex items-center gap-1 text-xs text-brand-400 hover:text-brand-300"
                        >
                          Get key <ExternalLink size={11} />
                        </a>
                      </div>
                      <div className="flex gap-2">
                        <div className="relative flex-1">
                          <input
                            type={showKeys[provider.id] ? 'text' : 'password'}
                            className="input pr-8"
                            placeholder={configured ? '••••••••••••••• (stored)' : 'sk-...'}
                            value={apiKeyInputs[provider.id] || ''}
                            onChange={(e) =>
                              setApiKeyInputs((prev) => ({ ...prev, [provider.id]: e.target.value }))
                            }
                          />
                          <button
                            type="button"
                            onClick={() => setShowKeys((prev) => ({ ...prev, [provider.id]: !prev[provider.id] }))}
                            className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[var(--text-muted)]"
                          >
                            {showKeys[provider.id] ? <EyeOff size={13} /> : <Eye size={13} />}
                          </button>
                        </div>
                        <button
                          onClick={() => handleSaveKey(provider.id)}
                          disabled={!apiKeyInputs[provider.id]?.trim() || savingKey === provider.id}
                          className="btn-primary"
                        >
                          {savingKey === provider.id ? <Loader2 size={14} className="animate-spin" /> : <Key size={14} />}
                          Save
                        </button>
                        {configured && (
                          <button
                            onClick={() => handleDeleteKey(provider.id)}
                            className="btn-secondary text-red-400 hover:text-red-300"
                            title="Remove key"
                          >
                            <Trash2 size={14} />
                          </button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Available Models */}
                  {provider.models.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-[var(--text-secondary)] mb-2">Available Models</p>
                      <div className="grid grid-cols-2 gap-2">
                        {provider.models.map((m) => (
                          <div key={m.id} className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2">
                            <p className="text-xs font-medium text-[var(--text-primary)]">{m.name}</p>
                            <p className="text-[10px] text-[var(--text-muted)]">Context: {m.context}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Test Connection */}
                  <div>
                    <button
                      onClick={() => handleTest(provider.id)}
                      disabled={testingProvider === provider.id || (provider.requires_key && !configured)}
                      className="btn-secondary text-xs"
                    >
                      {testingProvider === provider.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Zap size={13} />
                      )}
                      Test Connection
                    </button>
                    {testResult && (
                      <div
                        className={`mt-2 rounded-lg px-3 py-2 text-xs ${
                          testResult.success
                            ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                            : 'bg-red-500/10 border border-red-500/20 text-red-400'
                        }`}
                      >
                        {testResult.success ? <Check size={12} className="inline mr-1" /> : <X size={12} className="inline mr-1" />}
                        {testResult.message}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Info Box */}
      <div className="mt-6 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-4 text-xs text-[var(--text-muted)]">
        <p className="font-medium text-[var(--text-secondary)] mb-1">Security Note</p>
        <p>
          API keys are encrypted before storage using AES-256 encryption. Keys are never logged or exposed in responses.
          For maximum security, use environment-specific keys and rotate them regularly.
        </p>
      </div>
    </div>
  );
}
