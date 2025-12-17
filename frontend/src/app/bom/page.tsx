"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useState, useMemo } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { pdfAPI, bomAPI } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Loader2,
  Search,
  Package,
  Download,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import { BomItem } from "@/types";

type SortField = "item_number" | "description" | "unit" | "quantity" | "notes";
type SortDirection = "asc" | "desc" | null;

export default function BomPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPdfId, setSelectedPdfId] = useState<number | "all">("all");
  const [sortField, setSortField] = useState<SortField | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  // Fetch all PDFs for the filter
  const { data: pdfs } = useQuery({
    queryKey: ["pdfs"],
    queryFn: () => pdfAPI.getAll(),
    retry: 1,
  });

  // Fetch BoM items
  const {
    data: bomItems,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["bom", selectedPdfId],
    queryFn: async () => {
      if (selectedPdfId === "all") {
        // Fetch BoM for all PDFs
        if (!pdfs || pdfs.length === 0) return [];

        const allBomItems = await Promise.all(
          pdfs.map((pdf: { id: number }) => bomAPI.getByPdfId(pdf.id))
        );
        return allBomItems.flat();
      } else {
        return bomAPI.getByPdfId(selectedPdfId as number);
      }
    },
    enabled: selectedPdfId === "all" ? !!pdfs : true,
    retry: 1,
  });

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

  // Filter and sort BoM items
  const filteredBomItems = useMemo(() => {
    if (!bomItems) return [];

    let filtered = bomItems;

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = bomItems.filter(
        (item: BomItem) =>
          item.item_number?.toLowerCase().includes(query) ||
          item.description?.toLowerCase().includes(query) ||
          item.notes?.toLowerCase().includes(query) ||
          item.unit?.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    if (sortField && sortDirection) {
      filtered = [...filtered].sort((a, b) => {
        let aValue = a[sortField];
        let bValue = b[sortField];

        // Handle quantity as number
        if (sortField === "quantity") {
          aValue = aValue || 0;
          bValue = bValue || 0;
          const comparison = Number(aValue) - Number(bValue);
          return sortDirection === "asc" ? comparison : -comparison;
        }

        // Handle strings
        aValue = aValue?.toString().toLowerCase() || "";
        bValue = bValue?.toString().toLowerCase() || "";

        const comparison = aValue.localeCompare(bValue);
        return sortDirection === "asc" ? comparison : -comparison;
      });
    }

    return filtered;
  }, [bomItems, searchQuery, sortField, sortDirection]);

  // Export mutation
  const exportMutation = useMutation({
    mutationFn: async () => {
      const data = await bomAPI.export(
        selectedPdfId === "all" ? undefined : (selectedPdfId as number),
        true
      );
      await bomAPI.downloadExport(data.file_name);
      return data;
    },
    onSuccess: (data) => {
      alert(`Successfully exported ${data.total_items} BoM items!`);
    },
    onError: (error: any) => {
      alert(`Failed to export: ${error.message || "Unknown error"}`);
    },
  });

  const handleExport = () => {
    if (!filteredBomItems.length) {
      alert("No BoM items to export");
      return;
    }
    exportMutation.mutate();
  };

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Bill of Materials
            </h1>
            <p className="mt-1 text-sm text-gray-600">
              View extracted bill of materials from tender documents
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={exportMutation.isPending || !filteredBomItems.length}
            className="gap-2"
          >
            <Download className="h-4 w-4" />
            Export Excel
          </Button>
        </div>

        {/* Filters */}
        <Card className="p-4">
          <div className="grid gap-4 md:grid-cols-2">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search items..."
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
          </div>
        </Card>

        {/* BoM Table */}
        {isLoading ? (
          <Card className="flex items-center justify-center p-12">
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
              <p className="text-sm text-gray-500">Loading BoM items...</p>
            </div>
          </Card>
        ) : error ? (
          <Card className="p-12 text-center">
            <p className="text-gray-700">
              Unable to load BoM items. Make sure the backend is running.
            </p>
          </Card>
        ) : filteredBomItems.length === 0 ? (
          <Card className="p-12 text-center">
            <Package className="mx-auto mb-4 h-12 w-12 text-gray-400" />
            <h3 className="mb-2 text-lg font-semibold text-gray-900">
              No BoM items found
            </h3>
            <p className="text-sm text-gray-600">
              {searchQuery
                ? "Try adjusting your search"
                : "Extract BoM from uploaded PDFs to see them here"}
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
                        onClick={() => handleSort("item_number")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Item No.
                        {getSortIcon("item_number")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("description")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Description of Work
                        {getSortIcon("description")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("unit")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Unit
                        {getSortIcon("unit")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("quantity")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Quantity
                        {getSortIcon("quantity")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button
                        onClick={() => handleSort("notes")}
                        className="flex items-center gap-1 hover:text-gray-700 transition-colors"
                      >
                        Notes
                        {getSortIcon("notes")}
                      </button>
                    </th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Source
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {filteredBomItems.map((item: BomItem) => {
                    const pdf = pdfs?.find(
                      (p: { id: number; original_filename: string }) => p.id === item.pdf_id
                    );
                    const indent =
                      item.hierarchy_level > 0
                        ? "  ".repeat(item.hierarchy_level)
                        : "";

                    return (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="px-4 py-4 text-sm font-medium text-gray-900">
                          {indent}
                          {item.item_number || "-"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          <p className="line-clamp-3">
                            {item.description || "-"}
                          </p>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {item.unit || "-"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {item.quantity || "-"}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          <p className="line-clamp-2">{item.notes || "-"}</p>
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-600">
                          {pdf?.original_filename || `PDF ${item.pdf_id}`}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Card>
        )}

        {/* Stats */}
        {filteredBomItems.length > 0 && (
          <div className="flex items-center justify-between text-sm text-gray-600">
            <p>
              Showing {filteredBomItems.length} of {bomItems?.length || 0} items
            </p>
          </div>
        )}
      </div>
    </MainLayout>
  );
}
