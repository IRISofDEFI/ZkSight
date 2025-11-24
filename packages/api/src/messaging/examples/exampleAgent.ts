/**
 * Example agent implementation demonstrating publisher and subscriber usage
 */
import { ConnectionPool } from '../connection';
import { EventPublisher } from '../publisher';
import { EventSubscriber, MessageProperties } from '../subscriber';
import { createMetadata } from '../messages';

export class ExampleAgent extends EventSubscriber {
  private publisher: EventPublisher;

  constructor(connectionPool: ConnectionPool) {
    super(connectionPool, 'example_agent', {
      exchangeName: 'chimera.events',
      routingKeys: ['query.request', 'data.request'],
      prefetchCount: 1,
    });

    // Create publisher for sending responses
    this.publisher = new EventPublisher(
      connectionPool,
      'example_agent',
      'chimera.events'
    );
  }

  /**
   * Initialize agent
   */
  async initialize(): Promise<void> {
    await super.initialize();
    await this.publisher.initialize();
    console.log('Example agent initialized');
  }

  /**
   * Handle received message
   */
  async handleMessage(
    message: Buffer,
    properties: MessageProperties
  ): Promise<void> {
    const { routingKey, correlationId } = properties;

    console.log(
      `Processing message with routing key ${routingKey}, ` +
        `correlation_id: ${correlationId}`
    );

    // Process message based on routing key
    if (routingKey === 'query.request') {
      await this.handleQueryRequest(message, correlationId);
    } else if (routingKey === 'data.request') {
      await this.handleDataRequest(message, correlationId);
    } else {
      console.warn(`Unknown routing key: ${routingKey}`);
    }
  }

  /**
   * Handle query request
   */
  private async handleQueryRequest(
    _message: Buffer,
    correlationId?: string
  ): Promise<void> {
    console.log('Handling query request');

    // Parse message (would use protobuf in real implementation)
    // const request = messages.chimera.messaging.QueryRequest.decode(message);

    // Process the query
    // ... agent logic here ...

    // Create and publish response
    const response = {
      metadata: createMetadata('example_agent', correlationId),
      // ... response fields ...
    };

    await this.publisher.publish(
      Buffer.from(JSON.stringify(response)),
      'query.response',
      { correlationId }
    );
  }

  /**
   * Handle data retrieval request
   */
  private async handleDataRequest(
    _message: Buffer,
    correlationId?: string
  ): Promise<void> {
    console.log('Handling data request');

    // Parse message (would use protobuf in real implementation)
    // const request = messages.chimera.messaging.DataRetrievalRequest.decode(message);

    // Retrieve data
    // ... agent logic here ...

    // Create and publish response
    const response = {
      metadata: createMetadata('example_agent', correlationId),
      // ... response fields ...
    };

    await this.publisher.publish(
      Buffer.from(JSON.stringify(response)),
      'data.response',
      { correlationId }
    );
  }

  /**
   * Close agent resources
   */
  async close(): Promise<void> {
    await super.close();
    await this.publisher.close();
  }
}

/**
 * Main entry point for example agent
 */
async function main() {
  // Create connection pool
  const connectionPool = new ConnectionPool({
    host: process.env.RABBITMQ_HOST || 'localhost',
    port: parseInt(process.env.RABBITMQ_PORT || '5672'),
    username: process.env.RABBITMQ_USERNAME || 'guest',
    password: process.env.RABBITMQ_PASSWORD || 'guest',
    vhost: process.env.RABBITMQ_VHOST || '/',
  });

  try {
    // Connect to RabbitMQ
    await connectionPool.connect();

    // Create and start agent
    const agent = new ExampleAgent(connectionPool);
    await agent.initialize();

    console.log('Starting example agent...');
    await agent.startConsuming();

    // Handle shutdown
    process.on('SIGINT', async () => {
      console.log('Shutting down example agent...');
      await agent.close();
      await connectionPool.close();
      process.exit(0);
    });
  } catch (error) {
    console.error('Error running example agent:', error);
    await connectionPool.close();
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}
