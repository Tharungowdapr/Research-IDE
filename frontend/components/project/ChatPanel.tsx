'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, MessageSquare, X, AlertCircle } from 'lucide-react';
import { chatAPI } from '@/services/api';

interface Message {
  role: 'user' | 'assistant' | 'error';
  content: string;
}

export default function ChatPanel({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;

    const userMsg: Message = { role: 'user', content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    const history = messages.map((m) => ({ role: m.role, content: m.content }));

    chatAPI.sendMessageStream(
      projectId,
      userMsg.content,
      history,
      (chunk) => {
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant') {
            return [...prev.slice(0, -1), { role: 'assistant', content: last.content + chunk }];
          }
          return [...prev, { role: 'assistant', content: chunk }];
        });
      },
      () => setLoading(false),
      (err) => {
        setLoading(false);
        const errMsg = err?.message || 'Failed to get response. Check your LLM provider settings.';
        setMessages((prev) => [...prev, { role: 'error', content: errMsg }]);
      },
    );
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-white shadow-lg hover:bg-brand-500 transition-all z-50"
      >
        <MessageSquare size={20} />
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 w-96 h-[500px] rounded-xl border border-[var(--border)] bg-[var(--bg-card)] shadow-2xl flex flex-col z-50">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--border)]">
        <div className="flex items-center gap-2">
          <MessageSquare size={14} className="text-brand-400" />
          <span className="text-sm font-medium text-[var(--text-primary)]">Research Chat</span>
        </div>
        <button onClick={() => setOpen(false)} className="btn-ghost p-1">
          <X size={14} />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <MessageSquare size={24} className="text-[var(--text-muted)] mb-2" />
            <p className="text-xs text-[var(--text-secondary)]">Ask questions about the retrieved papers,</p>
            <p className="text-xs text-[var(--text-secondary)]">gaps, ideas, or methodology.</p>
          </div>
        )}
        {messages.map((msg, i) => {
          if (msg.role === 'error') {
            return (
              <div key={i} className="flex justify-start">
                <div className="max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed bg-red-500/10 text-red-400 border border-red-500/20 flex items-start gap-1.5">
                  <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                  {msg.content}
                </div>
              </div>
            );
          }
          return (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] rounded-xl px-3 py-2 text-xs leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-brand-600/20 text-brand-400 border border-brand-500/20'
                    : 'bg-[var(--bg-secondary)] text-[var(--text-secondary)] border border-[var(--border)]'
                }`}
              >
                {msg.content}
              </div>
            </div>
          );
        })}
        {loading && (
          <div className="flex justify-start">
            <div className="rounded-xl px-3 py-2 text-xs bg-[var(--bg-secondary)] border border-[var(--border)]">
              <Loader2 size={12} className="animate-spin text-brand-400" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="border-t border-[var(--border)] p-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about the research..."
            className="input flex-1 text-xs"
            disabled={loading}
          />
          <button onClick={handleSend} disabled={loading || !input.trim()} className="btn-primary p-2">
            <Send size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
