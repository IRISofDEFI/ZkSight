import axios, { AxiosInstance } from 'axios';
import { ChimeraClientConfig, QueryRequest, QueryResponse } from './types';

export class ChimeraClient {
  private client: AxiosInstance;

  constructor(config: ChimeraClientConfig) {
    this.client = axios.create({
      baseURL: config.apiUrl,
      timeout: config.timeout || 30000,
      headers: {
        'Content-Type': 'application/json',
        ...(config.apiKey && { Authorization: `Bearer ${config.apiKey}` }),
      },
    });
  }

  async submitQuery(request: QueryRequest): Promise<QueryResponse> {
    const response = await this.client.post<QueryResponse>('/api/queries', request);
    return response.data;
  }

  async getQueryStatus(queryId: string): Promise<QueryResponse> {
    const response = await this.client.get<QueryResponse>(`/api/queries/${queryId}`);
    return response.data;
  }

  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    const response = await this.client.get('/health');
    return response.data;
  }
}
