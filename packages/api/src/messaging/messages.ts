/**
 * Message utilities and helpers for Protocol Buffer messages
 */
import { v4 as uuidv4 } from 'uuid';

export interface MessageMetadata {
  message_id: string;
  correlation_id: string;
  timestamp: number;
  sender_agent: string;
  reply_to?: string;
}

/**
 * Create message metadata
 */
export function createMetadata(
  senderAgent: string,
  correlationId?: string,
  replyTo?: string
): MessageMetadata {
  return {
    message_id: uuidv4(),
    correlation_id: correlationId || uuidv4(),
    timestamp: Date.now(),
    sender_agent: senderAgent,
    reply_to: replyTo,
  };
}

/**
 * Message builder helper class
 */
export class MessageBuilder {
  private senderAgent: string;

  constructor(senderAgent: string) {
    this.senderAgent = senderAgent;
  }

  /**
   * Create metadata for a message
   */
  createMetadata(correlationId?: string, replyTo?: string): MessageMetadata {
    return createMetadata(this.senderAgent, correlationId, replyTo);
  }
}

/**
 * Extract correlation ID from a message
 */
export function extractCorrelationId(message: any): string | null {
  if (message?.metadata?.correlation_id) {
    return message.metadata.correlation_id;
  }
  return null;
}

/**
 * Extract message ID from a message
 */
export function extractMessageId(message: any): string | null {
  if (message?.metadata?.message_id) {
    return message.metadata.message_id;
  }
  return null;
}
