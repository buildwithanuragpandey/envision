export type DocumentStatus = 'Uploaded' | 'Processing' | 'Indexed' | 'Failed';

export interface DocumentMetadata {
  document_id: string;
  filename: string;
  file_size_bytes: number;
  total_pages: number;
  chunk_count: number;
  document_hash: string;
  status: DocumentStatus;
  error_message?: string | null;
  created_at: string;
}

export interface SourceCitation {
  citation_id: number;
  filename: string;
  page_number: number;
  chunk_id: string;
  relevance_score: number;
  snippet: string;
}

export interface ChatHistoryItem {
  role: string;
  content: string;
}

export interface ChatRequest {
  message: string;
  session_id?: string;
  document_ids?: string[];
  history?: ChatHistoryItem[];
  top_k?: number;
}

export interface DebugInfo {
  retrieval_latency_ms: number;
  generation_latency_ms: number;
  total_latency_ms: number;
  retrieved_chunks_count: number;
  reformulated_query?: string | null;
  similarity_scores: number[];
  llm_provider: string;
  llm_model: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceCitation[];
  confidence?: number;
  is_grounded?: boolean;
  debug_info?: DebugInfo;
  created_at: string;
  isStreaming?: boolean;
}

export interface ProcessingAnalytics {
  total_documents: number;
  total_pages: number;
  total_chunks: number;
  indexed_documents: number;
  storage_size_bytes: number;
  active_llm_provider: string;
  active_llm_model: string;
  active_embedding_model: string;
}
