'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, FileText, Activity } from 'lucide-react';
import { ChatMessage as ChatMessageType, SourceCitation } from '@/types';

interface ChatMessageProps {
  message: ChatMessageType;
  onCitationClick?: (citation: SourceCitation) => void;
  onOpenDebug?: () => void;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({
  message,
  onCitationClick,
  onOpenDebug,
}) => {
  const [copied, setCopied] = useState(false);
  const [hoveredCitation, setHoveredCitation] = useState<SourceCitation | null>(null);
  const isUser = message.role === 'user';

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="py-4 border-b border-light-border/40 dark:border-dark-border/40">
        <div className="max-w-3xl mx-auto px-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-1.5">
            You
          </span>
          <div className="p-3 bg-light-subtle dark:bg-dark-subtle border border-light-border/80 dark:border-dark-border/80 rounded-md text-xs sm:text-sm text-light-text dark:text-dark-text whitespace-pre-wrap leading-relaxed">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // AI Response - Editorial layout rendered directly on page
  return (
    <div className="py-6 border-b border-light-border/40 dark:border-dark-border/40 relative">
      <div className="max-w-3xl mx-auto px-4">
        {/* Header */}
        <div className="flex items-center justify-between mb-3">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-accent">
            DocuMind AI
          </span>

          <div className="flex items-center gap-3 text-[11px] text-light-muted dark:text-dark-muted">
            {message.debug_info && onOpenDebug && (
              <button
                onClick={onOpenDebug}
                className="flex items-center gap-1 hover:text-light-text dark:hover:text-dark-text transition-colors"
                title="View RAG latency & similarity scores"
              >
                <Activity className="w-3 h-3" />
                <span className="font-mono">{message.debug_info.total_latency_ms.toFixed(0)}ms</span>
              </button>
            )}

            <button
              onClick={handleCopy}
              className="flex items-center gap-1 hover:text-light-text dark:hover:text-dark-text transition-colors"
            >
              {copied ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
              <span>{copied ? 'Copied' : 'Copy'}</span>
            </button>
          </div>
        </div>

        {/* Editorial Markdown Body */}
        <div className="editorial-prose text-light-text dark:text-dark-text">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              h1: ({ children }) => <h1 className="text-base font-semibold mt-4 mb-2">{children}</h1>,
              h2: ({ children }) => <h2 className="text-sm font-semibold mt-4 mb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-xs font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted mt-3 mb-1.5">{children}</h3>,
              p: ({ children }) => <p className="mb-2.5 leading-relaxed">{children}</p>,
              ul: ({ children }) => <ul className="list-disc pl-4 mb-2.5 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal pl-4 mb-2.5 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="text-light-text/90 dark:text-dark-text/90">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold text-light-text dark:text-dark-text">{children}</strong>,
              blockquote: ({ children }) => (
                <blockquote className="font-serif-doc my-2.5 italic border-l-2 border-light-border dark:border-dark-border pl-3 text-light-muted dark:text-dark-muted">
                  {children}
                </blockquote>
              ),
            }}
          >
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Sources Section at bottom of response */}
        {message.sources && message.sources.length > 0 && !message.isStreaming && (
          <div className="mt-5 pt-3 border-t border-light-border/60 dark:border-dark-border/60">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-2">
              Referenced Sources
            </span>
            <div className="flex flex-wrap gap-2">
              {message.sources.map((src) => (
                <div
                  key={src.chunk_id + src.citation_id}
                  className="relative group/src"
                  onMouseEnter={() => setHoveredCitation(src)}
                  onMouseLeave={() => setHoveredCitation(null)}
                >
                  <button
                    onClick={() => onCitationClick && onCitationClick(src)}
                    className="flex items-center gap-1.5 px-2 py-1 rounded bg-light-subtle dark:bg-dark-subtle hover:bg-light-hover dark:hover:bg-dark-hover border border-light-border dark:border-dark-border text-[11px] text-light-text dark:text-dark-text transition-colors"
                  >
                    <FileText className="w-3 h-3 text-light-muted dark:text-dark-muted" />
                    <span className="font-medium truncate max-w-[180px]">{src.filename}</span>
                    <span className="text-light-muted dark:text-dark-muted">· p.{src.page_number}</span>
                  </button>

                  {/* Fast Hover Preview Card */}
                  {hoveredCitation?.chunk_id === src.chunk_id && (
                    <div className="absolute bottom-full left-0 mb-2 w-72 p-3 bg-light-surface dark:bg-dark-surface border border-light-border dark:border-dark-border rounded-md shadow-flyout z-30 pointer-events-none animate-fade-in text-left">
                      <div className="flex items-center justify-between pb-1.5 mb-1.5 border-b border-light-border dark:border-dark-border text-[10px]">
                        <span className="font-semibold text-light-text dark:text-dark-text truncate">{src.filename}</span>
                        <span className="text-light-muted dark:text-dark-muted">Page {src.page_number}</span>
                      </div>
                      <p className="font-serif-doc text-[11px] text-light-muted dark:text-dark-muted line-clamp-4 italic leading-relaxed">
                        &ldquo;{src.snippet}&rdquo;
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
