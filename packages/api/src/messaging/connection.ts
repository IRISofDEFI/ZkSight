/**
 * RabbitMQ connection management with retry logic and exponential backoff
 */
import amqp, { Connection, Options } from 'amqplib';

export interface RabbitMQConfig {
  host: string;
  port: number;
  username: string;
  password: string;
  vhost: string;
}

export interface ConnectionPoolOptions {
  maxRetries?: number;
  initialRetryDelay?: number;
  maxRetryDelay?: number;
}

export class ConnectionPool {
  private config: RabbitMQConfig;
  private maxRetries: number;
  private initialRetryDelay: number;
  private maxRetryDelay: number;
  private connection: Connection | null = null;

  constructor(config: RabbitMQConfig, options: ConnectionPoolOptions = {}) {
    this.config = config;
    this.maxRetries = options.maxRetries ?? 5;
    this.initialRetryDelay = options.initialRetryDelay ?? 1000; // milliseconds
    this.maxRetryDelay = options.maxRetryDelay ?? 60000; // milliseconds
  }

  /**
   * Build connection URL from config
   */
  private buildConnectionUrl(): string {
    const { username, password, host, port, vhost } = this.config;
    const encodedVhost = encodeURIComponent(vhost);
    return `amqp://${username}:${password}@${host}:${port}/${encodedVhost}`;
  }

  /**
   * Calculate exponential backoff delay
   */
  private calculateRetryDelay(attempt: number): number {
    const delay = this.initialRetryDelay * Math.pow(2, attempt);
    return Math.min(delay, this.maxRetryDelay);
  }

  /**
   * Sleep for specified milliseconds
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  /**
   * Establish connection to RabbitMQ with retry logic
   */
  async connect(): Promise<Connection> {
    if (this.connection) {
      return this.connection;
    }

    const url = this.buildConnectionUrl();
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        console.log(
          `Attempting to connect to RabbitMQ at ${this.config.host}:${this.config.port} ` +
            `(attempt ${attempt + 1}/${this.maxRetries})`
        );

        const options: Options.Connect = {
          heartbeat: 60,
        };

        this.connection = await amqp.connect(url, options);

        // Handle connection errors
        this.connection.on('error', (err) => {
          console.error('RabbitMQ connection error:', err);
          this.connection = null;
        });

        this.connection.on('close', () => {
          console.warn('RabbitMQ connection closed');
          this.connection = null;
        });

        console.log('Successfully connected to RabbitMQ');
        return this.connection;
      } catch (error) {
        lastError = error as Error;

        if (attempt < this.maxRetries - 1) {
          const delay = this.calculateRetryDelay(attempt);
          console.warn(
            `Failed to connect to RabbitMQ: ${lastError.message}. ` +
              `Retrying in ${delay}ms...`
          );
          await this.sleep(delay);
        } else {
          console.error(
            `Failed to connect to RabbitMQ after ${this.maxRetries} attempts`
          );
        }
      }
    }

    throw new Error(
      `Could not connect to RabbitMQ after ${this.maxRetries} attempts: ${lastError?.message}`
    );
  }

  /**
   * Get active connection, reconnecting if necessary
   */
  async getConnection(): Promise<Connection> {
    if (!this.connection) {
      return this.connect();
    }
    return this.connection;
  }

  /**
   * Close the connection gracefully
   */
  async close(): Promise<void> {
    if (this.connection) {
      try {
        console.log('Closing RabbitMQ connection');
        await this.connection.close();
      } catch (error) {
        console.error('Error closing RabbitMQ connection:', error);
      } finally {
        this.connection = null;
      }
    }
  }

  /**
   * Check if connection is active
   */
  isConnected(): boolean {
    return this.connection !== null;
  }
}

// Global connection pool instance
let connectionPool: ConnectionPool | null = null;

/**
 * Get or create global connection pool instance
 */
export function getConnectionPool(config?: RabbitMQConfig): ConnectionPool {
  if (!connectionPool) {
    if (!config) {
      throw new Error('Config must be provided when creating connection pool');
    }
    connectionPool = new ConnectionPool(config);
  }
  return connectionPool;
}
