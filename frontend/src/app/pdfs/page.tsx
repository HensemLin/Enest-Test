"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useEffect, useRef } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { PDFUpload } from "@/components/pdf/PDFUpload";
import { PDFList } from "@/components/pdf/PDFList";
import { pdfAPI, requirementsAPI, bomAPI } from "@/lib/api";
import { Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";

export default function PDFsPage() {
  const queryClient = useQueryClient();
  const [deletingId, setDeletingId] = useState<number | undefined>();
  const [extractingReqId, setExtractingReqId] = useState<number | undefined>();
  const [extractingBomId, setExtractingBomId] = useState<number | undefined>();
  const [processingPdfIds, setProcessingPdfIds] = useState<Set<number>>(
    new Set()
  );
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch all PDFs
  const {
    data: pdfs,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["pdfs"],
    queryFn: () => pdfAPI.getAll(),
    retry: 1,
  });

  // Initialize processing PDFs on load
  useEffect(() => {
    if (!pdfs) return;

    const processing = pdfs
      .filter((pdf: { id: number; status: string }) => pdf.status === "processing")
      .map((pdf: { id: number; status: string }) => pdf.id);

    if (processing.length > 0) {
      setProcessingPdfIds(new Set(processing));
    }
  }, [pdfs?.length]); // Only run when PDFs are first loaded or list length changes

  // Poll for processing status changes
  useEffect(() => {
    if (processingPdfIds.size === 0 || !pdfs) return;

    const checkStatus = () => {
      const stillProcessing = new Set<number>();
      let statusChanged = false;

      processingPdfIds.forEach((pdfId) => {
        const pdf = pdfs.find((p: { id: number; status: string }) => p.id === pdfId);
        if (!pdf) {
          stillProcessing.add(pdfId);
          return;
        }

        if (pdf.status === "processing") {
          stillProcessing.add(pdfId);
        } else if (pdf.status === "ready") {
          statusChanged = true;
          alert(
            `Extraction completed for ${pdf.original_filename}! The data is now ready to view.`
          );
        } else if (pdf.status === "failed") {
          statusChanged = true;
          alert(
            `Extraction failed for ${pdf.original_filename}. Please try again.`
          );
        }
      });

      if (statusChanged) {
        // Refresh requirements and BoM data
        queryClient.invalidateQueries({ queryKey: ["requirements"] });
        queryClient.invalidateQueries({ queryKey: ["bom"] });
      }

      setProcessingPdfIds(stillProcessing);

      // Stop polling if no PDFs are processing
      if (stillProcessing.size === 0 && pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };

    // Start polling if not already running
    if (!pollingIntervalRef.current) {
      pollingIntervalRef.current = setInterval(checkStatus, 3000); // Poll every 3 seconds
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [processingPdfIds, pdfs, queryClient]);

  // Upload PDF mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) => pdfAPI.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pdfs"] });
    },
  });

  // Delete PDF mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => {
      setDeletingId(id);
      return pdfAPI.delete(id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pdfs"] });
      setDeletingId(undefined);
    },
    onError: () => {
      setDeletingId(undefined);
    },
  });

  // Extract requirements mutation
  const extractReqMutation = useMutation({
    mutationFn: (pdfId: number) => {
      setExtractingReqId(pdfId);
      return requirementsAPI.extract(pdfId);
    },
    onSuccess: (data) => {
      setExtractingReqId(undefined);
      if (data.status === "processing") {
        alert(
          `Requirements extraction started in background! This may take 1-2 minutes. You can continue using the app and you'll be notified when complete.`
        );
        // Add to processing set to start polling
        setProcessingPdfIds((prev) => new Set(prev).add(data.pdf_id));
      } else {
        alert(
          `Successfully extracted ${data.total_requirements} requirements! Navigate to the Requirements page to view them.`
        );
      }
      // Refresh PDF list to show updated status
      queryClient.invalidateQueries({ queryKey: ["pdfs"] });
    },
    onError: (error: any) => {
      setExtractingReqId(undefined);
      alert(
        `Failed to extract requirements: ${error.message || "Unknown error"}`
      );
    },
  });

  // Extract BoM mutation
  const extractBomMutation = useMutation({
    mutationFn: (pdfId: number) => {
      setExtractingBomId(pdfId);
      return bomAPI.extract(pdfId);
    },
    onSuccess: (data) => {
      setExtractingBomId(undefined);
      if (data.status === "processing") {
        alert(
          `BoM extraction started in background! This may take 1-2 minutes. You can continue using the app and you'll be notified when complete.`
        );
        // Add to processing set to start polling
        setProcessingPdfIds((prev) => new Set(prev).add(data.pdf_id));
      } else {
        alert(
          `Successfully extracted ${data.total_items} BoM items! Navigate to the BoM page to view them.`
        );
      }
      // Refresh PDF list to show updated status
      queryClient.invalidateQueries({ queryKey: ["pdfs"] });
    },
    onError: (error: any) => {
      setExtractingBomId(undefined);
      alert(`Failed to extract BoM: ${error.message || "Unknown error"}`);
    },
  });

  const handleUpload = (file: File) => {
    uploadMutation.mutate(file);
  };

  const handleDelete = (id: number) => {
    if (confirm("Are you sure you want to delete this PDF?")) {
      deleteMutation.mutate(id);
    }
  };

  const handleExtractRequirements = (id: number) => {
    extractReqMutation.mutate(id);
  };

  const handleExtractBom = (id: number) => {
    extractBomMutation.mutate(id);
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">PDF Documents</h1>
          <p className="mt-1 text-sm text-gray-600">
            Upload and manage your tender documents
          </p>
        </div>

        {/* Upload Section */}
        <PDFUpload
          onUpload={handleUpload}
          isUploading={uploadMutation.isPending}
        />

        {/* PDFs List */}
        <div>
          <h2 className="mb-4 text-lg font-semibold text-gray-900">
            Uploaded Documents
          </h2>

          {isLoading ? (
            <Card className="flex items-center justify-center p-12">
              <div className="flex flex-col items-center gap-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
                <p className="text-sm text-gray-500">Loading PDFs...</p>
              </div>
            </Card>
          ) : error ? (
            <Card className="p-12 text-center">
              <p className="text-gray-700">
                Unable to load PDFs. Make sure the backend is running.
              </p>
            </Card>
          ) : (
            <PDFList
              pdfs={pdfs || []}
              onDelete={handleDelete}
              onExtractRequirements={handleExtractRequirements}
              onExtractBom={handleExtractBom}
              isDeleting={deletingId}
              isExtractingReq={extractingReqId}
              isExtractingBom={extractingBomId}
            />
          )}
        </div>
      </div>
    </MainLayout>
  );
}
