'use client';

import { useState } from 'react';
import { PDFDocument } from '@/types';
import { FileText, ChevronDown, ChevronRight, CheckSquare, Square } from 'lucide-react';
import { Card } from '@/components/ui/card';

interface PDFSelectorProps {
  pdfs: PDFDocument[];
  selectedPdfIds: number[];
  onSelectionChange: (pdfIds: number[]) => void;
  isLoading?: boolean;
  error?: any;
}

export function PDFSelector({ pdfs, selectedPdfIds, onSelectionChange, isLoading, error }: PDFSelectorProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleToggle = (pdfId: number) => {
    if (selectedPdfIds.includes(pdfId)) {
      onSelectionChange(selectedPdfIds.filter((id) => id !== pdfId));
    } else {
      onSelectionChange([...selectedPdfIds, pdfId]);
    }
  };

  const handleSelectAll = () => {
    if (selectedPdfIds.length === pdfs.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(pdfs.map((pdf) => pdf.id));
    }
  };

  const allSelected = pdfs.length > 0 && selectedPdfIds.length === pdfs.length;

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
              Selected PDFs ({selectedPdfIds.length})
            </h3>
          </div>
          {pdfs.length > 0 && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                handleSelectAll();
              }}
              className="text-xs text-primary-600 hover:text-primary-700"
            >
              {allSelected ? 'Deselect All' : 'Select All'}
            </button>
          )}
        </button>

        {isExpanded && (
          <div className="mt-4 space-y-2">
            {isLoading ? (
              <p className="text-sm text-gray-500">Loading PDFs...</p>
            ) : error ? (
              <div className="text-sm">
                <p className="text-red-600">Failed to load PDFs</p>
                <p className="text-xs text-gray-500 mt-1">
                  Check console for details
                </p>
              </div>
            ) : pdfs.length === 0 ? (
              <p className="text-sm text-gray-500">
                No PDFs uploaded yet. Upload PDFs in the PDFs page first.
              </p>
            ) : (
              pdfs.map((pdf) => {
                const isSelected = selectedPdfIds.includes(pdf.id);
                return (
                  <button
                    key={pdf.id}
                    onClick={() => handleToggle(pdf.id)}
                    title={pdf.original_filename}
                    className={`flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50'
                        : 'border-gray-200 bg-white hover:border-primary-300'
                    }`}
                  >
                    {isSelected ? (
                      <CheckSquare className="h-5 w-5 flex-shrink-0 text-primary-600" />
                    ) : (
                      <Square className="h-5 w-5 flex-shrink-0 text-gray-400" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start gap-2">
                        <FileText className="h-4 w-4 flex-shrink-0 text-primary-600 mt-0.5" />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-gray-900 break-words line-clamp-2" title={pdf.original_filename}>
                            {pdf.original_filename}
                          </p>
                          <p className="mt-1 text-xs text-gray-500">
                            {pdf.page_count || 0} pages
                          </p>
                        </div>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        )}
      </div>
    </Card>
  );
}
