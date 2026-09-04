'use client';

import React from 'react';
import { ArrowRight } from 'lucide-react';

interface SuggestedQuestionsProps {
  onSelectQuestion: (question: string) => void;
  hasDocuments: boolean;
}

export const SuggestedQuestions: React.FC<SuggestedQuestionsProps> = ({
  onSelectQuestion,
  hasDocuments,
}) => {
  const suggestions = [
    'Summarize the core conclusions across the uploaded documents',
    'Compare the main methodologies and findings between reports',
    'What key quantitative performance metrics or error rates are reported?',
    'Explain the primary limitations and future outlook mentioned',
  ];

  if (!hasDocuments) return null;

  return (
    <div className="w-full max-w-xl mx-auto my-6 text-left">
      <span className="text-[11px] font-semibold uppercase tracking-wider text-light-muted dark:text-dark-muted block mb-2 px-1">
        Suggested Research Prompts
      </span>

      <div className="space-y-1.5">
        {suggestions.map((query, idx) => (
          <button
            key={idx}
            onClick={() => onSelectQuestion(query)}
            className="w-full flex items-center justify-between p-2.5 rounded border border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface hover:bg-light-hover dark:hover:bg-dark-hover text-xs text-light-text dark:text-dark-text text-left transition-colors group"
          >
            <span className="truncate pr-2">{query}</span>
            <ArrowRight className="w-3.5 h-3.5 text-light-muted dark:text-dark-muted group-hover:text-accent flex-shrink-0 transition-colors" />
          </button>
        ))}
      </div>
    </div>
  );
};
