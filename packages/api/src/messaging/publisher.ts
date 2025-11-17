/**
 * Event publisher for sending messages to RabbitMQ
 */
import { Channel, Options } from 'amqplib';
import { ConnectionPool } from './connection';
import { ChannelManager } from './channel';

export interface PublishOptions {
  correlationId?: string;
  replyTo?: string;
  persistent?: boolean;
  headers?: Record<string, any>;
}

export class EventPublisher {
  private connectionPool: ConnectionPool;
  private agentName: string;
  private exchangeName: string;
  private exchangeType: 'direct' | 'topic' | 'fanout' | 'headers';
  private channelManager: ChannelManager;

  constructor(
    connectionPool: ConnectionPool,
    agentName: string,
    exchangeName: string = 'chimera.events',
    exchangeType: 'direct' | 'topic' | 'fanout' | 'headers' = 'topic'
  ) {
    this.connectionPool = connectionPool;
    this.agentName = agentName;
    this.exchangeName = exchangeName;
    this.exchangeType = exchangeType;
    this.channelManager = new ChannelManager(connectionPool);
  }

  /**
   * Initialize publisher by declaring exchange
   */
  async initialize(): Promise<void> {
    try {
      const channel = await this.channelManager.getChannel('publisher');
      await this.channelManager.declareExchange(
        channel,
        this.exchangeName,
        this.exchangeType,
        { durable: true }
      );
    } catch (error) {
      console.error('Failed to setup exchange:', error);
      throw error;
    }
  }

  /**
   * Publish a message to the exchange
   */
  async publish(
    message: Buffer | object,
    routingKey: string,
    options: PublishOptions = {}
  ): Promise<boolean> {
    try {
      const channel = await this.channelManager.getChannel('publisher');

      // Convert object to buffer if needed
      const buffer =
        message instanceof Buffer ? message : Buffer.from(JSON.stringify(message));

      // Build message options
      const publishOptions: Options.Publish = {
        persistent: options.persistent ?? true,
        contentType: message instanceof Buffer ? 'application/x-protobuf' : 'application/json',
        correlationId: options.correlationId,
        replyTo: options.replyTo,
        appId: this.agentName,
        timestamp: Date.now(),
        headers: options.headers,
      };

      // Publish message
      const result = channel.publish(
        this.exchangeName,
        routingKey,
        buffer,
        publishOptions
      );

      if (result) {
        console.log(
          `Published message to ${this.exchangeName} with routing key ${routingKey}`
        );
      } else {
        console.warn('Message was not published (channel buffer full)');
      }

      return result;
    } catch (error) {
      console.error('Failed to publish message:', error);
      throw error;
    }
  }

  /**
   * Publish a message expecting a reply
   */
  async publishWithReply(
    message: Buffer | object,
    routingKey: string,
    replyQueue: string,
    correlationId?: string
  ): Promise<boolean> {
    return this.publish(message, routingKey, {
      replyTo: replyQueue,
      correlationId,
    });
  }

  /**
   * Close publisher resources
   */
  async close(): Promise<void> {
    await this.channelManager.closeAllChannels();
  }
}
