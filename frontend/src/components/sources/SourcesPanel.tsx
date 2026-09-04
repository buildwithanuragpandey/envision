'use client';

import React from 'react';
import { SourceCitation } from '@/types';

interface SourcesPanelProps {
  sources: SourceCitation[];
  onSelectCitation: (citation: SourceCitation) => void;
}

export const SourcesPanel: React.FC<SourcesPanelProps> = ({
  sources,
  onSelectCitation,
}) => {
  return (
    <div className="flex flex-col h-full text-xs">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-light-border dark:border-dark-border">
        <span className="font-semibold uppercase tracking-wider text-[11px] text-light-text dark:text-dark-text">
          Sources
        </span>
        <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-light-subtle dark:bg-dark-subtle text-light-muted dark:text-dark-muted">
          {sources.length}
        </span>
      </div>

      {/* Sources List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-2.5">
        {sources.length === 0 ? (
          <div className="p-4 text-center text-light-muted dark:text-dark-muted">
            <p className="text-xs mb-1">No sources active.</p>
            <p className="text-[11px] text-light-muted/80 dark:text-dark-muted/80">
              When you ask a question, retrieved document sources and excerpts will appear here.
            </p>
          </div>
        ) : (
          sources.map((src) => (
            <div
              key={src.chunk_id + src.citation_id}
              onClick={() => onSelectCitation(src)}
              className="p-3 rounded border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface hover:bg-light-hover dark:hover:bg-dark-hover cursor-pointer transition-colors"
            >
              <div className="flex items-center justify-between mb-1 text-[11px]">
                <span className="font-semibold text-light-text dark:text-dark-text truncate pr-2">
                  {src.filename}
                </span>
                <span className="text-[10px] font-mono text-light-muted dark:text-dark-muted flex-shrink-0">
                  Page {src.page_number}
                </span>
              </div>

              <p className="font-serif-doc text-[11px] text-light-muted dark:text-dark-muted leading-relaxed line-clamp-4 italic mt-1.5">
                &ldquo;{src.snippet}&rdquo;
              </p>

              <div className="flex items-center justify-between mt-2 pt-2 border-t border-light-border/40 dark:border-dark-border/40 text-[10px] text-light-muted dark:text-dark-muted">
                <span>Score: {(src.relevance_score * 100).toFixed(0)}%</span>
                <span className="text-accent hover:underline">View excerpt →</span>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
