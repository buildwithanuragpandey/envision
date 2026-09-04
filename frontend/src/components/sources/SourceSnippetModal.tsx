'use client';

import React from 'react';
import { X, FileText, ChevronLeft, ChevronRight } from 'lucide-react';
import { SourceCitation } from '@/types';

interface SourceSnippetModalProps {
  citation: SourceCitation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const SourceSnippetModal: React.FC<SourceSnippetModalProps> = ({
  citation,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !citation) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30 backdrop-blur-xs">
      <div className="w-full max-w-md h-full bg-light-surface dark:bg-dark-surface border-l border-light-border dark:border-dark-border shadow-modal flex flex-col animate-fade-in text-xs text-light-text dark:text-dark-text">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-light-border dark:border-dark-border">
          <div className="flex items-center gap-2 min-w-0 pr-2">
            <FileText className="w-4 h-4 text-light-muted dark:text-dark-muted flex-shrink-0" />
            <div className="min-w-0">
              <h3 className="font-semibold text-xs truncate">{citation.filename}</h3>
              <p className="text-[10px] text-light-muted dark:text-dark-muted">
                Page {citation.page_number} • Match {(citation.relevance_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text hover:bg-light-subtle dark:hover:bg-dark-subtle transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Excerpt Area */}
        <div className="flex-1 overflow-y-auto p-5">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-3">
            Source Document Excerpt
          </span>

          <div className="p-4 rounded border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg font-serif-doc text-xs sm:text-sm text-light-text/90 dark:text-dark-text/90 leading-relaxed whitespace-pre-wrap italic">
            {citation.snippet}
          </div>

          <div className="mt-4 p-3 rounded border border-light-border/60 dark:border-dark-border/60 bg-light-subtle dark:bg-dark-subtle text-[11px] text-light-muted dark:text-dark-muted space-y-1">
            <div className="flex justify-between">
              <span>Document:</span>
              <span className="font-mono text-light-text dark:text-dark-text truncate max-w-[200px]">{citation.filename}</span>
            </div>
            <div className="flex justify-between">
              <span>Page Number:</span>
              <span className="font-mono text-light-text dark:text-dark-text">{citation.page_number}</span>
            </div>
            <div className="flex justify-between">
              <span>Chunk ID:</span>
              <span className="font-mono text-light-text dark:text-dark-text">{citation.chunk_id.slice(0, 10)}...</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-light-border dark:border-dark-border flex items-center justify-between">
          <span className="text-[10px] text-light-muted dark:text-dark-muted">Verified RAG Citation</span>
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded border border-light-border dark:border-dark-border hover:bg-light-subtle dark:hover:bg-dark-subtle text-xs"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
