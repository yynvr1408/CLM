/**
 * Type definitions for CLM Platform
 */

export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role_id: number;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

export interface Contract {
  id: number;
  contract_number: string;
  title: string;
  description?: string;
  owner_id: number;
  contract_type: string;
  status: 'draft' | 'submitted' | 'approved' | 'rejected' | 'executed';
  value?: number;
  currency: string;
  start_date?: string;
  end_date?: string;
  created_at: string;
  updated_at: string;
  executed_at?: string;
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
  created_at: string;
}

export interface AuthToken {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface ApiResponse<T> {
  total?: number;
  skip?: number;
  limit?: number;
  items?: T[];
  data?: T;
  message?: string;
  error?: string;
}
