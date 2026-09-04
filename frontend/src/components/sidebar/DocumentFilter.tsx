'use client';

import React from 'react';
import { Filter, CheckSquare, Square } from 'lucide-react';
import { DocumentMetadata } from '@/types';

interface DocumentFilterProps {
  documents: DocumentMetadata[];
  selectedDocIds: string[];
  onToggleDoc: (docId: string) => void;
  onSelectAll: () => void;
  onClearFilter: () => void;
}

export const DocumentFilter: React.FC<DocumentFilterProps> = ({
  documents,
  selectedDocIds,
  onToggleDoc,
  onSelectAll,
  onClearFilter,
}) => {
  if (documents.length <= 1) return null;

  const isAllSelected = selectedDocIds.length === 0 || selectedDocIds.length === documents.length;

  return (
    <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 text-slate-300 font-medium">
          <Filter className="w-3.5 h-3.5 text-indigo-400" />
          <span>Targeted Search Filter</span>
        </div>
        <button
          onClick={isAllSelected ? onClearFilter : onSelectAll}
          className="text-[11px] text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          {isAllSelected ? 'Search All' : 'Select All'}
        </button>
      </div>

      <p className="text-[11px] text-slate-400 mb-2">
        Check documents to narrow AI retrieval to specific files:
      </p>

      <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
        {documents.map((doc) => {
          const isChecked = selectedDocIds.length === 0 || selectedDocIds.includes(doc.document_id);
          return (
            <label
              key={doc.document_id}
              onClick={() => onToggleDoc(doc.document_id)}
              className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-slate-800/80 cursor-pointer transition-all"
            >
              {isChecked ? (
                <CheckSquare className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
              ) : (
                <Square className="w-3.5 h-3.5 text-slate-600 flex-shrink-0" />
              )}
              <span className="text-[11px] text-slate-300 truncate">{doc.filename}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
};
