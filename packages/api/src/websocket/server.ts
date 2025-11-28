/**
 * WebSocket server for real-time updates
 */
import { Server as HttpServer } from 'http';
import { Server, Socket } from 'socket.io';
import { JwtService } from '../auth';
import { EventSubscriber, MessageProperties } from '../messaging';
import { ConnectionPool } from '../messaging';

export interface WebSocketConfig {
  cors: {
    origin: string;
    credentials: boolean;
  };
}

export class WebSocketServer {
  private io: Server;
  private jwtService: JwtService;
  private connectionPool: ConnectionPool;
  private subscribers: Map<string, EventSubscriber> = new Map();

  constructor(
    httpServer: HttpServer,
    jwtService: JwtService,
    connectionPool: ConnectionPool,
    config: WebSocketConfig
  ) {
    this.jwtService = jwtService;
    this.connectionPool = connectionPool;

    // Initialize Socket.io server
    this.io = new Server(httpServer, {
      cors: config.cors,
      path: '/ws',
    });

    this.setupAuthentication();
    this.setupEventHandlers();
    this.setupMessageBusSubscribers();
  }

  /**
   * Setup authentication middleware
   */
  private setupAuthentication(): void {
    this.io.use(async (socket, next) => {
      try {
        const token = socket.handshake.auth.token;
        
        if (!token) {
          return next(new Error('Authentication required'));
        }

        // Verify JWT token
        const payload = this.jwtService.verifyToken(token);
        
        // Attach user info to socket
        (socket as any).userId = payload.userId;
        (socket as any).userRole = payload.role;
        
        next();
      } catch (error) {
        next(new Error('Invalid token'));
      }
    });
  }

  /**
   * Setup event handlers for client connections
   */
  private setupEventHandlers(): void {
    this.io.on('connection', (socket: Socket) => {
      const userId = (socket as any).userId;
      console.log(`WebSocket client connected: ${socket.id} (user: ${userId})`);

      // Join user-specific room
      socket.join(`user:${userId}`);

      // Handle dashboard subscription
      socket.on('subscribe:dashboard', (dashboardId: string) => {
        console.log(`Client ${socket.id} subscribed to dashboard ${dashboardId}`);
        socket.join(`dashboard:${dashboardId}`);
        socket.emit('subscribed', { type: 'dashboard', id: dashboardId });
      });

      // Handle dashboard unsubscription
      socket.on('unsubscribe:dashboard', (dashboardId: string) => {
        console.log(`Client ${socket.id} unsubscribed from dashboard ${dashboardId}`);
        socket.leave(`dashboard:${dashboardId}`);
        socket.emit('unsubscribed', { type: 'dashboard', id: dashboardId });
      });

      // Handle query subscription
      socket.on('subscribe:query', (queryId: string) => {
        console.log(`Client ${socket.id} subscribed to query ${queryId}`);
        socket.join(`query:${queryId}`);
        socket.emit('subscribed', { type: 'query', id: queryId });
      });

      // Handle query unsubscription
      socket.on('unsubscribe:query', (queryId: string) => {
        console.log(`Client ${socket.id} unsubscribed from query ${queryId}`);
        socket.leave(`query:${queryId}`);
        socket.emit('unsubscribed', { type: 'query', id: queryId });
      });

      // Handle alert subscription
      socket.on('subscribe:alerts', () => {
        console.log(`Client ${socket.id} subscribed to alerts`);
        socket.join(`alerts:${userId}`);
        socket.emit('subscribed', { type: 'alerts' });
      });

      // Handle alert unsubscription
      socket.on('unsubscribe:alerts', () => {
        console.log(`Client ${socket.id} unsubscribed from alerts`);
        socket.leave(`alerts:${userId}`);
        socket.emit('unsubscribed', { type: 'alerts' });
      });

      // Handle ping/pong for connection health
      socket.on('ping', () => {
        socket.emit('pong', { timestamp: Date.now() });
      });

      // Handle disconnection
      socket.on('disconnect', (reason) => {
        console.log(`WebSocket client disconnected: ${socket.id} (reason: ${reason})`);
      });

      // Handle errors
      socket.on('error', (error) => {
        console.error(`WebSocket error for client ${socket.id}:`, error);
      });
    });
  }

