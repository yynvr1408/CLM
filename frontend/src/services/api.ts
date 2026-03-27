/**
 * API Service for CLM Platform
 */
import { AuthToken, Contract, Clause, Approval, Renewal, User } from "../types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

class ApiService {
  private token: string | null = localStorage.getItem("access_token");

  private getHeaders(): HeadersInit {
    return {
      "Content-Type": "application/json",
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
        ...this.getHeaders(),
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
      // On 401, clear stale token and redirect to login
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
  // Auth endpoints
  async register(
    email: string,
    username: string,
    password: string,
    full_name?: string,
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
    return response;
  }

  async logout(): Promise<void> {
    await this.request("/auth/logout", { method: "POST" });
    this.clearToken();
  }

  async getCurrentUser(): Promise<User> {
    return this.request("/auth/me");
  }

  async refreshToken(refreshToken: string): Promise<AuthToken> {
    return this.request("/auth/refresh", {
      method: "POST",
      headers: {
        ...this.getHeaders(),
        Authorization: `Bearer ${refreshToken}`,
      },
    });
  }

  // Contract endpoints
  async createContract(data: Partial<Contract>): Promise<Contract> {
    return this.request("/contracts", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getContracts(
    skip = 0,
    limit = 20,
    status?: string,
    search?: string,
  ): Promise<any> {
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
    return this.request(`/contracts/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  async submitContract(id: number): Promise<Contract> {
    return this.request(`/contracts/${id}/submit`, { method: "POST" });
  }

  async deleteContract(id: number): Promise<void> {
    return this.request(`/contracts/${id}`, { method: "DELETE" });
  }

  // Clause endpoints
  async createClause(data: Partial<Clause>): Promise<Clause> {
    return this.request("/clauses", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getClauses(
    skip = 0,
    limit = 20,
    category?: string,
    search?: string,
  ): Promise<any> {
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
    return this.request(`/clauses/${id}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  }

  // Approval endpoints
  async createApproval(contractId: number, data: any): Promise<Approval> {
    return this.request("/approvals", {
      method: "POST",
      body: JSON.stringify({ ...data, contract_id: contractId }),
    });
  }

  async getContractApprovals(
    contractId: number,
    skip = 0,
    limit = 20,
  ): Promise<any> {
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

  async approveContract(
    approvalId: number,
    comments?: string,
  ): Promise<Approval> {
    const params = comments ? `?comments=${encodeURIComponent(comments)}` : "";
    return this.request(`/approvals/${approvalId}/approve${params}`, {
      method: "POST",
    });
  }

  async rejectContract(
    approvalId: number,
    comments: string,
  ): Promise<Approval> {
    const params = `?comments=${encodeURIComponent(comments)}`;
    return this.request(`/approvals/${approvalId}/reject${params}`, {
      method: "POST",
    });
  }

  // Renewal endpoints
  async createRenewal(contractId: number, data: any): Promise<Renewal> {
    return this.request("/renewals", {
      method: "POST",
      body: JSON.stringify({ ...data, contract_id: contractId }),
    });
  }

  async getUpcomingRenewals(
    skip = 0,
    limit = 20,
    daysAhead = 30,
  ): Promise<any> {
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

  // Audit endpoints
  async getAuditLogs(skip = 0, limit = 50, contractId?: number): Promise<any> {
    const params = new URLSearchParams();
    params.append("skip", skip.toString());
    params.append("limit", limit.toString());
    if (contractId) params.append("contract_id", contractId.toString());
    return this.request(`/audit/logs?${params}`);
  }

  async getContractAuditTrail(contractId: number): Promise<any> {
    return this.request(`/audit/trail/${contractId}`);
  }

  setToken(token: string): void {
    this.token = token;
    localStorage.setItem("access_token", token);
  }

  clearToken(): void {
    this.token = null;
    localStorage.removeItem("access_token");
  }

  getToken(): string | null {
    return this.token;
  }
}

export default new ApiService();
