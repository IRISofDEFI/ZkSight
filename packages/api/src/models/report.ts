import { ObjectId } from 'mongodb';

/**
 * Report document schema with TTL index
 * Requirements: 8.1, 8.3, 10.1, 11.1
 */

export interface ReportMetadata {
  generatedAt: Date;
  executionTime: number;
  dataSourcesUsed: string[];
  version: string;
}

export interface ReportSection {
  title: string;
  content: string;
  order: number;
  visualizationIds?: string[];
}

export interface Report {
  title: string;
  executiveSummary: string;
  sections: ReportSection[];
  metadata: ReportMetadata;
}

export interface Anomaly {
  metric: string;
  timestamp: number;
  value: number;
  expectedValue: number;
  deviationScore: number;
  severity: 'low' | 'medium' | 'high';
  context?: string;
}

export interface Correlation {
  metric1: string;
  metric2: string;
  coefficient: number;
  pValue: number;
  significance: boolean;
  lag?: number;
}

export interface Pattern {
  type: string;
  metric: string;
  description: string;
  confidence: number;
  timeRange: {
    start: number;
    end: number;
  };
}

export interface Statistics {
  mean: number;
  median: number;
  stdDev: number;
  min: number;
  max: number;
  count: number;
}

export interface AnalysisResponse {
  correlations: Correlation[];
  anomalies: Anomaly[];
  patterns: Pattern[];
  statistics: Record<string, Statistics>;
}

export interface Evidence {
  source: string;
  value: number | string;
  timestamp: number;
}

export interface VerifiedClaim {
  id: string;
  statement: string;
  metric: string;
  value: number | string;
  verified: boolean;
  confidence: number;
  sources: string[];
  evidence: Evidence[];
}

export interface DataConflict {
  claimId: string;
  sources: {
    source: string;
    value: number | string;
    difference: number;
  }[];
  resolution?: string;
}

export interface AuditEntry {
  timestamp: Date;
  action: string;
  claimId: string;
  result: 'verified' | 'failed' | 'conflict';
  details: Record<string, any>;
}

export interface FactCheckResponse {
  verifiedClaims: VerifiedClaim[];
  conflicts: DataConflict[];
  auditTrail: AuditEntry[];
  overallConfidence: number;
}

export interface ReportDocument {
  _id?: ObjectId;
  reportId: string;
  userId: string;
  queryId: string;
  query: string;
  createdAt: Date;
  report: Report;
  analysisResults: AnalysisResponse;
  factCheckResults?: FactCheckResponse;
  visualizationUrls: string[];
  expiresAt: Date;
}

export const REPORT_COLLECTION = 'reports';

/**
 * MongoDB indexes for report collection
 * Includes TTL index for automatic expiration
 */
export const REPORT_INDEXES = [
  {
    key: { reportId: 1 },
    unique: true,
    name: 'idx_reportId',
  },
  {
    key: { userId: 1 },
    name: 'idx_userId',
  },
  {
    key: { queryId: 1 },
    name: 'idx_queryId',
  },
  {
    key: { userId: 1, createdAt: -1 },
    name: 'idx_userId_createdAt',
  },
  {
    key: { expiresAt: 1 },
    expireAfterSeconds: 0,
    name: 'idx_ttl',
  },
];
