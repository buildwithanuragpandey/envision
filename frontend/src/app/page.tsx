'use client';

import React, { useState, useEffect } from 'react';
import {
  FileText,
  Moon,
  Sun,
  PanelLeft,
  PanelRight,
  Upload,
  Sparkles,
} from 'lucide-react';
import { DocumentList } from '@/components/sidebar/DocumentList';
import { DocumentUploader } from '@/components/sidebar/DocumentUploader';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { SourcesPanel } from '@/components/sources/SourcesPanel';
import { SourceSnippetModal } from '@/components/sources/SourceSnippetModal';
import { DebugDrawer } from '@/components/chat/DebugDrawer';
import {
  DocumentMetadata,
  ChatMessage,
  SourceCitation,
  DebugInfo,
  ProcessingAnalytics,
} from '@/types';
import {
  fetchDocuments,
  deleteDocument,
  clearAllDocuments,
  seedSampleDocuments,
  fetchAnalytics,
  streamChatMessage,
} from '@/lib/api';

export default function Home() {
  const [documents, setDocuments] = useState<DocumentMetadata[]>([]);
  const [selectedDocIds, setSelectedDocIds] = useState<string[]>([]);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [analytics, setAnalytics] = useState<ProcessingAnalytics | null>(null);
  const [activeSources, setActiveSources] = useState<SourceCitation[]>([]);
  const [activeCitationSnippet, setActiveCitationSnippet] = useState<SourceCitation | null>(null);
  const [isSnippetModalOpen, setIsSnippetModalOpen] = useState(false);
  const [debugInfo, setDebugInfo] = useState<DebugInfo | null>(null);
  const [isDebugDrawerOpen, setIsDebugDrawerOpen] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isSeeding, setIsSeeding] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const [showLeftSidebar, setShowLeftSidebar] = useState(true);
  const [showRightSidebar, setShowRightSidebar] = useState(true);

  // Sync theme
  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const loadData = async () => {
    try {
      const [docs, stats] = await Promise.all([
        fetchDocuments().catch(() => []),
        fetchAnalytics().catch(() => null),
      ]);
      setDocuments(docs);
      setAnalytics(stats);
    } catch (e) {
      console.error('Error loading initial data', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleUploadSuccess = (newDocs: DocumentMetadata[]) => {
    loadData();
  };

  const handleDeleteDocument = async (docId: string) => {
    try {
      await deleteDocument(docId);
      setSelectedDocIds((prev) => prev.filter((id) => id !== docId));
      loadData();
    } catch (e) {
      console.error('Failed to delete document', e);
    }
  };

  const handleClearAll = async () => {
    try {
      await clearAllDocuments();
      setDocuments([]);
      setSelectedDocIds([]);
      setActiveSources([]);
      loadData();
    } catch (e) {
      console.error('Failed to clear documents', e);
    }
  };

  const handleSeedSamples = async () => {
    setIsSeeding(true);
    try {
      await seedSampleDocuments();
      await loadData();
    } catch (e) {
      console.error('Failed to seed sample papers', e);
    } finally {
      setIsSeeding(false);
    }
  };

  const handleToggleDocFilter = (docId: string) => {
    setSelectedDocIds((prev) =>
      prev.includes(docId) ? prev.filter((id) => id !== docId) : [...prev, docId]
    );
  };

  const handleSendMessage = async (text: string) => {
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    const userMessage: ChatMessage = {
      id: userMsgId,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    };

    const initialAssistantMessage: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      sources: [],
      isStreaming: true,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage, initialAssistantMessage]);
    setIsLoading(true);

    const historyPayload = messages.slice(-8).map((m) => ({
      role: m.role,
      content: m.content,
    }));

    let accumulatedAnswer = '';

    await streamChatMessage(
      {
        message: text,
        document_ids: selectedDocIds.length > 0 ? selectedDocIds : undefined,
        history: historyPayload,
      },
      {
        onToken: (token) => {
          accumulatedAnswer += token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId ? { ...msg, content: accumulatedAnswer } : msg
            )
          );
        },
        onSources: (sources) => {
          setActiveSources(sources);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId ? { ...msg, sources } : msg
            )
          );
        },
        onDone: (payload) => {
          setDebugInfo(payload.debug_info || null);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    isStreaming: false,
                    confidence: payload.confidence,
                    is_grounded: payload.is_grounded,
                    debug_info: payload.debug_info,
                  }
                : msg
            )
          );
          setIsLoading(false);
          fetchAnalytics().then(setAnalytics).catch(() => {});
        },
        onError: (err) => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: `Error: ${err}. Please check server connection.`,
                    isStreaming: false,
                  }
                : msg
            )
          );
          setIsLoading(false);
        },
      }
    );
  };

  const handleOpenCitation = (citation: SourceCitation) => {
    setActiveCitationSnippet(citation);
    setIsSnippetModalOpen(true);
  };

  return (
    <main className="flex flex-col h-screen w-screen overflow-hidden bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text font-sans antialiased">
      {/* Workspace Top Bar */}
      <header className="h-12 border-b border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface flex items-center justify-between px-3 z-20">
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowLeftSidebar(!showLeftSidebar)}
            className="p-1 rounded text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text hover:bg-light-subtle dark:hover:bg-dark-subtle transition-colors"
            title="Toggle Documents Explorer"
          >
            <PanelLeft className="w-4 h-4" />
          </button>

          <div className="flex items-center gap-2">
            <span className="font-semibold text-xs text-light-text dark:text-dark-text tracking-tight">
              DocuMind AI
            </span>
            <span className="hidden sm:inline-block text-[11px] text-light-muted dark:text-dark-muted">
              / Document Research Workspace
            </span>
          </div>
        </div>

        {/* Right Header Actions */}
        <div className="flex items-center gap-2">
          {analytics && (
            <span className="hidden md:inline-block text-[11px] font-mono text-light-muted dark:text-dark-muted px-2 py-0.5 rounded bg-light-subtle dark:bg-dark-subtle">
              {analytics.indexed_documents} docs · {analytics.total_pages} pages
            </span>
          )}

          <button
            onClick={() => setIsDarkMode(!isDarkMode)}
            className="p-1.5 rounded text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text hover:bg-light-subtle dark:hover:bg-dark-subtle transition-colors"
            title={isDarkMode ? 'Switch to Light theme' : 'Switch to Dark theme'}
          >
            {isDarkMode ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
          </button>

          <button
            onClick={() => setShowRightSidebar(!showRightSidebar)}
            className="p-1 rounded text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text hover:bg-light-subtle dark:hover:bg-dark-subtle transition-colors"
            title="Toggle Sources Panel"
          >
            <PanelRight className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* 3-Column Workspace */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Column: Documents Explorer */}
        {showLeftSidebar && (
          <aside className="w-64 sm:w-72 border-r border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface flex flex-col flex-shrink-0 z-10">
            <DocumentList
              documents={documents}
              selectedDocIds={selectedDocIds}
              onToggleDoc={handleToggleDocFilter}
              onSelectAll={() => setSelectedDocIds([])}
              onClearFilter={() => setSelectedDocIds([])}
              onDeleteDocument={handleDeleteDocument}
              onClearAll={handleClearAll}
              onSeedSamples={handleSeedSamples}
              onOpenUpload={() => setIsUploadModalOpen(true)}
              isSeeding={isSeeding}
            />
          </aside>
        )}

        {/* Center Column: Research Chat */}
        <section className="flex-1 flex flex-col bg-light-bg dark:bg-dark-bg relative min-w-0">
          <ChatInterface
            messages={messages}
            isLoading={isLoading}
            onSendMessage={handleSendMessage}
            onClearChat={() => setMessages([])}
            onCitationClick={handleOpenCitation}
            onOpenDebug={(info) => {
              setDebugInfo(info);
              setIsDebugDrawerOpen(true);
            }}
            documents={documents}
            selectedDocIds={selectedDocIds}
            onClearFilter={() => setSelectedDocIds([])}
            latestDebugInfo={debugInfo}
            onOpenUpload={() => setIsUploadModalOpen(true)}
          />
        </section>

        {/* Right Column: Sources Panel */}
        {showRightSidebar && (
          <aside className="w-64 sm:w-72 border-l border-light-border dark:border-dark-border bg-light-surface dark:bg-dark-surface flex flex-col flex-shrink-0 z-10">
            <SourcesPanel
              sources={activeSources}
              onSelectCitation={handleOpenCitation}
            />
          </aside>
        )}
      </div>

      {/* Modals & Slide-over Drawers */}
      <DocumentUploader
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
        disabled={documents.length >= 50}
      />

      <SourceSnippetModal
        citation={activeCitationSnippet}
        isOpen={isSnippetModalOpen}
        onClose={() => setIsSnippetModalOpen(false)}
      />

      <DebugDrawer
        debugInfo={debugInfo}
        isOpen={isDebugDrawerOpen}
        onClose={() => setIsDebugDrawerOpen(false)}
      />
    </main>
  );
}
