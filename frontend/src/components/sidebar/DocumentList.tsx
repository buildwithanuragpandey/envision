'use client';

import React, { useState } from 'react';
import {
  FileText,
  Trash2,
  Search,
  Plus,
  Sparkles,
  CheckSquare,
  Square,
  ChevronRight,
  Filter,
} from 'lucide-react';
import { DocumentMetadata } from '@/types';
import { formatBytes } from '@/lib/utils';

interface DocumentListProps {
  documents: DocumentMetadata[];
  selectedDocIds: string[];
  onToggleDoc: (docId: string) => void;
  onSelectAll: () => void;
  onClearFilter: () => void;
  onDeleteDocument: (docId: string) => void;
  onClearAll: () => void;
  onSeedSamples: () => void;
  onOpenUpload: () => void;
  isSeeding?: boolean;
}

export const DocumentList: React.FC<DocumentListProps> = ({
  documents,
  selectedDocIds,
  onToggleDoc,
  onSelectAll,
  onClearFilter,
  onDeleteDocument,
  onClearAll,
  onSeedSamples,
  onOpenUpload,
  isSeeding = false,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredDocs = documents.filter((d) =>
    d.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const isAllSelected = selectedDocIds.length === 0 || selectedDocIds.length === documents.length;

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'Indexed':
        return <span className="inline-block w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400" title="Indexed" />;
      case 'Processing':
        return <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" title="Processing" />;
      default:
        return <span className="inline-block w-1.5 h-1.5 rounded-full bg-red-500" title="Failed" />;
    }
  };

  return (
    <div className="flex flex-col h-full select-none text-xs">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-light-border dark:border-dark-border">
        <div className="flex items-center gap-1.5">
          <span className="font-semibold uppercase tracking-wider text-[11px] text-light-text dark:text-dark-text">
            Documents
          </span>
          <span className="px-1.5 py-0.2 rounded text-[10px] font-mono bg-light-subtle dark:bg-dark-subtle text-light-muted dark:text-dark-muted">
            {documents.length}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {documents.length > 0 && (
            <button
              onClick={onClearAll}
              className="text-[11px] text-light-muted dark:text-dark-muted hover:text-red-600 transition-colors"
            >
              Clear
            </button>
          )}
          <button
            onClick={onOpenUpload}
            className="flex items-center gap-1 px-2 py-1 text-[11px] font-medium text-white bg-accent hover:bg-accent-hover rounded transition-colors"
            title="Upload PDF documents"
          >
            <Plus className="w-3 h-3" />
            <span>Add</span>
          </button>
        </div>
      </div>

      {/* Search & Filter Bar */}
      {documents.length > 0 && (
        <div className="p-2 border-b border-light-border dark:border-dark-border">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-2 text-light-muted dark:text-dark-muted" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents..."
              className="w-full pl-8 pr-2.5 py-1.5 text-xs bg-light-surface dark:bg-dark-surface border border-light-border dark:border-dark-border rounded outline-none focus:border-accent text-light-text dark:text-dark-text placeholder-light-muted dark:placeholder-dark-muted"
            />
          </div>

          {documents.length > 1 && (
            <div className="flex items-center justify-between mt-2 px-1 text-[10px] text-light-muted dark:text-dark-muted">
              <span>{isAllSelected ? 'Searching all files' : `Filtered (${selectedDocIds.length} active)`}</span>
              <button
                onClick={isAllSelected ? () => onToggleDoc(documents[0].document_id) : onClearFilter}
                className="hover:text-accent transition-colors"
              >
                {isAllSelected ? 'Filter' : 'Reset'}
              </button>
            </div>
          )}
        </div>
      )}

      {/* Document List */}
      <div className="flex-1 overflow-y-auto py-1.5 space-y-0.5">
        {documents.length === 0 ? (
          <div className="p-4 text-center text-light-muted dark:text-dark-muted">
            <p className="text-xs mb-2">No documents loaded.</p>
            <p className="text-[11px] mb-3 text-light-muted/80 dark:text-dark-muted/80">
              Upload your PDFs or load sample research papers to begin.
            </p>
            <button
              onClick={onSeedSamples}
              disabled={isSeeding}
              className="w-full py-1.5 px-2.5 text-xs border border-light-border dark:border-dark-border hover:bg-light-subtle dark:hover:bg-dark-subtle text-light-text dark:text-dark-text rounded transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              <Sparkles className="w-3 h-3 text-accent" />
              <span>{isSeeding ? 'Loading...' : 'Load Sample Papers'}</span>
            </button>
          </div>
        ) : (
          filteredDocs.map((doc) => {
            const isSelected = selectedDocIds.length === 0 || selectedDocIds.includes(doc.document_id);
            return (
              <div
                key={doc.document_id}
                className={`group flex items-center justify-between px-2.5 py-2 mx-1 rounded cursor-pointer transition-colors ${
                  isSelected
                    ? 'bg-light-surface dark:bg-dark-surface hover:bg-light-hover dark:hover:bg-dark-hover border border-light-border/60 dark:border-dark-border/60'
                    : 'opacity-50 hover:opacity-80 hover:bg-light-subtle dark:hover:bg-dark-subtle border border-transparent'
                }`}
                onClick={() => onToggleDoc(doc.document_id)}
              >
                <div className="flex items-start gap-2 min-w-0 pr-1">
                  <div className="mt-0.5 text-light-muted dark:text-dark-muted group-hover:text-light-text dark:group-hover:text-dark-text transition-colors">
                    <FileText className="w-3.5 h-3.5" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5">
                      <span className="font-medium text-light-text dark:text-dark-text truncate block text-xs">
                        {doc.filename}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 text-[10px] text-light-muted dark:text-dark-muted">
                      <span>{doc.total_pages} {doc.total_pages === 1 ? 'page' : 'pages'}</span>
                      <span>•</span>
                      <span>{getStatusIndicator(doc.status)}</span>
                      <span>{doc.status}</span>
                    </div>
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteDocument(doc.document_id);
                  }}
                  className="p-1 text-light-muted dark:text-dark-muted hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Remove from session"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* Footer info */}
      {documents.length > 0 && (
        <div className="p-2.5 border-t border-light-border dark:border-dark-border flex items-center justify-between text-[10px] text-light-muted dark:text-dark-muted">
          <span>{documents.length} / 50 files indexed</span>
          <button
            onClick={onSeedSamples}
            disabled={isSeeding}
            className="hover:text-accent transition-colors"
          >
            {isSeeding ? 'Reloading...' : '+ Samples'}
          </button>
        </div>
      )}
    </div>
  );
};
