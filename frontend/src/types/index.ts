export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  status: 'active' | 'disabled';
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserListResponse {
  total: number;
  items: User[];
}

export interface Contract {
  id: number;
  title: string;
  contract_no: string;
  party_a: string;
  party_b: string;
  amount: number | null;
  status: 'draft' | 'active' | 'terminated' | 'expired';
  sign_date: string | null;
  expiry_date: string | null;
  content: string | null;
  created_by: number;
  creator_username: string | null;
  attachment_count: number;
  created_at: string;
  updated_at: string;
}

export interface ContractListResponse {
  total: number;
  items: Contract[];
}

export interface Attachment {
  id: number;
  contract_id: number;
  filename: string;
  original_name: string;
  file_type: string;
  file_size: number;
  uploaded_by: number;
  uploader_username: string | null;
  uploaded_at: string;
}

export interface AttachmentListResponse {
  total: number;
  items: Attachment[];
}

export interface AuditLog {
  id: number;
  user_id: number;
  username: string;
  action: string;
  target_type: string | null;
  target_id: number | null;
  detail: string | null;
  ip_address: string | null;
  created_at: string;
}

export interface AuditLogFilter {
  action?: string;
  user_search?: string;
  user_id?: number;
  start_date?: string;
  end_date?: string;
  page?: number;
  page_size?: number;
}

export interface AuditLogListResponse {
  total: number;
  items: AuditLog[];
}

export interface ContractTemplate {
  id: number;
  name: string;
  category: string;
  party_a_default: string | null;
  party_b_default: string | null;
  content: string | null;
  amount_min: number | null;
  amount_max: number | null;
  is_deleted: boolean;
  created_by: number;
  creator_username: string | null;
  created_at: string;
  updated_at: string;
}

export interface TemplateListResponse {
  total: number;
  items: ContractTemplate[];
}

export interface TemplateDropdownItem {
  id: number;
  name: string;
  category: string;
}

export interface ApiError {
  detail: string;
}
