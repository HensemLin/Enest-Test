'use client';

import { SourceDocument } from '@/types';
import { FileText } from 'lucide-react';
import { truncate } from '@/lib/utils';

interface SourceCardProps {
  source: SourceDocument;
  index: number;
}

export function SourceCard({ source, index }: SourceCardProps) {
  // Convert FAISS distance score to similarity percentage
  // FAISS returns distance (lower = more similar), we convert to similarity (higher = more similar)
  // Using exponential decay: similarity = e^(-distance)
  // Then scale to 0-100%
  const similarity = Math.exp(-source.relevance_score);
  const relevancePercentage = Math.round(similarity * 100);

  const displayName = source.pdf_filename || `PDF ${source.pdf_id}`;

  return (
    <div className="flex gap-2 rounded-md border border-gray-200 bg-white p-2 text-xs hover:border-primary-300 hover:shadow-sm transition-all">
      <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded bg-primary-50">
        <FileText className="h-3 w-3 text-primary-600" />
      </div>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <span className="font-medium text-gray-900 text-xs" title={displayName}>
            [{index}] {displayName}, Page {source.page_number}
          </span>
          <span className="rounded-full bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700">
            {relevancePercentage}%
          </span>
        </div>
        <p className="text-gray-600 text-xs leading-snug line-clamp-2">
          {truncate(source.text_snippet, 100)}
        </p>
      </div>
    </div>
  );
}
