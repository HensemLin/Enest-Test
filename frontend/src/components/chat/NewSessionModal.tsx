"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { pdfAPI, chatAPI } from "@/lib/api";
import { PDFDocument } from "@/types";
import {
  FileText,
  CheckSquare,
  Square,
  X,
  Loader2,
  AlertCircle,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { generateSessionId } from "@/lib/utils";

interface NewSessionModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function NewSessionModal({ isOpen, onClose }: NewSessionModalProps) {
  const router = useRouter();
  const [selectedPdfIds, setSelectedPdfIds] = useState<number[]>([]);

  // Fetch available PDFs
  const {
    data: pdfs,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["pdfs"],
    queryFn: () => pdfAPI.getAll(),
    enabled: isOpen,
    retry: 1,
  });

  const handleToggle = (pdfId: number) => {
    if (selectedPdfIds.includes(pdfId)) {
      setSelectedPdfIds(selectedPdfIds.filter((id) => id !== pdfId));
    } else {
      setSelectedPdfIds([...selectedPdfIds, pdfId]);
    }
  };

  const handleSelectAll = () => {
    if (pdfs && selectedPdfIds.length === pdfs.length) {
      setSelectedPdfIds([]);
    } else if (pdfs) {
      setSelectedPdfIds(pdfs.map((pdf: { id: number }) => pdf.id));
    }
  };

  const createSessionMutation = useMutation({
    mutationFn: async (pdfIds: number[]) => {
      const sessionId = generateSessionId();
      // Store selected PDFs in localStorage for this session
      localStorage.setItem(`session-${sessionId}-pdfs`, JSON.stringify(pdfIds));
      return sessionId;
    },
    onSuccess: (sessionId) => {
      onClose();
      setSelectedPdfIds([]);
      router.push(`/chat/${sessionId}`);
    },
  });

  const handleCreateSession = () => {
    if (selectedPdfIds.length > 0) {
      createSessionMutation.mutate(selectedPdfIds);
    }
  };

  if (!isOpen) return null;

  const allSelected =
    pdfs && pdfs.length > 0 && selectedPdfIds.length === pdfs.length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <Card className="max-h-[80vh] w-full max-w-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-200 p-6">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Select PDFs for New Session
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              Choose which PDFs you want to chat with in this session
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 hover:bg-gray-100"
            disabled={createSessionMutation.isPending}
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[50vh] overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
                <p className="text-sm text-gray-500">Loading PDFs...</p>
              </div>
            </div>
          ) : error ? (
            <div className="rounded-lg bg-red-50 p-4 text-center">
              <AlertCircle className="mx-auto h-8 w-8 text-red-600" />
              <p className="mt-2 text-sm font-medium text-red-900">
                Failed to load PDFs
              </p>
              <p className="mt-1 text-xs text-red-700">
                Make sure the backend is running and try again
              </p>
            </div>
          ) : !pdfs || pdfs.length === 0 ? (
            <div className="rounded-lg bg-yellow-50 p-6 text-center">
              <FileText className="mx-auto h-12 w-12 text-yellow-600" />
              <h3 className="mt-4 text-sm font-medium text-yellow-900">
                No PDFs available
              </h3>
              <p className="mt-2 text-xs text-yellow-700">
                Upload some PDFs first before creating a session
              </p>
            </div>
          ) : (
            <>
              {/* Select All Button */}
              <div className="mb-4 flex items-center justify-between">
                <p className="text-sm text-gray-600">
                  {selectedPdfIds.length} of {pdfs.length} PDFs selected
                </p>
                <button
                  onClick={handleSelectAll}
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  {allSelected ? "Deselect All" : "Select All"}
                </button>
              </div>

              {/* PDF List */}
              <div className="space-y-2">
                {pdfs.map(
                  (pdf: {
                    id: number;
                    original_filename: string;
                    page_count: number;
                  }) => {
                    const isSelected = selectedPdfIds.includes(pdf.id);
                    return (
                      <button
                        key={pdf.id}
                        onClick={() => handleToggle(pdf.id)}
                        title={pdf.original_filename}
                        className={`flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-all ${
                          isSelected
                            ? "border-primary-500 bg-primary-50"
                            : "border-gray-200 bg-white hover:border-primary-300"
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
                        </div>
                      </button>
                    );
                  }
                )}
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-200 p-6">
          <div className="text-sm text-gray-500">
            {selectedPdfIds.length === 0 ? (
              <span className="flex items-center gap-2 text-yellow-600">
                <AlertCircle className="h-4 w-4" />
                Please select at least one PDF
              </span>
            ) : (
              <span>
                Ready to create session with {selectedPdfIds.length} PDF
                {selectedPdfIds.length > 1 ? "s" : ""}
              </span>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={createSessionMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleCreateSession}
              disabled={
                selectedPdfIds.length === 0 || createSessionMutation.isPending
              }
              className="gap-2"
            >
              {createSessionMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                "Create Session"
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
