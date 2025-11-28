export interface ChimeraClientConfig {
  apiUrl: string;
  apiKey?: string;
  timeout?: number;
  enableWebSocket?: boolean;
}

export interface QueryRequest {
  query: string;
  sessionId?: string;
  context?: Record<string, any>;
}

export interface QuerySubmissionResponse {
  queryId: string;
  status: 'pending';
  message?: string;
  _links?: {
    self: string;
    cancel: string;
  };
}

export interface QueryStatusResponse {
  queryId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  query: string;
  result?: {
    reportId?: string;
    error?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export interface QueryListItem {
  queryId: string;
  query: string;
  status: string;
  createdAt: string;
}

export interface QueryListResponse {
  queries: QueryListItem[];
  pagination: Pagination;
}

export interface Report {
  reportId: string;
  queryId: string;
  title: string;
  executiveSummary: string;
  sections: ReportSection[];
  visualizations: string[];
  metadata: Record<string, any>;
  createdAt: string;
}

export interface ReportSection {
  title: string;
  content: string;
  order: number;
}

export interface ReportListResponse {
  reports: Report[];
  pagination: Pagination;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  layout: Record<string, any>;
  widgets: Widget[];
  refreshInterval: number;
  shared: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'alert_list' | 'report';
  position: { x: number; y: number; w: number; h: number };
  config: Record<string, any>;
}

export interface DashboardCreate {
  name: string;
  description?: string;
  layout?: Record<string, any>;
  widgets?: Widget[];
  refreshInterval?: number;
}

export interface DashboardUpdate {
  name?: string;
  description?: string;
  layout?: Record<string, any>;
  widgets?: Widget[];
  refreshInterval?: number;
}

export interface DashboardListResponse {
  dashboards: Dashboard[];
  pagination: Pagination;
}

export interface AlertRule {
  id: string;
  name: string;
  description?: string;
  condition: AlertCondition;
  channels: NotificationChannel[];
  enabled: boolean;
  createdAt: string;
  updatedAt: string;
}

export interface AlertCondition {
  metric: string;
  operator: '>' | '<' | '==' | '!=' | 'change_pct';
  threshold: number;
  duration?: number;
  cooldown?: number;
}

export interface NotificationChannel {
  type: 'email' | 'webhook' | 'websocket' | 'sms';
  config: Record<string, any>;
}

export interface AlertRuleCreate {
  name: string;
  description?: string;
  condition: AlertCondition;
  channels?: NotificationChannel[];
  enabled?: boolean;
}

export interface AlertRuleUpdate {
  name?: string;
  description?: string;
  condition?: AlertCondition;
  channels?: NotificationChannel[];
  enabled?: boolean;
}

export interface AlertRuleListResponse {
  rules: AlertRule[];
  pagination: Pagination;
}

export interface MetricsQuery {
  metric: string;
  start: string;
  end?: string;
  aggregation?: 'mean' | 'sum' | 'min' | 'max' | 'count';
  interval?: string;
}

export interface MetricsResponse {
  metric: string;
  timeRange: Record<string, any>;
  aggregation?: string;
  interval?: string;
  data: MetricDataPoint[];
  count: number;
}

export interface MetricDataPoint {
  timestamp: string;
  value: number;
  tags?: Record<string, string>;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  pages: number;
}

export interface ErrorResponse {
  error: {
    code: string;
    message: string;
    retryable: boolean;
    details?: Record<string, any>;
  };
  requestId: string;
  timestamp: number;
}

export interface PaginationOptions {
  page?: number;
  limit?: number;
}

export type ExportFormat = 'pdf' | 'html' | 'json';
