import { ObjectId } from 'mongodb';

/**
 * Query history schema
 * Requirements: 8.1, 8.3, 10.1, 11.1
 */

export type QueryIntentType = 'trend_analysis' | 'anomaly_detection' | 'comparison' | 'explanation';
export type QueryStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';

export interface TimeRange {
  start: string;
  end: string;
}

export interface QueryIntent {
  type: QueryIntentType;
  timeRange: TimeRange;
  metrics: string[];
  confidence: number;
}

export interface ExtractedEntity {
  type: string;
  value: string;
  confidence: number;
  position: {
    start: number;
    end: number;
  };
}

export interface ConversationContext {
  previousQueries: string[];
  entities: Record<string, any>;
  timeRange?: TimeRange;
  metrics?: string[];
}

export interface QueryResults {
  reportId: string;
  executionTime: number;
  dataSourcesUsed: string[];
  recordsProcessed: number;
}

export interface QueryHistory {
  _id?: ObjectId;
  queryId: string;
  userId: string;
  sessionId: string;
  timestamp: Date;
  query: string;
  intent: QueryIntent;
  entities: ExtractedEntity[];
  context?: ConversationContext;
  status: QueryStatus;
  results?: QueryResults;
  error?: {
    code: string;
    message: string;
    details?: Record<string, any>;
  };
  clarificationNeeded: boolean;
  clarificationQuestions?: string[];
  clarificationResponse?: string;
}

export const QUERY_HISTORY_COLLECTION = 'query_history';

/**
 * MongoDB indexes for query history collection
 */
export const QUERY_HISTORY_INDEXES = [
  {
    key: { queryId: 1 },
    unique: true,
    name: 'idx_queryId',
  },
  {
    key: { userId: 1 },
    name: 'idx_userId',
  },
  {
    key: { sessionId: 1 },
    name: 'idx_sessionId',
  },
  {
    key: { userId: 1, timestamp: -1 },
    name: 'idx_userId_timestamp',
  },
  {
    key: { status: 1 },
    name: 'idx_status',
  },
  {
    key: { 'intent.type': 1 },
    name: 'idx_intentType',
  },
  {
    key: { timestamp: -1 },
    name: 'idx_timestamp',
  },
];
