// API Response Types

export interface PDFDocument {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  page_count: number | null;
  total_pages?: number; // Alias for page_count
  upload_date: string;
  uploaded_at?: string; // Alias for upload_date
  processed_at?: string; // Alias for last_extraction_date
  status: string;
  session_id?: string;
  requirements_extracted: boolean;
  requirements_count: number;
  last_extraction_date?: string;
}

export interface ChatMessage {
  id: number;
  session_id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: SourceDocument[];
}

export interface SourceDocument {
  pdf_id: number;
  pdf_filename?: string;
  page_number: number;
  text_snippet: string;
  relevance_score: number;
}

export interface ChatSession {
  id: number;
  session_id: string;
  pdf_ids: number[];
  user_id?: string;
  created_at: string;
  last_activity: string;
  summary?: string;
  total_messages: number;
}

export interface Requirement {
  id: number;
  pdf_id: number;
  extraction_job_id: string;
  document_source: string;
  category?: string;
  requirement_detail: string;
  mandatory_optional?: string;
  compliance_status: string;
  page_number?: number;
  confidence_score?: number;
  created_at: string;
}

export interface BomItem {
  id: number;
  pdf_id: number;
  extraction_job_id: string;
  item_number?: string;
  description: string;
  unit?: string;
  quantity?: number;
  notes?: string;
  hierarchy_level: number;
  parent_item_id?: number;
  is_ambiguous: boolean;
  created_at: string;
}

export interface ChatResponse {
  session_id: string;
  message: string;
  sources: SourceDocument[];
  conversation_summary?: string;
  total_messages: number;
  memory_stats?: Record<string, any>;
}

// UI State Types

export interface UIState {
  sidebarOpen: boolean;
  currentSession: string | null;
  toggleSidebar: () => void;
  setCurrentSession: (sessionId: string | null) => void;
}
