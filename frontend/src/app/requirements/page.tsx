"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { pdfAPI, requirementsAPI } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Search,
  FileText,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Download,
  Save,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { Requirement } from "@/types";

type SortField =
  | "document_source"
  | "category"
  | "requirement_detail"
  | "mandatory_optional"
  | "compliance_status";
type SortDirection = "asc" | "desc" | null;

export default function RequirementsPage() {
  const queryClient = useQueryClient();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [mandatoryFilter, setMandatoryFilter] = useState<string>("all");
  const [selectedPdfId, setSelectedPdfId] = useState<number | "all">("all");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);
  const [pendingChanges, setPendingChanges] = useState<Record<number, string>>(
    {}
  );
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 100;

  // Fetch all PDFs for the filter
  const { data: pdfs } = useQuery({
    queryKey: ["pdfs"],
    queryFn: () => pdfAPI.getAll(),
    retry: 1,
  });

  // Fetch requirements - fetch all if no PDF selected
  const {
    data: requirements,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["requirements", selectedPdfId],
    queryFn: async () => {
      if (selectedPdfId === "all") {
        // Fetch requirements for all PDFs
        if (!pdfs || pdfs.length === 0) return [];

        const allRequirements = await Promise.all(
          pdfs.map((pdf: { id: number }) => requirementsAPI.getByPdfId(pdf.id))
        );
        return allRequirements.flat();
      } else {
        return requirementsAPI.getByPdfId(selectedPdfId as number);
      }
    },
    enabled: selectedPdfId === "all" ? !!pdfs : true,
    retry: 1,
  });

  // Batch update compliance mutation
  const batchUpdateMutation = useMutation({
    mutationFn: (updates: Array<{ id: number; compliance_status: string }>) =>
      requirementsAPI.batchUpdateCompliance(updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["requirements"] });
      setPendingChanges({});
      alert(`Successfully updated ${data.updated_count} requirements!`);
    },
    onError: (error: any) => {
      alert(`Failed to update: ${error.message || "Unknown error"}`);
    },
  });

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async ({ format }: { format: "excel" | "json" }) => {
      const data = await requirementsAPI.export(
        format,
        selectedPdfId === "all" ? undefined : (selectedPdfId as number)
      );
      await requirementsAPI.downloadExport(data.file_name);
      return data;
    },
    onSuccess: (data) => {
      alert(`Successfully exported ${data.total_requirements} requirements!`);
    },
    onError: (error: any) => {
      alert(`Failed to export: ${error.message || "Unknown error"}`);
    },
  });

  const handleStatusChange = (id: number, status: string) => {
    setPendingChanges((prev) => ({
      ...prev,
      [id]: status,
    }));
  };

  const handleSaveChanges = () => {
    const updates = Object.entries(pendingChanges).map(
      ([id, compliance_status]) => ({
        id: Number(id),
        compliance_status,
      })
    );

    if (updates.length === 0) {
      alert("No changes to save");
      return;
    }

    batchUpdateMutation.mutate(updates);
  };

  const handleCancelChanges = () => {
    setPendingChanges({});
  };

  const handleExport = (format: "excel" | "json") => {
    if (!filteredRequirements.length) {
      alert("No requirements to export");
      return;
    }
    exportMutation.mutate({ format });
  };

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      // Cycle through: asc -> desc -> null
      if (sortDirection === "asc") {
        setSortDirection("desc");
      } else if (sortDirection === "desc") {
        setSortDirection(null);
        setSortField(null);
      }
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 text-gray-400" />;
    }
    if (sortDirection === "asc") {
      return <ArrowUp className="h-4 w-4 text-primary-600" />;
    }
    return <ArrowDown className="h-4 w-4 text-primary-600" />;
  };

  // Filter and sort requirements
  const filteredRequirements = useMemo(() => {
    if (!requirements) return [];

    let filtered = requirements.filter((req: Requirement) => {
      // Status filter (case-insensitive comparison)
      if (
        statusFilter !== "all" &&
        req.compliance_status?.toLowerCase() !== statusFilter.toLowerCase()
      ) {
        return false;
      }

      // Mandatory/Optional filter (case-insensitive comparison)
      if (
        mandatoryFilter !== "all" &&
        req.mandatory_optional?.toLowerCase() !== mandatoryFilter.toLowerCase()
      ) {
        return false;
      }

      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        return (
          req.requirement_detail.toLowerCase().includes(query) ||
          req.category?.toLowerCase().includes(query) ||
          req.document_source?.toLowerCase().includes(query)
        );
      }

      return true;
    });

    // Apply sorting
    if (sortField && sortDirection) {
      filtered = [...filtered].sort((a, b) => {
        const aValue = a[sortField] || "";
        const bValue = b[sortField] || "";

        const comparison = aValue
          .toString()
          .toLowerCase()
          .localeCompare(bValue.toString().toLowerCase());
        return sortDirection === "asc" ? comparison : -comparison;
      });
    }

    return filtered;
  }, [
    requirements,
    statusFilter,
    mandatoryFilter,
    searchQuery,
    sortField,
    sortDirection,
  ]);

  // Pagination
  const totalPages = Math.ceil(filteredRequirements.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedRequirements = filteredRequirements.slice(
    startIndex,
    endIndex
  );

  // Reset to page 1 when filters change
  useMemo(() => {
    setCurrentPage(1);
  }, [
    searchQuery,
    statusFilter,
    mandatoryFilter,
    selectedPdfId,
    sortField,
    sortDirection,
  ]);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case "yes":
        return "bg-green-100 text-green-700";
      case "no":
        return "bg-red-100 text-red-700";
      case "partial":
        return "bg-yellow-100 text-yellow-700";
      case "unknown":
      default:
        return "bg-gray-100 text-gray-700";
    }
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Requirements</h1>
            <p className="mt-1 text-sm text-gray-600">
              View and manage extracted requirements from tender documents
            </p>
          </div>
          <div className="flex gap-2">
            {Object.keys(pendingChanges).length > 0 && (
              <>
                <Button
                  variant="default"
                  size="sm"
                  onClick={handleSaveChanges}
                  disabled={batchUpdateMutation.isPending}
                  className="gap-2"
                >
                  <Save className="h-4 w-4" />
                  Save Changes ({Object.keys(pendingChanges).length})
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleCancelChanges}
                  disabled={batchUpdateMutation.isPending}
                >
                  Cancel
                </Button>
              </>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("excel")}
              disabled={
                exportMutation.isPending || !filteredRequirements.length
              }
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export Excel
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleExport("json")}
              disabled={
                exportMutation.isPending || !filteredRequirements.length
              }
              className="gap-2"
            >
              <Download className="h-4 w-4" />
              Export JSON
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card className="p-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search requirements..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full rounded-lg border border-gray-300 py-2 pl-10 pr-4 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
              />
            </div>

            {/* PDF Filter */}
            <select
              value={selectedPdfId}
              onChange={(e) =>
                setSelectedPdfId(
                  e.target.value === "all" ? "all" : Number(e.target.value)
                )
              }
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            >
              <option value="all">All PDFs</option>
              {pdfs?.map((pdf: { id: number; original_filename: string }) => (
                <option key={pdf.id} value={pdf.id}>
                  {pdf.original_filename}
                </option>
              ))}
            </select>

            {/* Mandatory/Optional Filter */}
            <select
              value={mandatoryFilter}
              onChange={(e) => setMandatoryFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            >
              <option value="all">All Types</option>
              <option value="Mandatory">Mandatory</option>
              <option value="Optional">Optional</option>
              <option value="Unclear">Unclear</option>
            </select>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20"
            >
              <option value="all">All Statuses</option>
              <option value="Unknown">Unknown</option>
              <option value="Yes">Yes (Compliant)</option>
              <option value="Partial">Partial</option>
              <option value="No">No (Non-Compliant)</option>
            </select>
          </div>
        </Card>

        {/* Requirements Table */}
        {isLoading ? (
          <Card className="flex items-center justify-center p-12">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
              <p className="text-sm text-gray-500">Loading requirements...</p>
            </div>
          </Card>
        ) : error ? (
          <Card className="p-12 text-center">
            <p className="text-gray-700">
              Unable to load requirements. Make sure the backend is running.
            </p>
          </Card>
        ) : filteredRequirements.length === 0 ? (
          <Card className="p-12 text-center">
            <FileText className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              No requirements found
            </h3>
            <p className="text-sm text-gray-600">
              {searchQuery ||
              statusFilter !== "all" ||
              mandatoryFilter !== "all"
                ? "Try adjusting your filters"
                : "Extract requirements from uploaded PDFs to see them here"}
            </p>
          </Card>
        ) : (
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("document_source")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Document Source
                        {getSortIcon("document_source")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("category")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Requirement Category
                        {getSortIcon("category")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("requirement_detail")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Requirement Detail
                        {getSortIcon("requirement_detail")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("mandatory_optional")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Mandatory/Optional
                        {getSortIcon("mandatory_optional")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("compliance_status")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Compliance Status
                        {getSortIcon("compliance_status")}
                      </button>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {paginatedRequirements.map((req: Requirement) => {
                    const currentStatus =
                      pendingChanges[req.id] || req.compliance_status;
                    const hasChanges = pendingChanges[req.id] !== undefined;

                    return (
                      <tr
                        key={req.id}
                        className={`hover:bg-gray-50 ${
                          hasChanges ? "bg-yellow-50" : ""
                        }`}
                      >
                        <td className="px-4 py-4 text-sm text-gray-600">
                          <div>
                            <p className="font-medium text-gray-900 line-clamp-1">
                              {req.document_source || "-"}
                            </p>
                            {req.page_number && (
                              <p className="text-xs text-gray-500 mt-1">
                                Page {req.page_number}
                              </p>
                            )}
                          </div>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {req.category || "-"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-900">
                          <p className="line-clamp-3">
                            {req.requirement_detail}
                          </p>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          <span
                            className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                              req.mandatory_optional?.toLowerCase() ===
                              "mandatory"
                                ? "bg-red-100 text-red-800"
                                : "bg-blue-100 text-blue-800"
                            }`}
                          >
                            {req.mandatory_optional || "Unknown"}
                          </span>
                        </td>
                        <td className="px-4 py-4">
                          <select
                            value={currentStatus}
                            onChange={(e) =>
                              handleStatusChange(req.id, e.target.value)
                            }
                            className={`rounded-full px-3 py-1 text-xs font-medium ${getStatusColor(
                              currentStatus
                            )} ${
                              hasChanges ? "ring-2 ring-yellow-400" : ""
                            } border-0 focus:outline-none focus:ring-2 focus:ring-primary-500/20`}
                          >
                            <option value="Unknown">Unknown</option>
                            <option value="Yes">Yes</option>
                            <option value="Partial">Partial</option>
                            <option value="No">No</option>
                          </select>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Pagination & Stats */}
        {filteredRequirements.length > 0 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-600">
              Showing {startIndex + 1}-
              {Math.min(endIndex, filteredRequirements.length)} of{" "}
              {filteredRequirements.length} requirements
              {filteredRequirements.length < (requirements?.length || 0) &&
                ` (filtered from ${requirements?.length || 0} total)`}
            </p>

            {totalPages > 1 && (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="gap-1"
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>

                <div className="flex items-center gap-1">
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }

                    return (
                      <Button
                        key={pageNum}
                        variant={
                          currentPage === pageNum ? "default" : "outline"
                        }
                        size="sm"
                        onClick={() => handlePageChange(pageNum)}
                        className="w-10"
                      >
                        {pageNum}
                      </Button>
                    );
                  })}
                </div>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages}
                  className="gap-1"
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </MainLayout>
  );
}
