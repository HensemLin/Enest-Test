import axios from "axios";
import type {
  PDFDocument,
  ChatMessage,
  ChatSession,
  Requirement,
  BomItem,
  ChatResponse,
} from "@/types";

const api = axios.create({
  baseURL: "/",
  headers: {
    "Content-Type": "application/json",
  },
});

// PDF APIs
export const pdfAPI = {
  upload: async (file: File, sessionId?: string) => {
    const formData = new FormData();
    formData.append("file", file);
    if (sessionId) formData.append("session_id", sessionId);

    const { data } = await api.post<PDFDocument>("/api/pdfs/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },

  getAll: async () => {
    const { data } = await api.get<any>("/api/pdfs/");
    // Backend returns { total, documents }, we just need documents
    return data.documents || data;
  },

  getById: async (id: number) => {
    const { data } = await api.get<PDFDocument>(`/api/pdfs/${id}`);
    return data;
  },

  delete: async (id: number) => {
    await api.delete(`/api/pdfs/${id}`);
  },
};

// Requirements APIs
export const requirementsAPI = {
  extract: async (pdfId: number) => {
    const { data } = await api.post("/api/requirements/extract", {
      pdf_id: pdfId,
      extraction_mode: "full", // or 'quick' - adjust as needed
    });
    return data;
  },

  getByPdfId: async (pdfId: number) => {
    const { data } = await api.get<Requirement[]>("/api/requirements/list", {
      params: { pdf_id: pdfId },
    });
    return data;
  },

  updateCompliance: async (id: number, status: string) => {
    const { data } = await api.patch(`/api/requirements/${id}`, {
      compliance_status: status,
    });
    return data;
  },

  batchUpdateCompliance: async (
    updates: Array<{ id: number; compliance_status: string }>
  ) => {
    const { data } = await api.patch("/api/requirements/batch", {
      updates,
    });
    return data;
  },

  export: async (format: "excel" | "json", pdfId?: number) => {
    const { data } = await api.post("/api/requirements/export", {
      format,
      pdf_id: pdfId,
    });
    return data;
  },

  downloadExport: async (fileName: string) => {
    const response = await api.get(`/api/requirements/download/${fileName}`, {
      responseType: "blob",
    });

    // Create a download link and trigger it
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

// BoM APIs
export const bomAPI = {
  extract: async (pdfId: number) => {
    const { data } = await api.post("/api/bom/extract", {
      pdf_id: pdfId,
    });
    return data;
  },

  getByPdfId: async (pdfId: number) => {
    const { data } = await api.get<BomItem[]>("/api/bom/list", {
      params: { pdf_id: pdfId },
    });
    return data;
  },

  export: async (pdfId?: number, includeHierarchy: boolean = true) => {
    const { data } = await api.post("/api/bom/export", {
      pdf_id: pdfId,
      include_hierarchy: includeHierarchy,
    });
    return data;
  },

  downloadExport: async (fileName: string) => {
    const response = await api.get(`/api/bom/download/${fileName}`, {
      responseType: "blob",
    });

    // Create a download link and trigger it
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", fileName);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },
};

// Chat APIs
export const chatAPI = {
  sendMessage: async (sessionId: string, message: string, pdfIds: number[]) => {
    const { data } = await api.post<ChatResponse>("/api/chat/message", {
      session_id: sessionId,
      message,
      pdf_ids: pdfIds,
    });
    return data;
  },

  getSession: async (sessionId: string) => {
    const { data } = await api.post("/api/chat/session/info", {
      session_id: sessionId,
    });
    return data;
  },

  getAllSessions: async () => {
    const { data } = await api.get<ChatSession[]>("/api/chat/sessions");
    return data;
  },

  getMessages: async (sessionId: string) => {
    const { data } = await api.get<ChatMessage[]>(
      `/api/chat/messages/${sessionId}`
    );
    return data;
  },
};

export default api;
