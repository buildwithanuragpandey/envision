'use client';

import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';
import { ArrowUp, Trash2, Upload, SlidersHorizontal } from 'lucide-react';
import { ChatMessage as ChatMessageType, SourceCitation, DebugInfo, DocumentMetadata } from '@/types';
import { ChatMessage } from './ChatMessage';
import { SuggestedQuestions } from './SuggestedQuestions';
import { TypingIndicator } from './TypingIndicator';

interface ChatInterfaceProps {
  messages: ChatMessageType[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  onClearChat: () => void;
  onCitationClick: (citation: SourceCitation) => void;
  onOpenDebug: (debugInfo: DebugInfo) => void;
  documents: DocumentMetadata[];
  selectedDocIds: string[];
  onClearFilter: () => void;
  latestDebugInfo: DebugInfo | null;
  onOpenUpload: () => void;
}

export const ChatInterface: React.FC<ChatInterfaceProps> = ({
  messages,
  isLoading,
  onSendMessage,
  onClearChat,
  onCitationClick,
  onOpenDebug,
  documents,
  selectedDocIds,
  onClearFilter,
  latestDebugInfo,
  onOpenUpload,
}) => {
  const [inputText, setInputText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isLoading || documents.length === 0) return;
    onSendMessage(inputText.trim());
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = `${Math.min(e.target.scrollHeight, 120)}px`;
  };

  const isFiltered = selectedDocIds.length > 0 && selectedDocIds.length < documents.length;

  return (
    <div className="flex flex-col h-full relative select-text">
      {/* Subheader / Context Bar */}
      {isFiltered && (
        <div className="px-4 py-1.5 bg-light-subtle dark:bg-dark-subtle border-b border-light-border dark:border-dark-border flex items-center justify-between text-[11px] text-light-muted dark:text-dark-muted">
          <span>Search scoped to {selectedDocIds.length} of {documents.length} documents</span>
          <button onClick={onClearFilter} className="text-accent hover:underline">
            Reset filter
          </button>
        </div>
      )}

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center min-h-[65vh] text-center px-4">
            {documents.length === 0 ? (
              <div className="max-w-md mx-auto">
                <h1 className="text-base sm:text-lg font-semibold text-light-text dark:text-dark-text mb-2 tracking-tight">
                  Welcome to your research workspace
                </h1>
                <p className="text-xs text-light-muted dark:text-dark-muted mb-5 leading-relaxed">
                  Upload PDF documents to begin exploring and asking questions across your files.
                </p>
                <button
                  onClick={onOpenUpload}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-accent hover:bg-accent-hover rounded transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Upload documents</span>
                </button>
              </div>
            ) : (
              <div className="max-w-md mx-auto">
                <h1 className="text-base sm:text-lg font-semibold text-light-text dark:text-dark-text mb-2 tracking-tight">
                  What would you like to understand?
                </h1>
                <p className="text-xs text-light-muted dark:text-dark-muted mb-4 leading-relaxed">
                  Search and compare information across your {documents.length} uploaded documents.
                </p>

                <SuggestedQuestions
                  onSelectQuestion={onSendMessage}
                  hasDocuments={documents.length > 0}
                />
              </div>
            )}
          </div>
        ) : (
          <div>
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                message={msg}
                onCitationClick={onCitationClick}
                onOpenDebug={msg.debug_info ? () => onOpenDebug(msg.debug_info!) : undefined}
              />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Minimal Prompt Input */}
      <div className="p-4 border-t border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
          <div className="flex items-end gap-2 p-2 rounded-lg border border-light-border dark:border-dark-border bg-light-bg dark:bg-dark-bg focus-within:border-accent transition-colors">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder={
                documents.length === 0
                  ? 'Upload documents first...'
                  : 'Ask anything about your documents... (Enter to send)'
              }
              disabled={isLoading || documents.length === 0}
              className="flex-1 max-h-32 p-1 bg-transparent text-xs sm:text-sm text-light-text dark:text-dark-text placeholder-light-muted dark:placeholder-dark-muted resize-none outline-none disabled:opacity-50 font-sans"
            />

            <button
              type="submit"
              disabled={!inputText.trim() || isLoading || documents.length === 0}
              className="p-1.5 rounded text-white bg-accent hover:bg-accent-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all flex-shrink-0"
              title="Send question (Enter)"
            >
              <ArrowUp className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center justify-between mt-2 px-1 text-[10px] text-light-muted dark:text-dark-muted">
            <span>Shift + Enter for new line</span>
            {messages.length > 0 && (
              <button
                type="button"
                onClick={onClearChat}
                className="hover:text-red-600 transition-colors"
              >
                Clear conversation
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};
