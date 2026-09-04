import { DocumentMetadata, ProcessingAnalytics, ChatRequest, SourceCitation, DebugInfo } from '@/types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export async function fetchDocuments(): Promise<DocumentMetadata[]> {
  const res = await fetch(`${API_BASE}/api/documents`);
  if (!res.ok) throw new Error('Failed to fetch documents');
  return res.json();
}

export async function uploadDocuments(files: File[]): Promise<{ documents: DocumentMetadata[]; message: string }> {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const res = await fetch(`${API_BASE}/api/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function deleteDocument(documentId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/documents/${documentId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to delete document');
}

export async function clearAllDocuments(): Promise<void> {
  const res = await fetch(`${API_BASE}/api/documents`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Failed to clear documents');
}

export async function seedSampleDocuments(): Promise<{ documents: DocumentMetadata[]; message: string }> {
  const res = await fetch(`${API_BASE}/api/documents/seed_samples`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to seed sample documents');
  return res.json();
}

export async function fetchAnalytics(): Promise<ProcessingAnalytics> {
  const res = await fetch(`${API_BASE}/api/analytics`);
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

export interface StreamCallbacks {
  onToken: (token: string) => void;
  onSources: (sources: SourceCitation[]) => void;
  onDone: (payload: { confidence: number; is_grounded: boolean; debug_info?: DebugInfo }) => void;
  onError: (error: string) => void;
}

export async function streamChatMessage(
  request: ChatRequest,
  callbacks: StreamCallbacks
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: 'Failed to communicate with AI server' }));
      throw new Error(err.detail || 'Streaming failed');
    }

    if (!response.body) {
      throw new Error('Response body is empty');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const block of lines) {
        if (!block.trim()) continue;

        const eventMatch = block.match(/^event:\s*(\w+)/m);
        const dataMatch = block.match(/^data:\s*(.+)$/m);

        if (eventMatch && dataMatch) {
          const eventType = eventMatch[1];
          const rawData = dataMatch[1];

          try {
            const parsed = JSON.parse(rawData);
            if (eventType === 'token') {
              callbacks.onToken(parsed);
            } else if (eventType === 'sources') {
              callbacks.onSources(parsed);
            } else if (eventType === 'done') {
              callbacks.onDone(parsed);
            }
          } catch {
            // Handle plain string fallback
            if (eventType === 'token') {
              callbacks.onToken(rawData);
            }
          }
        }
      }
    }
  } catch (err: any) {
    callbacks.onError(err.message || 'Error streaming response');
  }
}
