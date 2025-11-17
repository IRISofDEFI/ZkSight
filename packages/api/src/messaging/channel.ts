/**
 * Channel management utilities for RabbitMQ
 */
import { Channel, Options } from 'amqplib';
import { ConnectionPool } from './connection';

export class ChannelManager {
  private connectionPool: ConnectionPool;
  private channels: Map<string, Channel> = new Map();

  constructor(connectionPool: ConnectionPool) {
    this.connectionPool = connectionPool;
  }

  /**
   * Get or create a channel
   */
  async getChannel(channelId: string = 'default'): Promise<Channel> {
    // Check if we have an existing channel
    const existingChannel = this.channels.get(channelId);
    if (existingChannel) {
      return existingChannel;
    }

    // Create new channel
    try {
      const connection = await this.connectionPool.getConnection();
      const channel = await connection.createChannel();

      // Handle channel errors
      channel.on('error', (err) => {
        console.error(`Channel ${channelId} error:`, err);
        this.channels.delete(channelId);
      });

      channel.on('close', () => {
        console.warn(`Channel ${channelId} closed`);
        this.channels.delete(channelId);
      });

      this.channels.set(channelId, channel);
      console.log(`Created new channel: ${channelId}`);
      return channel;
    } catch (error) {
      console.error(`Failed to create channel ${channelId}:`, error);
      throw new Error(`Could not create channel: ${error}`);
    }
  }

  /**
   * Close a specific channel
   */
  async closeChannel(channelId: string = 'default'): Promise<void> {
    const channel = this.channels.get(channelId);
    if (channel) {
      try {
        console.log(`Closing channel: ${channelId}`);
        await channel.close();
      } catch (error) {
        console.error(`Error closing channel ${channelId}:`, error);
      } finally {
        this.channels.delete(channelId);
      }
    }
  }

  /**
   * Close all managed channels
   */
  async closeAllChannels(): Promise<void> {
    const channelIds = Array.from(this.channels.keys());
    await Promise.all(channelIds.map((id) => this.closeChannel(id)));
  }

  /**
   * Declare an exchange
   */
  async declareExchange(
    channel: Channel,
    exchangeName: string,
    exchangeType: 'direct' | 'topic' | 'fanout' | 'headers' = 'topic',
    options: Options.AssertExchange = {}
  ): Promise<void> {
    try {
      await channel.assertExchange(exchangeName, exchangeType, {
        durable: true,
        ...options,
      });
      console.log(`Declared exchange: ${exchangeName} (type: ${exchangeType})`);
    } catch (error) {
      console.error(`Failed to declare exchange ${exchangeName}:`, error);
      throw error;
    }
  }

  /**
   * Declare a queue
   */
  async declareQueue(
    channel: Channel,
    queueName: string,
    options: Options.AssertQueue = {}
  ): Promise<{ queue: string; messageCount: number; consumerCount: number }> {
    try {
      const result = await channel.assertQueue(queueName, {
        durable: true,
        ...options,
      });
      console.log(`Declared queue: ${queueName}`);
      return result;
    } catch (error) {
      console.error(`Failed to declare queue ${queueName}:`, error);
      throw error;
    }
  }

  /**
   * Bind a queue to an exchange with a routing key
   */
  async bindQueue(
    channel: Channel,
    queueName: string,
    exchangeName: string,
    routingKey: string
  ): Promise<void> {
    try {
      await channel.bindQueue(queueName, exchangeName, routingKey);
      console.log(
        `Bound queue ${queueName} to exchange ${exchangeName} with routing key ${routingKey}`
      );
    } catch (error) {
      console.error(
        `Failed to bind queue ${queueName} to exchange ${exchangeName}:`,
        error
      );
      throw error;
    }
  }

  /**
   * Set prefetch count for a channel (QoS)
   */
  async setPrefetch(channel: Channel, count: number): Promise<void> {
    try {
      await channel.prefetch(count);
      console.log(`Set prefetch count to ${count}`);
    } catch (error) {
      console.error(`Failed to set prefetch count:`, error);
      throw error;
    }
  }
}
