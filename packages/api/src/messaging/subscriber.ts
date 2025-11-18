/**
 * Event subscriber for consuming messages from RabbitMQ
 */
import { ConsumeMessage } from 'amqplib';
import { ConnectionPool } from './connection';
import { ChannelManager } from './channel';

export interface MessageProperties {
  routingKey: string;
  correlationId?: string;
  deliveryTag: number;
  appId?: string;
  headers?: Record<string, any>;
}

export type MessageHandler = (
  message: Buffer,
  properties: MessageProperties
) => Promise<void> | void;

export interface SubscriberOptions {
  exchangeName?: string;
  queueName?: string;
  routingKeys?: string[];
  prefetchCount?: number;
  durable?: boolean;
}

export abstract class EventSubscriber {
  protected connectionPool: ConnectionPool;
  protected agentName: string;
  protected exchangeName: string;
  protected queueName: string;
  protected routingKeys: string[];
  protected prefetchCount: number;
  protected durable: boolean;
  protected channelManager: ChannelManager;
  private consuming: boolean = false;
  private consumerTag?: string;

  constructor(
    connectionPool: ConnectionPool,
    agentName: string,
    options: SubscriberOptions = {}
  ) {
    this.connectionPool = connectionPool;
    this.agentName = agentName;
    this.exchangeName = options.exchangeName ?? 'chimera.events';
    this.queueName = options.queueName ?? agentName;
    this.routingKeys = options.routingKeys ?? ['#'];
    this.prefetchCount = options.prefetchCount ?? 1;
    this.durable = options.durable ?? true;
    this.channelManager = new ChannelManager(connectionPool);
  }

  /**
   * Initialize subscriber by setting up queue and bindings
   */
  async initialize(): Promise<void> {
    try {
      const channel = await this.channelManager.getChannel('subscriber');

      // Declare exchange
      await this.channelManager.declareExchange(
        channel,
        this.exchangeName,
        'topic',
        { durable: this.durable }
      );

      // Declare dead letter exchange
      const dlxName = `${this.exchangeName}.dlx`;
      await this.channelManager.declareExchange(channel, dlxName, 'topic', {
        durable: this.durable,
      });

      // Declare main queue with DLX
      await this.channelManager.declareQueue(channel, this.queueName, {
        durable: this.durable,
        arguments: {
          'x-dead-letter-exchange': dlxName,
          'x-message-ttl': 86400000, // 24 hours
        },
      });

      // Declare dead letter queue
      const dlqName = `${this.queueName}.dlq`;
      await this.channelManager.declareQueue(channel, dlqName, {
        durable: this.durable,
      });

      // Bind dead letter queue
      for (const routingKey of this.routingKeys) {
        await this.channelManager.bindQueue(channel, dlqName, dlxName, routingKey);
      }

      // Bind main queue to exchange
      for (const routingKey of this.routingKeys) {
        await this.channelManager.bindQueue(
          channel,
          this.queueName,
          this.exchangeName,
          routingKey
        );
      }

      // Set QoS
      await this.channelManager.setPrefetch(channel, this.prefetchCount);

      console.log(
        `Setup queue ${this.queueName} bound to ${this.exchangeName} ` +
          `with routing keys ${this.routingKeys.join(', ')}`
      );
    } catch (error) {
      console.error('Failed to setup queue:', error);
      throw error;
    }
  }

  /**
   * Handle received message (must be implemented by subclasses)
   */
  abstract handleMessage(
    message: Buffer,
    properties: MessageProperties
  ): Promise<void> | void;

  /**
   * Internal message callback
   */
  private async onMessage(msg: ConsumeMessage | null): Promise<void> {
    if (!msg) {
      console.warn('Received null message');
      return;
    }

    const channel = await this.channelManager.getChannel('subscriber');

    try {
      // Extract properties
      const properties: MessageProperties = {
        routingKey: msg.fields.routingKey,
        correlationId: msg.properties.correlationId,
        deliveryTag: msg.fields.deliveryTag,
        appId: msg.properties.appId,
        headers: msg.properties.headers,
      };

      console.log(
        `Received message with routing key ${msg.fields.routingKey} ` +
          `(correlation_id: ${msg.properties.correlationId})`
      );

      // Handle message
      await this.handleMessage(msg.content, properties);

      // Acknowledge message
      channel.ack(msg);
      console.log(`Acknowledged message ${msg.fields.deliveryTag}`);
    } catch (error) {
      console.error('Error processing message:', error);
      // Reject and send to DLQ
      channel.nack(msg, false, false);
    }
  }

  /**
   * Start consuming messages
   */
  async startConsuming(): Promise<void> {
    try {
      const channel = await this.channelManager.getChannel('subscriber');

      const { consumerTag } = await channel.consume(
        this.queueName,
        (msg: any) => this.onMessage(msg),
        { noAck: false }
      );

      this.consumerTag = consumerTag;
      this.consuming = true;
      console.log(`Started consuming from queue ${this.queueName}`);
    } catch (error) {
      console.error('Error starting consumer:', error);
      throw error;
    }
  }

  /**
   * Stop consuming messages
   */
  async stopConsuming(): Promise<void> {
    if (this.consuming && this.consumerTag) {
      try {
        const channel = await this.channelManager.getChannel('subscriber');
        await channel.cancel(this.consumerTag);
        this.consuming = false;
        console.log('Stopped consuming');
      } catch (error) {
        console.error('Error stopping consumer:', error);
      }
    }
  }

  /**
   * Check if currently consuming
   */
  isConsuming(): boolean {
    return this.consuming;
  }

  /**
   * Close subscriber resources
   */
  async close(): Promise<void> {
    await this.stopConsuming();
    await this.channelManager.closeAllChannels();
  }
}
