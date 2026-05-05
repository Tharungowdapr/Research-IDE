'use client';

import { useState, useCallback, useRef } from 'react';
import { useAuthStore } from '@/store/useAuthStore';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface StreamOptions {
  onResult?: (data: any) => void;
  onDone?: () => void;
  onError?: (msg: string) => void;
}

async function refreshAccessToken(refreshToken: string): Promise<string | null> {
  try {
    const r = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!r.ok) return null;
    const data = await r.json();
    return data.access_token as string;
  } catch {
    return null;
  }
}

async function doStream(
  url: string,
  token: string,
  options: StreamOptions,
  onProgress: (msg: string) => void,
  onError: (msg: string) => void,
  signal: AbortSignal,
): Promise<void> {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
    signal,
  });

  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();
  if (!reader) throw new Error('No stream body received');

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const text = decoder.decode(value, { stream: true });
    for (const line of text.split('\n')) {
      if (!line.startsWith('data:')) continue;
      try {
        const evt = JSON.parse(line.slice(5).trim());
        if (evt.type === 'progress') onProgress(evt.message);
        else if (evt.type === 'result') options.onResult?.(evt.data);
        else if (evt.type === 'done') options.onDone?.();
        else if (evt.type === 'error') onError(evt.message);
      } catch {}
    }
  }
}

export function useStream() {
  const [streaming, setStreaming] = useState(false);
  const [log, setLog] = useState<string[]>([]);
  const [error, setError] = useState('');
  const abortRef = useRef<AbortController | null>(null);

  const stream = useCallback(async (
    projectId: string,
    stage: string,
    options: StreamOptions = {}
  ) => {
    // Abort any in-progress stream
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStreaming(true);
    setLog([]);
    setError('');

    const { accessToken, refreshToken, setAccessToken } = useAuthStore.getState();
    if (!accessToken) {
      setError('Not authenticated. Please log in.');
      setStreaming(false);
      return;
    }

    const url = `${API_URL}/api/agents/stream/${projectId}/${stage}`;
    const onProgress = (msg: string) => setLog(prev => [...prev, msg]);
    const onError = (msg: string) => setError(msg);

    try {
      await doStream(url, accessToken, options, onProgress, onError, controller.signal);
    } catch (e: any) {
      if (e.name === 'AbortError') return;

      // Try token refresh on auth error
      if (e.message.includes('401') && refreshToken) {
        const newToken = await refreshAccessToken(refreshToken);
        if (newToken) {
          setAccessToken(newToken);
          try {
            await doStream(url, newToken, options, onProgress, onError, controller.signal);
            return;
          } catch (retryErr: any) {
            if (retryErr.name === 'AbortError') return;
            setError(retryErr.message || 'Stream failed after token refresh');
          }
        } else {
          setError('Session expired. Please log in again.');
        }
      } else {
        setError(e.message || 'Stream connection failed');
        options.onError?.(e.message);
      }
    } finally {
      setStreaming(false);
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
    setStreaming(false);
  }, []);

  return { stream, cancel, streaming, log, error, setError };
}
