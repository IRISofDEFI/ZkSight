import { ObjectId } from 'mongodb';

/**
 * Dashboard configuration schema
 * Requirements: 8.1, 8.3
 */

export interface LayoutConfig {
  columns: number;
  rowHeight: number;
  breakpoints?: Record<string, number>;
}

export interface WidgetPosition {
  x: number;
  y: number;
  w: number;
  h: number;
}

export type WidgetType = 'chart' | 'metric' | 'alert_list' | 'report';

export interface WidgetConfig {
  metric?: string;
  timeRange?: {
    start: string;
    end: string;
  };
  chartType?: 'line' | 'bar' | 'scatter' | 'heatmap' | 'candlestick';
  aggregation?: 'sum' | 'avg' | 'min' | 'max' | 'count';
  filters?: Record<string, any>;
  displayOptions?: Record<string, any>;
}

export interface Widget {
  id: string;
  type: WidgetType;
  position: WidgetPosition;
  config: WidgetConfig;
  title?: string;
  description?: string;
}

export interface Dashboard {
  _id?: ObjectId;
  dashboardId: string;
  userId: string;
  name: string;
  description?: string;
  layout: LayoutConfig;
  widgets: Widget[];
  refreshInterval: number;
  shared: boolean;
  sharedWith?: string[];
  tags?: string[];
  createdAt: Date;
  updatedAt: Date;
}

export const DASHBOARD_COLLECTION = 'dashboards';

/**
 * MongoDB indexes for dashboard collection
 */
export const DASHBOARD_INDEXES = [
  {
    key: { dashboardId: 1 },
    unique: true,
    name: 'idx_dashboardId',
  },
  {
    key: { userId: 1 },
    name: 'idx_userId',
  },
  {
    key: { userId: 1, createdAt: -1 },
    name: 'idx_userId_createdAt',
  },
  {
    key: { shared: 1 },
    name: 'idx_shared',
  },
  {
    key: { tags: 1 },
    name: 'idx_tags',
  },
];
