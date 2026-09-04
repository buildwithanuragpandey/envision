'use client';

import React from 'react';

export const TypingIndicator: React.FC = () => {
  return (
    <div className="py-4">
      <div className="max-w-3xl mx-auto px-4">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-accent block mb-2">
          DocuMind AI
        </span>
        <div className="flex items-center gap-2 text-xs text-light-muted dark:text-dark-muted font-mono">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          <span>Synthesizing answer from retrieved document context...</span>
        </div>
      </div>
    </div>
  );
};