  /**
   * Setup message bus subscribers to forward events to WebSocket clients
   */
  private setupMessageBusSubscribers(): void {
    // Subscribe to query status updates
    this.createSubscriber(
      'query-updates',
      ['query.#'],
      async (message: Buffer, properties: MessageProperties) => {
        const data = JSON.parse(message.toString());
        const routingKey = properties.routingKey;

        if (routingKey === 'query.submitted') {
          this.io.to(`query:${data.queryId}`).emit('query:submitted', data);
        } else if (routingKey === 'query.processing') {
          this.io.to(`query:${data.queryId}`).emit('query:processing', data);
        } else if (routingKey === 'query.completed') {
          this.io.to(`query:${data.queryId}`).emit('query:completed', data);
          if (data.userId) {
            this.io.to(`user:${data.userId}`).emit('query:completed', data);
          }
        } else if (routingKey === 'query.failed') {
          this.io.to(`query:${data.queryId}`).emit('query:failed', data);
          if (data.userId) {
            this.io.to(`user:${data.userId}`).emit('query:failed', data);
          }
        }
      }
    );

    // Subscribe to alert events
    this.createSubscriber(
      'alert-updates',
      ['alert.#'],
      async (message: Buffer, properties: MessageProperties) => {
        const data = JSON.parse(message.toString());
        const routingKey = properties.routingKey;

        if (routingKey === 'alert.triggered') {
          // Send to user-specific room
          if (data.userId) {
            this.io.to(`alerts:${data.userId}`).emit('alert:triggered', data);
            this.io.to(`user:${data.userId}`).emit('alert:triggered', data);
          }
        }
      }
    );

    // Subscribe to dashboard data updates
    this.createSubscriber(
      'dashboard-updates',
      ['dashboard.#'],
      async (message: Buffer, properties: MessageProperties) => {
        const data = JSON.parse(message.toString());
        const routingKey = properties.routingKey;

        if (routingKey === 'dashboard.data.updated') {
          this.io.to(`dashboard:${data.dashboardId}`).emit('dashboard:data', data);
        }
      }
    );

    // Subscribe to metric updates
    this.createSubscriber(
      'metric-updates',
      ['metric.#'],
      async (message: Buffer, properties: MessageProperties) => {
        const data = JSON.parse(message.toString());
        
        // Broadcast to all connected clients
        this.io.emit('metric:updated', data);
      }
    );
  }

  /**
   * Create a message bus subscriber
   */
  private createSubscriber(
    name: string,
    routingKeys: string[],
    handler: (message: Buffer, properties: MessageProperties) => Promise<void>
  ): void {
    class DynamicSubscriber extends EventSubscriber {
      async handleMessage(
        message: Buffer,
        properties: MessageProperties
      ): Promise<void> {
        await handler(message, properties);
      }
    }

    const subscriber = new DynamicSubscriber(this.connectionPool, name, {
      routingKeys,
      queueName: `websocket.${name}`,
    });

    this.subscribers.set(name, subscriber);

    // Initialize and start consuming
    subscriber.initialize().then(() => {
      subscriber.startConsuming();
      console.log(`WebSocket subscriber ${name} started`);
    }).catch((error) => {
      console.error(`Failed to start WebSocket subscriber ${name}:`, error);
    });
  }

  /**
   * Emit event to specific room
   */
  emitToRoom(room: string, event: string, data: any): void {
    this.io.to(room).emit(event, data);
  }

  /**
   * Emit event to specific user
   */
  emitToUser(userId: string, event: string, data: any): void {
    this.io.to(`user:${userId}`).emit(event, data);
  }

  /**
   * Broadcast event to all connected clients
   */
  broadcast(event: string, data: any): void {
    this.io.emit(event, data);
  }

  /**
   * Get number of connected clients
   */
  getConnectionCount(): number {
    return this.io.sockets.sockets.size;
  }

  /**
   * Close WebSocket server and cleanup
   */
  async close(): Promise<void> {
    // Stop all subscribers
    for (const [name, subscriber] of this.subscribers) {
      await subscriber.close();
      console.log(`WebSocket subscriber ${name} stopped`);
    }

    // Close Socket.io server
    this.io.close();
    console.log('WebSocket server closed');
  }
}
