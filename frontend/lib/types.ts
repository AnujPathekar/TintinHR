export type Session = { id: string; role: string; exp: number };

export type Citation = {
  index: number;
  chunk_id: string;
  document_id: string;
  title: string;
  filename: string;
  page_number: number | null;
  quote: string;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
};

export type HRDocument = {
  id: string;
  title: string;
  filename: string;
  visibility: string;
  status: string;
  current_version: number;
  failure_reason?: string;
  created_at: string;
};

