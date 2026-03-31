/**
 * API Service for CLM Platform v2.0
 */
import {
  AuthToken,
  User,
  ClauseResponse,
  ClauseVersionResponse,
  AuditLogResponse,
  IntegrityStatus,
  Role,
  Contract,
  DashboardStats,
  Clause,
  ContractTemplate,
  Tag,
  Approval,
  Renewal,
  ApiResponse,
  AuditLog
} from "../types";

const API_URL = import.meta.env.VITE_API_URL || "/api/v1";

class ApiService {
  private token: string | null = localStorage.getItem("access_token");

  private getHeaders(isFormData = false): HeadersInit {
    return {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
    };
  }


  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
  ): Promise<T> {
    const url = `${API_URL}${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        ...this.getHeaders(options.body instanceof FormData),
        ...(options.headers || {}),
      },
    });


    let data: any = null;

    try {
      data = await response.json();
    } catch {
      data = null;
    }

    if (!response.ok) {
      if (response.status === 401) {
        this.token = null;
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
          window.location.href = "/login";
        }
      }
      throw new Error(data?.detail || `API Error: ${response.status}`);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return data as T;
  }

  // ═══════════════════════════════════════════════════════
  // Auth endpoints
  // ═══════════════════════════════════════════════════════
  async register(
    email: string, username: string, password: string, full_name?: string,
  ): Promise<User> {
    return this.request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, password, full_name }),
    });
  }

  async login(email: string, password: string): Promise<AuthToken> {
    const response = await this.request<AuthToken>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(response.access_token);
    localStorage.setItem("refresh_token", response.refresh_token);
    return response;
  }

  async logout(): Promise<void> {
    try {
      await this.request("/auth/logout", { method: "POST" });
    } finally {
      this.clearToken();
    }
  }

  async getCurrentUser(): Promise<User> {
    return this.request("/auth/me");
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    return this.request("/auth/refresh", {
      method: "POST",
      headers: { ...this.getHeaders(), Authorization: `Bearer ${refreshToken}` },
    });
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<any> {
    return this.request("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  }

  // ═══════════════════════════════════════════════════════
  // User Management (Admin)
  // ═══════════════════════════════════════════════════════
  async getUsers(skip = 0, limit = 50, filters?: Record<string, any>): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    if (filters?.is_approved !== undefined) params.append("is_approved", filters.is_approved.toString());
    if (filters?.is_active !== undefined) params.append("is_active", filters.is_active.toString());
    if (filters?.role_id) params.append("role_id", filters.role_id.toString());
    return this.request(`/auth/users?${params}`);
  }

  async approveUser(userId: number): Promise<User> {
    return this.request(`/auth/users/${userId}/approve`, { method: "POST" });
  }

  async deactivateUser(userId: number): Promise<User> {
    return this.request(`/auth/users/${userId}/deactivate`, { method: "POST" });
  }

  async activateUser(userId: number): Promise<User> {
    return this.request(`/auth/users/${userId}/activate`, { method: "POST" });
  }

  async unlockUser(userId: number): Promise<User> {
    return this.request(`/auth/users/${userId}/unlock`, { method: "POST" });
  }

  async updateUserRole(userId: number, roleId: number): Promise<User> {
    return this.request(`/auth/users/${userId}/role?role_id=${roleId}`, { method: "PATCH" });
  }

  async deleteUser(userId: number): Promise<void> {
    return this.request(`/auth/users/${userId}`, { method: "DELETE" });
  }

  // ═══════════════════════════════════════════════════════
  // Role Management
  // ═══════════════════════════════════════════════════════
  async getRoles(): Promise<any> {
    return this.request("/auth/roles");
  }

  async createRole(data: Partial<Role>): Promise<Role> {
    return this.request("/auth/roles", { method: "POST", body: JSON.stringify(data) });
  }

  async updateRole(roleId: number, data: Partial<Role>): Promise<Role> {
    return this.request(`/auth/roles/${roleId}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  async deleteRole(roleId: number): Promise<void> {
    return this.request(`/auth/roles/${roleId}`, { method: "DELETE" });
  }

  async getAllPermissions(): Promise<any> {
    return this.request("/auth/permissions");
  }

  // ═══════════════════════════════════════════════════════
  // Contract endpoints
  // ═══════════════════════════════════════════════════════
  async createContract(data: Partial<Contract>): Promise<Contract> {
    return this.request("/contracts", { method: "POST", body: JSON.stringify(data) });
  }

  async getContracts(skip = 0, limit = 20, status?: string, search?: string): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    if (status) params.append("status", status);
    if (search) params.append("search", search);
    return this.request(`/contracts?${params}`);
  }

  async getContract(id: number): Promise<Contract> {
    return this.request(`/contracts/${id}`);
  }

  async updateContract(id: number, data: Partial<Contract>): Promise<Contract> {
    return this.request(`/contracts/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  async submitContract(id: number): Promise<Contract> {
    return this.request(`/contracts/${id}/submit`, { method: "POST" });
  }

  async deleteContract(id: number): Promise<void> {
    return this.request(`/contracts/${id}`, { method: "DELETE" });
  }

  async restoreContract(id: number): Promise<Contract> {
    return this.request(`/contracts/${id}/restore`, { method: "POST" });
  }

  async getContractStats(): Promise<DashboardStats> {
    return this.request("/contracts/stats");
  }

  async getExpiringContracts(daysAhead = 30, skip = 0, limit = 20): Promise<any> {
    const params = new URLSearchParams();
    params.append("days_ahead", daysAhead.toString());
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    return this.request(`/contracts/expiring?${params}`);
  }

  async bulkUpdateStatus(contractIds: number[], newStatus: string): Promise<any> {
    return this.request("/contracts/bulk/status", {
      method: "POST",
      body: JSON.stringify({ contract_ids: contractIds, new_status: newStatus }),
    });
  }

  async bulkDeleteContracts(contractIds: number[]): Promise<any> {
    return this.request("/contracts/bulk/delete", {
      method: "POST",
      body: JSON.stringify({ contract_ids: contractIds }),
    });
  }

  // ═══════════════════════════════════════════════════════
  // Clause endpoints
  // ═══════════════════════════════════════════════════════
  async createClause(data: Partial<Clause>): Promise<Clause> {
    return this.request("/clauses", { method: "POST", body: JSON.stringify(data) });
  }

  async getClauses(skip = 0, limit = 20, category?: string, search?: string): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    if (category) params.append("category", category);
    if (search) params.append("search", search);
    return this.request(`/clauses?${params}`);
  }

  async getClause(id: number): Promise<Clause> {
    return this.request(`/clauses/${id}`);
  }

  async updateClause(id: number, data: Partial<Clause>): Promise<Clause> {
    return this.request(`/clauses/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  async deleteClause(id: number): Promise<void> {
    return this.request(`/clauses/${id}`, { method: "DELETE" });
  }

  // ═══════════════════════════════════════════════════════
  // Template endpoints
  // ═══════════════════════════════════════════════════════
  async createTemplate(data: any): Promise<ContractTemplate> {
    return this.request("/templates", { method: "POST", body: JSON.stringify(data) });
  }

  async getTemplates(skip = 0, limit = 20, contractType?: string): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    if (contractType) params.append("contract_type", contractType);
    return this.request(`/templates?${params}`);
  }

  async getTemplate(id: number): Promise<ContractTemplate> {
    return this.request(`/templates/${id}`);
  }

  async updateTemplate(id: number, data: any): Promise<ContractTemplate> {
    return this.request(`/templates/${id}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  async deleteTemplate(id: number): Promise<void> {
    return this.request(`/templates/${id}`, { method: "DELETE" });
  }

  // ═══════════════════════════════════════════════════════
  // Comment endpoints
  // ═══════════════════════════════════════════════════════
  async createComment(contractId: number, content: string, parentId?: number): Promise<Comment> {
    return this.request(`/comments/contract/${contractId}`, {
      method: "POST",
      body: JSON.stringify({ content, parent_id: parentId }),
    });
  }

  async getComments(contractId: number, skip = 0, limit = 50): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    return this.request(`/comments/contract/${contractId}?${params}`);
  }

  async updateComment(commentId: number, data: any): Promise<Comment> {
    return this.request(`/comments/${commentId}`, { method: "PATCH", body: JSON.stringify(data) });
  }

  async deleteComment(commentId: number): Promise<void> {
    return this.request(`/comments/${commentId}`, { method: "DELETE" });
  }

  // ═══════════════════════════════════════════════════════
  // Tag endpoints
  // ═══════════════════════════════════════════════════════
  async createTag(data: { name: string; color?: string }): Promise<Tag> {
    return this.request("/tags", { method: "POST", body: JSON.stringify(data) });
  }

  async getTags(): Promise<any> {
    return this.request("/tags");
  }

  async deleteTag(tagId: number): Promise<void> {
    return this.request(`/tags/${tagId}`, { method: "DELETE" });
  }

  async addTagToContract(contractId: number, tagId: number): Promise<any> {
    return this.request(`/tags/contract/${contractId}/tag/${tagId}`, { method: "POST" });
  }

  async removeTagFromContract(contractId: number, tagId: number): Promise<void> {
    return this.request(`/tags/contract/${contractId}/tag/${tagId}`, { method: "DELETE" });
  }

  // ═══════════════════════════════════════════════════════
  // Notification endpoints
  // ═══════════════════════════════════════════════════════
  async getNotifications(unreadOnly = false, skip = 0, limit = 20): Promise<any> {
    const params = new URLSearchParams();
    params.append("unread_only", unreadOnly.toString());
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    return this.request(`/notifications?${params}`);
  }

  async getUnreadCount(): Promise<{ unread_count: number }> {
    return this.request("/notifications/unread-count");
  }

  async markNotificationsRead(notificationIds?: number[], markAll = false): Promise<any> {
    return this.request("/notifications/mark-read", {
      method: "POST",
      body: JSON.stringify({ notification_ids: notificationIds || [], mark_all: markAll }),
    });
  }

  async deleteNotification(id: number): Promise<void> {
    return this.request(`/notifications/${id}`, { method: "DELETE" });
  }

  // ═══════════════════════════════════════════════════════
  // Approval endpoints
  // ═══════════════════════════════════════════════════════
  async createApproval(contractId: number, data: any): Promise<Approval> {
    return this.request("/approvals", {
      method: "POST",
      body: JSON.stringify({ ...data, contract_id: contractId }),
    });
  }

  async getContractApprovals(contractId: number, skip = 0, limit = 20): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    return this.request(`/approvals/contract/${contractId}?${params}`);
  }

  async getPendingApprovals(skip = 0, limit = 20): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    return this.request(`/approvals/pending?${params}`);
  }

  async approveContract(approvalId: number, comments?: string): Promise<Approval> {
    const params = comments ? `?comments=${encodeURIComponent(comments)}` : "";
    return this.request(`/approvals/${approvalId}/approve${params}`, { method: "POST" });
  }

  async rejectContract(approvalId: number, comments: string): Promise<Approval> {
    return this.request(`/approvals/${approvalId}/reject?comments=${encodeURIComponent(comments)}`, {
      method: "POST",
    });
  }

  // ═══════════════════════════════════════════════════════
  // Renewal endpoints
  // ═══════════════════════════════════════════════════════
  async createRenewal(contractId: number, data: any): Promise<Renewal> {
    return this.request("/renewals", {
      method: "POST",
      body: JSON.stringify({ ...data, contract_id: contractId }),
    });
  }

  async getUpcomingRenewals(skip = 0, limit = 20, daysAhead = 30): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    params.append("days_ahead", daysAhead.toString());
    return this.request(`/renewals/upcoming?${params}`);
  }

  async getOverdueRenewals(skip = 0, limit = 20): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    return this.request(`/renewals/overdue?${params}`);
  }

  // ═══════════════════════════════════════════════════════
  // History & Audit
  // ═══════════════════════════════════════════════════════
  async getContractHistory(contractId: number): Promise<AuditLogResponse[]> {
    return this.request(`/history/contract/${contractId}`);
  }

  async getClauseVersions(clauseId: number): Promise<ClauseVersionResponse[]> {
    return this.request(`/history/clause/${clauseId}/versions`);
  }

  async restoreClauseVersion(clauseId: number, versionId: number): Promise<ClauseResponse> {
    return this.request(`/history/clause/${clauseId}/restore/${versionId}`, {
      method: "POST"
    });
  }

  async checkAuditIntegrity(): Promise<IntegrityStatus> {
    return this.request("/history/integrity");
  }

  async getAuditLogs(params: URLSearchParams): Promise<ApiResponse<AuditLog>> {
  return this.request(`/audit/logs?${params}`);
}

  // ═══════════════════════════════════════════════════════
  // Token management
  // ═══════════════════════════════════════════════════════
  setToken(token: string): void {
    this.token = token;
    localStorage.setItem("access_token", token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
  }

  getToken(): string | null {
    return this.token;
  }

  // ═══════════════════════════════════════════════════════
  // Attachment endpoints
  // ═══════════════════════════════════════════════════════
  async getAttachments(skip: number = 0, limit: number = 20): Promise<any> {
    return this.request(`/attachments?skip=${skip}&limit=${limit}`);
  }

  async uploadAttachment(
    file: File, 
    parentId?: { contract_id?: number; clause_id?: number; template_id?: number }
  ): Promise<any> {
    const formData = new FormData();
    formData.append("file", file);
    if (parentId?.contract_id) formData.append("contract_id", parentId.contract_id.toString());
    if (parentId?.clause_id) formData.append("clause_id", parentId.clause_id.toString());
    if (parentId?.template_id) formData.append("template_id", parentId.template_id.toString());

    return this.request("/attachments/upload", {
      method: "POST",
      body: formData,
      headers: {
        // Headers here shouldn't include Content-Type as fetch handles it for FormData
      },
    });
  }

  async getContractVersions(id: number): Promise<any[]> {
    return this.request(`/history/contract/${id}/versions`);
  }

  getAuditExportUrl(): string {
    const token = localStorage.getItem("access_token");
    return `${API_URL}/history/export?token=${token}`;
  }

  async deleteAttachment(id: number): Promise<void> {
    return this.request(`/attachments/${id}`, { method: "DELETE" });
  }
}


export default new ApiService();
