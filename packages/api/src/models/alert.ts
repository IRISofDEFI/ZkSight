import { ObjectId } from 'mongodb';

/**
 * Alert rule schema
 * Requirements: 10.1, 10.3, 10.4
 */

export type AlertOperator = '>' | '<' | '==' | '!=' | 'change_pct' | 'change_abs';
export type AlertSeverity = 'info' | 'warning' | 'critical';
export type NotificationChannel = 'email' | 'webhook' | 'in_app' | 'sms';

export interface AlertCondition {
  metric: string;
  operator: AlertOperator;
  threshold: number;
  duration?: number;
  cooldown?: number;
}

export interface WebhookConfig {
  url: string;
  method: 'POST' | 'GET';
  headers?: Record<string, string>;
  body?: Record<string, any>;
}

export interface EmailConfig {
  to: string[];
  cc?: string[];
  subject?: string;
  template?: string;
}

export interface SmsConfig {
  phoneNumbers: string[];
  message?: string;
}

export interface NotificationChannelConfig {
  type: NotificationChannel;
  enabled: boolean;
  webhook?: WebhookConfig;
  email?: EmailConfig;
  sms?: SmsConfig;
}

export interface AlertRule {
  _id?: ObjectId;
  alertRuleId: string;
  userId: string;
  name: string;
  description?: string;
  condition: AlertCondition;
  channels: NotificationChannelConfig[];
  enabled: boolean;
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
  lastTriggeredAt?: Date;
  triggerCount: number;
}

export interface AlertHistory {
  _id?: ObjectId;
  alertHistoryId: string;
  alertRuleId: string;
  userId: string;
  timestamp: Date;
  metric: string;
  currentValue: number;
  threshold: number;
  severity: AlertSeverity;
  context: Record<string, any>;
  suggestedActions?: string[];
  acknowledged: boolean;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
  notes?: string;
}

export const ALERT_RULE_COLLECTION = 'alert_rules';
export const ALERT_HISTORY_COLLECTION = 'alert_history';

/**
 * MongoDB indexes for alert rule collection
 */
export const ALERT_RULE_INDEXES = [
  {
    key: { alertRuleId: 1 },
    unique: true,
    name: 'idx_alertRuleId',
  },
  {
    key: { userId: 1 },
    name: 'idx_userId',
  },
  {
    key: { userId: 1, enabled: 1 },
    name: 'idx_userId_enabled',
  },
  {
    key: { 'condition.metric': 1 },
    name: 'idx_metric',
  },
  {
    key: { tags: 1 },
    name: 'idx_tags',
  },
];

/**
 * MongoDB indexes for alert history collection
 */
export const ALERT_HISTORY_INDEXES = [
  {
    key: { alertHistoryId: 1 },
    unique: true,
    name: 'idx_alertHistoryId',
  },
  {
    key: { alertRuleId: 1 },
    name: 'idx_alertRuleId',
  },
  {
    key: { userId: 1 },
    name: 'idx_userId',
  },
  {
    key: { userId: 1, timestamp: -1 },
    name: 'idx_userId_timestamp',
  },
  {
    key: { timestamp: -1 },
    name: 'idx_timestamp',
  },
  {
    key: { acknowledged: 1 },
    name: 'idx_acknowledged',
  },
];
