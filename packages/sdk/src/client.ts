import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  ChimeraClientConfig,
  QueryRequest,
  QuerySubmissionResponse,
  QueryStatusResponse,
  QueryListResponse,
  Report,
  ReportListResponse,
  Dashboard,
  DashboardCreate,
  DashboardUpdate,
  DashboardListResponse,
  AlertRule,
  AlertRuleCreate,
  AlertRuleUpdate,
  AlertRuleListResponse,
  MetricsQuery,
  MetricsResponse,
  PaginationOptions,
  ExportFormat,
  ErrorResponse,
} from './types';

export class ChimeraClient {
  private client: AxiosInstance;
  private config: ChimeraClientConfig;

  constructor(config: ChimeraClientConfig) {
    this.config = config;
    this.client = axios.create({
      baseURL: config.apiUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(config.apiKey && { 'X-API-Key': config.apiKey }),
      },
    });

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ErrorResponse>) => {
        if (error.response?.data) {
          throw new ChimeraError(error.response.data);
        }
        throw error;
      }
    );
  }

  // Health Check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }

  // Query Methods
  async submitQuery(request: QueryRequest): Promise<QuerySubmissionResponse> {
    const response = await this.client.post<QuerySubmissionResponse>('/api/queries', request);
    return response.data;
  }

  async getQueryStatus(queryId: string): Promise<QueryStatusResponse> {
    const response = await this.client.get<QueryStatusResponse>(`/api/queries/${queryId}`);
    return response.data;
  }

  async listQueries(options?: PaginationOptions): Promise<QueryListResponse> {
    const response = await this.client.get<QueryListResponse>('/api/queries', {
      params: options,
    });
    return response.data;
  }

  async cancelQuery(queryId: string): Promise<{ queryId: string; status: string; message: string }> {
    const response = await this.client.delete(`/api/queries/${queryId}`);
    return response.data;
  }

  // Report Methods
  async getReport(reportId: string): Promise<Report> {
    const response = await this.client.get<Report>(`/api/reports/${reportId}`);
    return response.data;
  }

  async listReports(options?: PaginationOptions & { queryId?: string }): Promise<ReportListResponse> {
    const response = await this.client.get<ReportListResponse>('/api/reports', {
      params: options,
    });
    return response.data;
  }

  async exportReport(reportId: string, format: ExportFormat): Promise<Blob | Report> {
    const response = await this.client.get(`/api/reports/${reportId}/export/${format}`, {
      responseType: format === 'json' ? 'json' : 'blob',
    });
    return response.data;
  }

  // Dashboard Methods
  async createDashboard(dashboard: DashboardCreate): Promise<Dashboard> {
    const response = await this.client.post<Dashboard>('/api/dashboards', dashboard);
    return response.data;
  }

  async getDashboard(dashboardId: string): Promise<Dashboard> {
    const response = await this.client.get<Dashboard>(`/api/dashboards/${dashboardId}`);
    return response.data;
  }

  async updateDashboard(dashboardId: string, updates: DashboardUpdate): Promise<Dashboard> {
    const response = await this.client.put<Dashboard>(`/api/dashboards/${dashboardId}`, updates);
    return response.data;
  }

  async deleteDashboard(dashboardId: string): Promise<void> {
    await this.client.delete(`/api/dashboards/${dashboardId}`);
  }

  async listDashboards(options?: PaginationOptions): Promise<DashboardListResponse> {
    const response = await this.client.get<DashboardListResponse>('/api/dashboards', {
      params: options,
    });
    return response.data;
  }

  // Alert Methods
  async createAlertRule(rule: AlertRuleCreate): Promise<AlertRule> {
    const response = await this.client.post<AlertRule>('/api/alerts', rule);
    return response.data;
  }

  async getAlertRule(ruleId: string): Promise<AlertRule> {
    const response = await this.client.get<AlertRule>(`/api/alerts/${ruleId}`);
    return response.data;
  }

  async updateAlertRule(ruleId: string, updates: AlertRuleUpdate): Promise<AlertRule> {
    const response = await this.client.put<AlertRule>(`/api/alerts/${ruleId}`, updates);
    return response.data;
  }

  async deleteAlertRule(ruleId: string): Promise<void> {
    await this.client.delete(`/api/alerts/${ruleId}`);
  }

  async listAlertRules(options?: PaginationOptions & { enabled?: boolean }): Promise<AlertRuleListResponse> {
    const response = await this.client.get<AlertRuleListResponse>('/api/alerts', {
      params: options,
    });
    return response.data;
  }

  // Metrics Methods
  async queryMetrics(query: MetricsQuery): Promise<MetricsResponse> {
    const response = await this.client.get<MetricsResponse>('/api/metrics', {
      params: query,
    });
    return response.data;
  }
}

export class ChimeraError extends Error {
  public code: string;
  public retryable: boolean;
  public details?: Record<string, any>;
  public requestId: string;
  public timestamp: number;

  constructor(errorResponse: ErrorResponse) {
    super(errorResponse.error.message);
    this.name = 'ChimeraError';
    this.code = errorResponse.error.code;
    this.retryable = errorResponse.error.retryable;
    this.details = errorResponse.error.details;
    this.requestId = errorResponse.requestId;
    this.timestamp = errorResponse.timestamp;
  }
}
