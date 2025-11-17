import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import { loadConfig } from './config';

const config = loadConfig();
const app = express();

// Middleware
app.use(helmet());
app.use(cors(config.cors));
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Start server
app.listen(config.port, () => {
  console.log(`API server running on port ${config.port} in ${config.environment} mode`);
});

export default app;
