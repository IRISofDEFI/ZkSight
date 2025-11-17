export interface ChimeraClientConfig {
  apiUrl: string;
  apiKey?: string;
  timeout?: number;
}

export interface QueryRequest {
  query: string;
  sessionId?: string;
}

export interface QueryResponse {
  queryId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  message?: string;
}
