'use client';

import React, { useState, useRef, ChangeEvent, DragEvent } from 'react';
import { Upload, X, Loader2, AlertCircle } from 'lucide-react';
import { uploadDocuments } from '@/lib/api';
import { DocumentMetadata } from '@/types';

interface DocumentUploaderProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (newDocs: DocumentMetadata[]) => void;
  disabled?: boolean;
}

export const DocumentUploader: React.FC<DocumentUploaderProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
  disabled = false,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleFiles = async (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const pdfFiles = fileArray.filter((file) => file.name.toLowerCase().endsWith('.pdf'));

    if (pdfFiles.length === 0) {
      setErrorMessage('Only PDF files are supported.');
      return;
    }

    setErrorMessage(null);
    setIsUploading(true);

    try {
      const response = await uploadDocuments(pdfFiles);
      onUploadSuccess(response.documents);
      onClose();
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to upload documents.');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (!disabled && !isUploading) setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (!disabled && !isUploading && e.dataTransfer.files) {
      handleFiles(e.dataTransfer.files);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFiles(e.target.files);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-md bg-light-surface dark:bg-dark-surface border border-light-border dark:border-dark-border rounded-lg shadow-modal p-5 text-xs text-light-text dark:text-dark-text">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-light-border dark:border-dark-border">
          <span className="font-semibold text-sm">Upload Documents</span>
          <button
            onClick={onClose}
            className="text-light-muted dark:text-dark-muted hover:text-light-text dark:hover:text-dark-text"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".pdf"
          className="hidden"
          onChange={handleInputChange}
          disabled={disabled || isUploading}
        />

        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !disabled && !isUploading && fileInputRef.current?.click()}
          className={`flex flex-col items-center justify-center p-8 border border-dashed rounded-md cursor-pointer transition-colors text-center ${
            isDragging
              ? 'border-accent bg-accent/5'
              : 'border-light-border dark:border-dark-border hover:bg-light-subtle dark:hover:bg-dark-subtle'
          } ${disabled || isUploading ? 'opacity-50 pointer-events-none' : ''}`}
        >
          {isUploading ? (
            <Loader2 className="w-6 h-6 animate-spin text-accent mb-2" />
          ) : (
            <Upload className="w-6 h-6 text-light-muted dark:text-dark-muted mb-2" />
          )}

          <p className="font-medium text-xs text-light-text dark:text-dark-text mb-0.5">
            {isUploading ? 'Extracting & Indexing...' : 'Click or drag PDF files here'}
          </p>
          <p className="text-[11px] text-light-muted dark:text-dark-muted">
            Upload up to 50 documents per session
          </p>
        </div>

        {errorMessage && (
          <div className="mt-3 p-2 rounded bg-red-500/10 border border-red-500/20 flex items-start gap-1.5 text-[11px] text-red-600 dark:text-red-400">
            <AlertCircle className="w-3.5 h-3.5 mt-0.5 flex-shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="flex justify-end gap-2 mt-4 pt-3 border-t border-light-border dark:border-dark-border">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded border border-light-border dark:border-dark-border text-light-muted dark:text-dark-muted hover:bg-light-subtle dark:hover:bg-dark-subtle"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
};
