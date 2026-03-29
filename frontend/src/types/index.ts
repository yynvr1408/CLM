/**
 * Type definitions for CLM Platform v2.0
 */

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role_id: number;
  role_name?: string;
  organization_id?: number;
  is_active: boolean;
  is_superuser: boolean;
  is_approved: boolean;
  permissions: string[];
  created_at: string;
  updated_at: string;
}

export interface Organization {
  id: number;
  name: string;
  slug: string;
  domain?: string;
  logo_url?: string;
  settings: Record<string, any>;
  subscription_tier: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Role {
  id: number;
  name: string;
  description?: string;
  permissions: string[];
  is_system_role: boolean;
  created_at: string;
  updated_at: string;
}

export interface Contract {
  id: number;
  contract_number: string;
  title: string;
  description?: string;
  owner_id: number;
  organization_id?: number;
  template_id?: number;
  contract_type: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'executed';
  value?: number;
  currency: string;
  start_date?: string;
  end_date?: string;
  metadata_fields?: Record<string, any>;
  is_deleted?: boolean;
  created_at: string;
  updated_at: string;
  executed_at?: string;
  clauses?: Clause[];
  tags?: Tag[];
  attachments?: Attachment[];
}

export interface Clause {
  id: number;
  title: string;
  content: string;
  category: string;
  version: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  attachments?: Attachment[];
}


export interface Tag {
  id: number;
  name: string;
  color: string;
  organization_id?: number;
  created_at: string;
}

export interface ContractTemplate {
  id: number;
  name: string;
  description?: string;
  contract_type: string;
  default_fields: Record<string, any>;
  approval_workflow: Record<string, any>[];
  version: number;
  is_active: boolean;
  organization_id?: number;
  created_by_id: number;
  clauses: Clause[];
  attachments?: Attachment[];
  created_at: string;
  updated_at: string;
}

export interface Comment {
  id: number;
  contract_id: number;
  user_id: number;
  parent_id?: number;
  content: string;
  is_resolved: boolean;
  user_name?: string;
  replies: Comment[];
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: number;
  user_id: number;
  type: 'approval_request' | 'status_change' | 'comment' | 'renewal' | 'system';
  title: string;
  message: string;
  link?: string;
  is_read: boolean;
  created_at: string;
}

export interface Approval {
  id: number;
  contract_id: number;
  approver_id: number;
  approval_level: number;
  status: 'pending' | 'approved' | 'rejected';
  comments?: string;
  approved_at?: string;
  created_at: string;
}

export interface Renewal {
  id: number;
  contract_id: number;
  renewal_date: string;
  alert_date: string;
  status: 'pending' | 'notified' | 'renewed' | 'expired';
  notification_sent: boolean;
  created_at: string;
}

export interface AuditLog {
  id: number;
  user_id: number;
  contract_id?: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  changes?: Record<string, any>;
  ip_address?: string;
  entry_hash?: string;
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface DashboardStats {
  total_contracts: number;
  draft_contracts: number;
  submitted_contracts: number;
  approved_contracts: number;
  rejected_contracts: number;
  executed_contracts: number;
  total_value: number;
  pending_approvals: number;
  upcoming_renewals: number;
  overdue_renewals: number;
  total_users: number;
  contracts_expiring_30d: number;
  contracts_expiring_60d: number;
  contracts_expiring_90d: number;
}

export interface Attachment {
  id: number;
  filename: string;
  file_path: string;
  file_type?: string;
  file_size?: number;
  uploaded_by_id: number;
  created_at: string;
}

export interface ApiResponse<T> {

  total?: number;
  skip?: number;
  limit?: number;
  items?: T[];
  data?: T;
  message?: string;
  error?: string;
  unread_count?: number;
}

export interface ClauseVersion {
  id: number;
  clause_id: number;
  version_number: number;
  title: string;
  content: string;
  category: string;
  created_by_id: number;
  created_at: string;
}

export interface ClauseVersionResponse extends ClauseVersion {}

export interface AuditLogResponse {
  id: number;
  user_id: number;
  action: string;
  resource_type: string;
  resource_id?: number;
  contract_id?: number;
  clause_id?: number;
  changes?: Record<string, { old: any; new: any }>;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
  user_full_name?: string;
}

export interface IntegrityStatus {
  is_valid: boolean;
  broken_id?: number;
  total_logs: number;
}


export interface ContractResponse extends Contract {}
export interface ContractDetailResponse extends Contract {
  clauses: Clause[];
  tags: Tag[];
}

export interface ClauseCreate extends Omit<Clause, 'id' | 'version' | 'is_active' | 'created_at' | 'updated_at' | 'attachments'> {}
export interface ClauseUpdate extends Partial<ClauseCreate> {}
export interface ClauseResponse extends Clause {}

export interface ApprovalResponse extends Approval {
  contract_title?: string;
  contract_number?: string;
}
export interface ApprovalCreate {
  approver_id: number;
  approval_level: number;
  comments?: string;
}

export interface RenewalResponse extends Renewal {}

export interface AttachmentResponse extends Attachment {}

export interface BulkStatusUpdate {
  contract_ids: number[];
  new_status: string;
}

export interface BulkDeleteRequest {
  contract_ids: number[];
}
