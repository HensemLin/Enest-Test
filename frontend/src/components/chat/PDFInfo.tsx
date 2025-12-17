'use client';

import { PDFDocument } from '@/types';
import { FileText, ChevronDown, ChevronRight } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { useState } from 'react';

interface PDFInfoProps {
  pdfs: PDFDocument[];
  sessionPdfIds: number[];
  isLoading?: boolean;
}

export function PDFInfo({ pdfs, sessionPdfIds, isLoading }: PDFInfoProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  // Filter to only show PDFs that are in this session
  const sessionPdfs = pdfs.filter((pdf) => sessionPdfIds.includes(pdf.id));

  return (
    <Card className="border-l-4 border-l-primary-500">
      <div className="p-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex w-full items-center justify-between text-left"
        >
          <div className="flex items-center gap-2">
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-gray-500" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-500" />
            )}
            <h3 className="font-semibold text-gray-900">
              Chatting with {sessionPdfIds.length} PDF{sessionPdfIds.length !== 1 ? 's' : ''}
            </h3>
          </div>
        </button>

        {isExpanded && (
          <div className="mt-4 space-y-2">
            {isLoading ? (
              <p className="text-sm text-gray-500">Loading PDFs...</p>
            ) : sessionPdfs.length === 0 ? (
              <div className="rounded-lg bg-yellow-50 p-3 text-sm">
                <p className="font-medium text-yellow-800">No PDFs loaded</p>
                <p className="mt-1 text-xs text-yellow-700">
                  The PDFs for this session may have been deleted.
                </p>
              </div>
            ) : (
              sessionPdfs.map((pdf) => (
                <div
                  key={pdf.id}
                  className="flex items-start gap-3 rounded-lg border border-gray-200 bg-white p-3"
                >
                  <FileText className="h-5 w-5 flex-shrink-0 text-primary-600 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p
                      className="text-sm font-medium text-gray-900 break-words line-clamp-2"
                      title={pdf.original_filename}
                    >
                      {pdf.original_filename}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      {pdf.page_count || 0} pages
                    </p>
                  </div>
                </div>
              ))
            )}

            {sessionPdfs.length > 0 && (
              <div className="mt-3 rounded-lg bg-blue-50 p-3">
                <p className="text-xs text-blue-700">
                  💡 <strong>Tip:</strong> Want to chat with different PDFs? Create a new session from the dashboard.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
