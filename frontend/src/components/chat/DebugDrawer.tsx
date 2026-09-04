'use client';

import React from 'react';
import { X } from 'lucide-react';
import { DebugInfo } from '@/types';

interface DebugDrawerProps {
  debugInfo: DebugInfo | null;
  isOpen: boolean;
  onClose: () => void;
}

export const DebugDrawer: React.FC<DebugDrawerProps> = ({
  debugInfo,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !debugInfo) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/30 backdrop-blur-xs">
      <div className="w-full max-w-sm h-full bg-light-surface dark:bg-dark-surface border-l border-light-border dark:border-dark-border shadow-modal flex flex-col animate-fade-in text-xs text-light-text dark:text-dark-text p-4 overflow-y-auto">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-light-border dark:border-dark-border">
          <span className="font-semibold text-xs uppercase tracking-wider text-light-text dark:text-dark-text">
            RAG Telemetry
          </span>
          <button
            onClick={onClose}
            className="p-1 rounded text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Latencies */}
        <div className="space-y-4">
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-2">
              Latency
            </span>
            <div className="space-y-1 font-mono text-xs">
              <div className="flex justify-between p-2 rounded bg-light-subtle dark:bg-dark-subtle">
                <span className="text-light-muted dark:text-dark-muted">Retrieval:</span>
                <span>{debugInfo.retrieval_latency_ms.toFixed(1)} ms</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-light-subtle dark:bg-dark-subtle">
                <span className="text-light-muted dark:text-dark-muted">Synthesis:</span>
                <span>{debugInfo.generation_latency_ms.toFixed(1)} ms</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-light-subtle dark:bg-dark-subtle font-semibold">
                <span className="text-light-muted dark:text-dark-muted">Total:</span>
                <span>{debugInfo.total_latency_ms.toFixed(1)} ms</span>
              </div>
            </div>
          </div>

          {/* Model info */}
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-2">
              Configuration
            </span>
            <div className="space-y-1 font-mono text-xs p-2 rounded bg-light-subtle dark:bg-dark-subtle">
              <div className="flex justify-between">
                <span className="text-light-muted dark:text-dark-muted">Provider:</span>
                <span className="capitalize">{debugInfo.llm_provider}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-light-muted dark:text-dark-muted">Model:</span>
                <span>{debugInfo.llm_model}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-light-muted dark:text-dark-muted">Chunks:</span>
                <span>{debugInfo.retrieved_chunks_count}</span>
              </div>
            </div>
          </div>

          {/* Similarity list */}
          {debugInfo.similarity_scores && debugInfo.similarity_scores.length > 0 && (
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-2">
                Chunk Similarities
              </span>
              <div className="space-y-1 font-mono text-xs">
                {debugInfo.similarity_scores.map((score, i) => (
                  <div key={i} className="flex justify-between p-2 rounded bg-light-subtle dark:bg-dark-subtle">
                    <span className="text-light-muted dark:text-dark-muted">Chunk [{i + 1}]</span>
                    <span>{(score * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {debugInfo.reformulated_query && (
            <div>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-2">
                Enriched Query
              </span>
              <div className="p-2 rounded bg-light-subtle dark:bg-dark-subtle font-mono text-[11px] text-light-muted dark:text-dark-muted break-words">
                {debugInfo.reformulated_query}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
