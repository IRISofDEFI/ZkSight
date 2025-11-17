/**
 * Message bus components for agent communication
 */
export { ConnectionPool, getConnectionPool, RabbitMQConfig } from './connection';
export { ChannelManager } from './channel';
export { EventPublisher, PublishOptions } from './publisher';
export { EventSubscriber, MessageHandler, MessageProperties, SubscriberOptions } from './subscriber';
export {
  MessageBuilder,
  MessageMetadata,
  createMetadata,
  extractCorrelationId,
  extractMessageId,
} from './messages';
