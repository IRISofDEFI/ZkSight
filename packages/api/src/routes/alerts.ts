/**
 * Alert management endpoints
 */
import { Router, Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { AuthMiddleware } from '../auth';
import { ApiError } from '../middleware/errorHandler';
import { EventPublisher } from '../messaging';
import { MongoClient, Db, Collection } from 'mongodb';

export interface AlertRule {
  id: string;
  userId: string;
  name: string;
  description?: string;
  condition: AlertCondition;
  channels: NotificationChannel[];
  enabled: boolean;
  createdAt: Date;
  updatedAt: Date;
}

export interface AlertCondition {
  metric: string;
  operator: '>' | '<' | '==' | '!=' | 'change_pct';
  threshold: number;
  duration?: number;
  cooldown?: number;
}

export interface NotificationChannel {
  type: 'email' | 'webhook' | 'sms' | 'in_app';
  config: Record<string, any>;
}

export interface AlertHistory {
  id: string;
  ruleId: string;
  userId: string;
  timestamp: Date;
  metric: string;
  currentValue: number;
  threshold: number;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  acknowledged: boolean;
  acknowledgedAt?: Date;
  acknowledgedBy?: string;
}

export class AlertRoutes {
  private router: Router;
  private authMiddleware: AuthMiddleware;
  private publisher: EventPublisher;
  private db: Db;
  private alertRules: Collection<AlertRule>;
  private alertHistory: Collection<AlertHistory>;

  constructor(
    authMiddleware: AuthMiddleware,
    publisher: EventPublisher,
    mongoClient: MongoClient,
    dbName: string
  ) {
    this.router = Router();
    this.authMiddleware = authMiddleware;
    this.publisher = publisher;
    this.db = mongoClient.db(dbName);
    this.alertRules = this.db.collection<AlertRule>('alert_rules');
    this.alertHistory = this.db.collection<AlertHistory>('alert_history');
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Create alert rule
    this.router.post(
      '/',
      this.authMiddleware.authenticate,
      this.createAlertRule.bind(this)
    );

    // Get alert rule
    this.router.get(
      '/:id',
      this.authMiddleware.authenticate,
      this.getAlertRule.bind(this)
    );

    // Update alert rule
    this.router.put(
      '/:id',
      this.authMiddleware.authenticate,
      this.updateAlertRule.bind(this)
    );

    // Delete alert rule
    this.router.delete(
      '/:id',
      this.authMiddleware.authenticate,
      this.deleteAlertRule.bind(this)
    );

    // List alert rules
    this.router.get(
      '/',
      this.authMiddleware.authenticate,
      this.listAlertRules.bind(this)
    );

    // Test alert rule
    this.router.post(
      '/:id/test',
      this.authMiddleware.authenticate,
      this.testAlertRule.bind(this)
    );

    // Get alert history
    this.router.get(
      '/history',
      this.authMiddleware.authenticate,
      this.getAlertHistory.bind(this)
    );

    // Acknowledge alert
    this.router.post(
      '/history/:id/acknowledge',
      this.authMiddleware.authenticate,
      this.acknowledgeAlert.bind(this)
    );
  }

  /**
   * POST /api/alerts - Create alert rule
   */
  private async createAlertRule(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { name, description, condition, channels, enabled } = req.body;

      if (!name || !condition) {
        throw this.createValidationError('Name and condition are required');
      }

      // Validate condition
      this.validateCondition(condition);

      const alertRule: AlertRule = {
        id: uuidv4(),
        userId: req.user!.id,
        name,
        description,
        condition,
        channels: channels || [],
        enabled: enabled !== false,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      await this.alertRules.insertOne(alertRule);

      // Publish alert rule created event
      await this.publisher.publish(
        {
          ruleId: alertRule.id,
          userId: alertRule.userId,
          condition: alertRule.condition,
          enabled: alertRule.enabled,
        },
        'alert.rule.created',
        { correlationId: req.correlationId }
      );

      res.status(201).json({
        id: alertRule.id,
        name: alertRule.name,
        description: alertRule.description,
        condition: alertRule.condition,
        channels: alertRule.channels,
        enabled: alertRule.enabled,
        createdAt: alertRule.createdAt,
        _links: {
          self: `/api/alerts/${alertRule.id}`,
          test: `/api/alerts/${alertRule.id}/test`,
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/alerts/:id - Get alert rule
   */
  private async getAlertRule(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const rule = await this.alertRules.findOne({ id });
      if (!rule) {
        throw this.createNotFoundError('Alert rule not found');
      }

      // Check authorization
      if (rule.userId !== req.user!.id) {
        throw this.createForbiddenError('Access denied');
      }

      res.json(rule);
    } catch (error) {
      next(error);
    }
  }

  /**
   * PUT /api/alerts/:id - Update alert rule
   */
  private async updateAlertRule(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;
      const { name, description, condition, channels, enabled } = req.body;

      const rule = await this.alertRules.findOne({ id });
      if (!rule) {
        throw this.createNotFoundError('Alert rule not found');
      }

      // Check authorization
      if (rule.userId !== req.user!.id) {
        throw this.createForbiddenError('Access denied');
      }

      // Validate condition if provided
      if (condition) {
        this.validateCondition(condition);
      }

      const updates: any = { updatedAt: new Date() };
      if (name !== undefined) updates.name = name;
      if (description !== undefined) updates.description = description;
      if (condition !== undefined) updates.condition = condition;
      if (channels !== undefined) updates.channels = channels;
      if (enabled !== undefined) updates.enabled = enabled;

      await this.alertRules.updateOne({ id }, { $set: updates });

      // Publish alert rule updated event
      await this.publisher.publish(
        {
          ruleId: id,
          userId: rule.userId,
          updates,
        },
        'alert.rule.updated',
        { correlationId: req.correlationId }
      );

      const updated = await this.alertRules.findOne({ id });
      res.json(updated);
    } catch (error) {
      next(error);
    }
  }

  /**
   * DELETE /api/alerts/:id - Delete alert rule
   */
  private async deleteAlertRule(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const rule = await this.alertRules.findOne({ id });
      if (!rule) {
        throw this.createNotFoundError('Alert rule not found');
      }

      // Check authorization
      if (rule.userId !== req.user!.id) {
        throw this.createForbiddenError('Access denied');
      }

      await this.alertRules.deleteOne({ id });

      // Publish alert rule deleted event
      await this.publisher.publish(
        {
          ruleId: id,
          userId: rule.userId,
        },
        'alert.rule.deleted',
        { correlationId: req.correlationId }
      );

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/alerts - List alert rules
   */
  private async listAlertRules(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
      const skip = (page - 1) * limit;

      const filter: any = { userId: req.user!.id };

      // Filter by enabled status if provided
      if (req.query.enabled !== undefined) {
        filter.enabled = req.query.enabled === 'true';
      }

      const [rules, total] = await Promise.all([
        this.alertRules
          .find(filter)
          .sort({ updatedAt: -1 })
          .skip(skip)
          .limit(limit)
          .toArray(),
        this.alertRules.countDocuments(filter),
      ]);

      res.json({
        rules: rules.map((r) => ({
          id: r.id,
          name: r.name,
          condition: r.condition,
          enabled: r.enabled,
          updatedAt: r.updatedAt,
          _links: {
            self: `/api/alerts/${r.id}`,
          },
        })),
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * POST /api/alerts/:id/test - Test alert rule
   */
  private async testAlertRule(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const rule = await this.alertRules.findOne({ id });
      if (!rule) {
        throw this.createNotFoundError('Alert rule not found');
      }

      // Check authorization
      if (rule.userId !== req.user!.id) {
        throw this.createForbiddenError('Access denied');
      }

      // Publish test alert event
      await this.publisher.publish(
        {
          ruleId: id,
          userId: rule.userId,
          condition: rule.condition,
          test: true,
        },
        'alert.test',
        { correlationId: req.correlationId }
      );

      res.json({
        message: 'Test alert triggered successfully',
        ruleId: id,
        condition: rule.condition,
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/alerts/history - Get alert history
   */
  private async getAlertHistory(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = Math.min(parseInt(req.query.limit as string) || 50, 100);
      const skip = (page - 1) * limit;

      const filter: any = { userId: req.user!.id };

      // Filter by rule ID if provided
      if (req.query.ruleId) {
        filter.ruleId = req.query.ruleId;
      }

      // Filter by severity if provided
      if (req.query.severity) {
        filter.severity = req.query.severity;
      }

      // Filter by acknowledged status if provided
      if (req.query.acknowledged !== undefined) {
        filter.acknowledged = req.query.acknowledged === 'true';
      }

      const [alerts, total] = await Promise.all([
        this.alertHistory
          .find(filter)
          .sort({ timestamp: -1 })
          .skip(skip)
          .limit(limit)
          .toArray(),
        this.alertHistory.countDocuments(filter),
      ]);

      res.json({
        alerts: alerts.map((a) => ({
          id: a.id,
          ruleId: a.ruleId,
          timestamp: a.timestamp,
          metric: a.metric,
          currentValue: a.currentValue,
          threshold: a.threshold,
          severity: a.severity,
          message: a.message,
          acknowledged: a.acknowledged,
          acknowledgedAt: a.acknowledgedAt,
          _links: {
            acknowledge: !a.acknowledged
              ? `/api/alerts/history/${a.id}/acknowledge`
              : undefined,
          },
        })),
        pagination: {
          page,
          limit,
          total,
          pages: Math.ceil(total / limit),
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * POST /api/alerts/history/:id/acknowledge - Acknowledge alert
   */
  private async acknowledgeAlert(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const alert = await this.alertHistory.findOne({ id });
      if (!alert) {
        throw this.createNotFoundError('Alert not found');
      }

      // Check authorization
      if (alert.userId !== req.user!.id) {
        throw this.createForbiddenError('Access denied');
      }

      if (alert.acknowledged) {
        throw this.createValidationError('Alert already acknowledged');
      }

      await this.alertHistory.updateOne(
        { id },
        {
          $set: {
            acknowledged: true,
            acknowledgedAt: new Date(),
            acknowledgedBy: req.user!.id,
          },
        }
      );

      res.json({
        id: alert.id,
        acknowledged: true,
        acknowledgedAt: new Date(),
        message: 'Alert acknowledged successfully',
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * Validate alert condition
   */
  private validateCondition(condition: AlertCondition): void {
    if (!condition.metric) {
      throw this.createValidationError('Condition metric is required');
    }

    if (!['>', '<', '==', '!=', 'change_pct'].includes(condition.operator)) {
      throw this.createValidationError('Invalid condition operator');
    }

    if (typeof condition.threshold !== 'number') {
      throw this.createValidationError('Condition threshold must be a number');
    }

    if (condition.duration !== undefined && condition.duration < 0) {
      throw this.createValidationError('Condition duration must be positive');
    }

    if (condition.cooldown !== undefined && condition.cooldown < 0) {
      throw this.createValidationError('Condition cooldown must be positive');
    }
  }

  private createValidationError(message: string): ApiError {
    const error = new Error(message) as ApiError;
    error.statusCode = 400;
    error.code = 'INVALID_REQUEST';
    error.retryable = false;
    return error;
  }

  private createNotFoundError(message: string): ApiError {
    const error = new Error(message) as ApiError;
    error.statusCode = 404;
    error.code = 'NOT_FOUND';
    error.retryable = false;
    return error;
  }

  private createForbiddenError(message: string): ApiError {
    const error = new Error(message) as ApiError;
    error.statusCode = 403;
    error.code = 'FORBIDDEN';
    error.retryable = false;
    return error;
  }

  getRouter(): Router {
    return this.router;
  }
}
