/**
 * Main server setup with all routes and services
 */
import express from 'express';
import { createServer } from 'http';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { MongoClient } from 'mongodb';
import { loadConfig } from './config';
import {
  correlationIdMiddleware,
  requestLogger,
  createRateLimiter,
  errorHandler,
  notFoundHandler,
} from './middleware';
import { JwtService, AuthDatabase, AuthMiddleware } from './auth';
import { getConnectionPool, EventPublisher } from './messaging';
import { QueryRoutes, ReportRoutes, DashboardRoutes, AlertRoutes, MetricsRoutes } from './routes';
import { WebSocketServer } from './websocket';

export async function createApp() {
  const config = loadConfig();
  const app = express();
  const httpServer = createServer(app);

  // Security and performance middleware
  app.use(helmet());
  app.use(cors(config.cors));
  app.use(compression());

  // Request parsing
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // Correlation ID for distributed tracing
  app.use(correlationIdMiddleware);

  // Request logging
  app.use(requestLogger);

  // Rate limiting
  app.use(createRateLimiter(config));

  // Health check endpoint
  app.get('/health', (_req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
  });

  // Initialize services
  console.log('Initializing services...');

  // MongoDB connection
  const mongoClient = new MongoClient(config.mongodb.uri);
  await mongoClient.connect();
  console.log('Connected to MongoDB');

  // Auth services
  const authDb = new AuthDatabase(config);
  await authDb.connect(config.mongodb.database);
  console.log('Auth database initialized');

  const jwtService = new JwtService(config);
  const authMiddleware = new AuthMiddleware(jwtService, authDb);

  // Message bus connection
  const connectionPool = getConnectionPool({
    host: config.rabbitmq.host,
    port: config.rabbitmq.port,
    username: config.rabbitmq.username,
    password: config.rabbitmq.password,
    vhost: config.rabbitmq.vhost,
  });
  console.log('Message bus connection pool created');

  // Event publisher
  const publisher = new EventPublisher(
    connectionPool,
    'api-server',
    'chimera.events',
    'topic'
  );
  await publisher.initialize();
  console.log('Event publisher initialized');

  // Initialize routes
  const queryRoutes = new QueryRoutes(
    publisher,
    authMiddleware,
    mongoClient,
    config.mongodb.database
  );
  app.use('/api/queries', queryRoutes.getRouter());

  const reportRoutes = new ReportRoutes(
    authMiddleware,
    mongoClient,
    config.mongodb.database
  );
  app.use('/api/reports', reportRoutes.getRouter());

  const dashboardRoutes = new DashboardRoutes(
    authMiddleware,
    mongoClient,
    config.mongodb.database
  );
  app.use('/api/dashboards', dashboardRoutes.getRouter());

  const alertRoutes = new AlertRoutes(
    authMiddleware,
    publisher,
    mongoClient,
    config.mongodb.database
  );
  app.use('/api/alerts', alertRoutes.getRouter());

  const metricsRoutes = new MetricsRoutes(authMiddleware, config);
  app.use('/api/metrics', metricsRoutes.getRouter());

  console.log('API routes initialized');

  // Initialize WebSocket server
  const wsServer = new WebSocketServer(
    httpServer,
    jwtService,
    connectionPool,
    { cors: config.cors }
  );
  console.log('WebSocket server initialized');

  // 404 handler
  app.use(notFoundHandler);

  // Global error handler (must be last)
  app.use(errorHandler);

  // Graceful shutdown
  const shutdown = async () => {
    console.log('Shutting down gracefully...');
    
    httpServer.close(() => {
      console.log('HTTP server closed');
    });

    await wsServer.close();
    await publisher.close();
    await authDb.close();
    await mongoClient.close();
    
    console.log('All connections closed');
    process.exit(0);
  };

  process.on('SIGTERM', shutdown);
  process.on('SIGINT', shutdown);

  return { app, httpServer, config };
}

// Start server if this file is run directly
if (require.main === module) {
  createApp()
    .then(({ httpServer, config }) => {
      httpServer.listen(config.port, () => {
        console.log(`API server running on port ${config.port} in ${config.environment} mode`);
        console.log(`WebSocket server available at ws://localhost:${config.port}/ws`);
      });
    })
    .catch((error) => {
      console.error('Failed to start server:', error);
      process.exit(1);
    });
}
