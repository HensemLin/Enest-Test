'use client';

import { PDFDocument } from '@/types';
import { formatDateTime, formatRelativeTime } from '@/lib/utils';
import { FileText, Trash2, FileSearch, Package } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface PDFListProps {
  pdfs: PDFDocument[];
  onDelete: (id: number) => void;
  onExtractRequirements: (id: number) => void;
  onExtractBom: (id: number) => void;
  isDeleting?: number;
  isExtractingReq?: number;
  isExtractingBom?: number;
}

export function PDFList({
  pdfs,
  onDelete,
  onExtractRequirements,
  onExtractBom,
  isDeleting,
  isExtractingReq,
  isExtractingBom,
}: PDFListProps) {
  if (pdfs.length === 0) {
    return (
      <Card className="p-12 text-center">
        <FileText className="mx-auto mb-4 h-12 w-12 text-gray-400" />
        <h3 className="mb-2 text-lg font-semibold text-gray-900">
          No PDFs uploaded yet
        </h3>
        <p className="text-sm text-gray-600">
          Upload your first PDF document to get started
        </p>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {pdfs.map((pdf) => (
        <Card key={pdf.id} className="p-4">
          <div className="flex items-start gap-4">
            <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-lg bg-primary-50">
              <FileText className="h-6 w-6 text-primary-600" />
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <h4 className="truncate font-semibold text-gray-900">
                  {pdf.original_filename}
                </h4>
                {pdf.status === 'processing' && (
                  <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
                    Processing...
                  </span>
                )}
                {pdf.status === 'ready' && pdf.last_extraction_date && (
                  <span className="inline-flex items-center rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-800">
                    Ready
                  </span>
                )}
                {pdf.status === 'failed' && (
                  <span className="inline-flex items-center rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-800">
                    Failed
                  </span>
                )}
              </div>
              <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-sm text-gray-600">
                <span>{pdf.page_count || 0} pages</span>
                <span>•</span>
                <span>Uploaded {formatRelativeTime(pdf.upload_date)}</span>
              </div>

              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onExtractRequirements(pdf.id)}
                  disabled={isExtractingReq === pdf.id || pdf.status === 'processing'}
                  className="gap-2"
                >
                  <FileSearch className="h-4 w-4" />
                  {isExtractingReq === pdf.id || pdf.status === 'processing'
                    ? 'Processing...'
                    : 'Extract Requirements'}
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onExtractBom(pdf.id)}
                  disabled={isExtractingBom === pdf.id || pdf.status === 'processing'}
                  className="gap-2"
                >
                  <Package className="h-4 w-4" />
                  {isExtractingBom === pdf.id || pdf.status === 'processing' ? 'Processing...' : 'Extract BoM'}
                </Button>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onDelete(pdf.id)}
                  disabled={isDeleting === pdf.id}
                  className="gap-2 text-red-600 hover:bg-red-50 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                  {isDeleting === pdf.id ? 'Deleting...' : 'Delete'}
                </Button>
              </div>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );
}
