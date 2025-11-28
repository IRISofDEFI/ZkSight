import { io, Socket } from 'socket.io-client';

export interface WebSocketConfig {
  url: string;
  apiKey?: string;
  autoConnect?: boolean;
}

export interface DashboardUpdateEvent {
  dashboardId: string;
  widgetId: string;
  data: any;
  timestamp: number;
}

export interface AlertEvent {
  alertId: string;
  ruleId: string;
  metric: string;
  currentValue: number;
  threshold: number;
  severity: 'info' | 'warning' | 'critical';
  timestamp: number;
  context: Record<string, any>;
}

export interface QueryUpdateEvent {
  queryId: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress?: number;
  message?: string;
}

export type EventHandler<T> = (data: T) => void;

export class ChimeraWebSocketClient {
  private socket: Socket | null = null;
  private config: WebSocketConfig;
  private eventHandlers: Map<string, Set<EventHandler<any>>> = new Map();

  constructor(config: WebSocketConfig) {
    this.config = config;
    if (config.autoConnect !== false) {
      this.connect();
    }
  }

  connect(): void {
    if (this.socket?.connected) {
      return;
    }

    this.socket = io(this.config.url, {
      auth: {
        apiKey: this.config.apiKey,
      },
      transports: ['websocket', 'polling'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('error', (error: Error) => {
      console.error('WebSocket error:', error);
    });

    // Set up event forwarding
    this.socket.on('dashboard:update', (data: DashboardUpdateEvent) => {
      this.emit('dashboard:update', data);
    });

    this.socket.on('alert', (data: AlertEvent) => {
      this.emit('alert', data);
    });

    this.socket.on('query:update', (data: QueryUpdateEvent) => {
      this.emit('query:update', data);
    });
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.connected ?? false;
  }

  // Subscribe to dashboard updates
  onDashboardUpdate(handler: EventHandler<DashboardUpdateEvent>): () => void {
    return this.on('dashboard:update', handler);
  }

  // Subscribe to alerts
  onAlert(handler: EventHandler<AlertEvent>): () => void {
    return this.on('alert', handler);
  }

  // Subscribe to query updates
  onQueryUpdate(handler: EventHandler<QueryUpdateEvent>): () => void {
    return this.on('query:update', handler);
  }

  // Generic event subscription
  on<T>(event: string, handler: EventHandler<T>): () => void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(event);
      if (handlers) {
        handlers.delete(handler);
      }
    };
  }

  // Emit event to handlers
  private emit<T>(event: string, data: T): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  // Subscribe to specific dashboard
  subscribeToDashboard(dashboardId: string): void {
    if (this.socket) {
      this.socket.emit('subscribe:dashboard', { dashboardId });
    }
  }

  // Unsubscribe from specific dashboard
  unsubscribeFromDashboard(dashboardId: string): void {
    if (this.socket) {
      this.socket.emit('unsubscribe:dashboard', { dashboardId });
    }
  }

  // Subscribe to specific query
  subscribeToQuery(queryId: string): void {
    if (this.socket) {
      this.socket.emit('subscribe:query', { queryId });
    }
  }

  // Unsubscribe from specific query
  unsubscribeFromQuery(queryId: string): void {
    if (this.socket) {
      this.socket.emit('unsubscribe:query', { queryId });
    }
  }
}
