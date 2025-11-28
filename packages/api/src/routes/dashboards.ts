/**
 * Dashboard configuration endpoints
 */
import { Router, Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { AuthMiddleware } from '../auth';
import { ApiError } from '../middleware/errorHandler';
import { MongoClient, Db, Collection } from 'mongodb';

export interface Dashboard {
  id: string;
  userId: string;
  name: string;
  description?: string;
  layout: LayoutConfig;
  widgets: Widget[];
  refreshInterval: number;
  shared: boolean;
  sharedWith?: string[];
  createdAt: Date;
  updatedAt: Date;
}

export interface LayoutConfig {
  columns: number;
  rowHeight: number;
}

export interface Widget {
  id: string;
  type: 'chart' | 'metric' | 'alert_list' | 'report';
  position: { x: number; y: number; w: number; h: number };
  config: WidgetConfig;
}

export interface WidgetConfig {
  title?: string;
  metric?: string;
  timeRange?: string;
  chartType?: string;
  aggregation?: string;
  filters?: Record<string, any>;
  [key: string]: any;
}

export class DashboardRoutes {
  private router: Router;
  private authMiddleware: AuthMiddleware;
  private db: Db;
  private dashboards: Collection<Dashboard>;

  constructor(
    authMiddleware: AuthMiddleware,
    mongoClient: MongoClient,
    dbName: string
  ) {
    this.router = Router();
    this.authMiddleware = authMiddleware;
    this.db = mongoClient.db(dbName);
    this.dashboards = this.db.collection<Dashboard>('dashboards');
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Create dashboard
    this.router.post(
      '/',
      this.authMiddleware.authenticate,
      this.createDashboard.bind(this)
    );

    // Get dashboard
    this.router.get(
      '/:id',
      this.authMiddleware.authenticate,
      this.getDashboard.bind(this)
    );

    // Update dashboard
    this.router.put(
      '/:id',
      this.authMiddleware.authenticate,
      this.updateDashboard.bind(this)
    );

    // Delete dashboard
    this.router.delete(
      '/:id',
      this.authMiddleware.authenticate,
      this.deleteDashboard.bind(this)
    );

    // List dashboards
    this.router.get(
      '/',
      this.authMiddleware.authenticate,
      this.listDashboards.bind(this)
    );

    // Share dashboard
    this.router.post(
      '/:id/share',
      this.authMiddleware.authenticate,
      this.shareDashboard.bind(this)
    );

    // Unshare dashboard
    this.router.delete(
      '/:id/share',
      this.authMiddleware.authenticate,
      this.unshareDashboard.bind(this)
    );

    // Add widget
    this.router.post(
      '/:id/widgets',
      this.authMiddleware.authenticate,
      this.addWidget.bind(this)
    );

    // Update widget
    this.router.put(
      '/:id/widgets/:widgetId',
      this.authMiddleware.authenticate,
      this.updateWidget.bind(this)
    );

    // Delete widget
    this.router.delete(
      '/:id/widgets/:widgetId',
      this.authMiddleware.authenticate,
      this.deleteWidget.bind(this)
    );
  }

  /**
   * POST /api/dashboards - Create dashboard
   */
  private async createDashboard(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { name, description, layout, widgets, refreshInterval } = req.body;

      if (!name) {
        throw this.createValidationError('Dashboard name is required');
      }

      const dashboard: Dashboard = {
        id: uuidv4(),
        userId: req.user!.id,
        name,
        description,
        layout: layout || { columns: 12, rowHeight: 100 },
        widgets: widgets || [],
        refreshInterval: refreshInterval || 60000,
        shared: false,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      await this.dashboards.insertOne(dashboard);

      res.status(201).json({
        id: dashboard.id,
        name: dashboard.name,
        description: dashboard.description,
        layout: dashboard.layout,
        widgets: dashboard.widgets,
        refreshInterval: dashboard.refreshInterval,
        shared: dashboard.shared,
        createdAt: dashboard.createdAt,
        _links: {
          self: `/api/dashboards/${dashboard.id}`,
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/dashboards/:id - Get dashboard
   */
  private async getDashboard(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization
      if (!this.canAccessDashboard(dashboard, req.user!.id)) {
        throw this.createForbiddenError('Access denied');
      }

      res.json({
        id: dashboard.id,
        name: dashboard.name,
        description: dashboard.description,
        layout: dashboard.layout,
        widgets: dashboard.widgets,
        refreshInterval: dashboard.refreshInterval,
        shared: dashboard.shared,
        createdAt: dashboard.createdAt,
        updatedAt: dashboard.updatedAt,
        _links: {
          self: `/api/dashboards/${dashboard.id}`,
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * PUT /api/dashboards/:id - Update dashboard
   */
  private async updateDashboard(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;
      const { name, description, layout, widgets, refreshInterval } = req.body;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can update)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can update');
      }

      const updates: any = { updatedAt: new Date() };
      if (name !== undefined) updates.name = name;
      if (description !== undefined) updates.description = description;
      if (layout !== undefined) updates.layout = layout;
      if (widgets !== undefined) updates.widgets = widgets;
      if (refreshInterval !== undefined) updates.refreshInterval = refreshInterval;

      await this.dashboards.updateOne({ id }, { $set: updates });

      const updated = await this.dashboards.findOne({ id });
      res.json(updated);
    } catch (error) {
      next(error);
    }
  }

  /**
   * DELETE /api/dashboards/:id - Delete dashboard
   */
  private async deleteDashboard(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can delete)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can delete');
      }

      await this.dashboards.deleteOne({ id });

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/dashboards - List dashboards
   */
  private async listDashboards(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
      const skip = (page - 1) * limit;

      // Find dashboards owned by user or shared with user
      const filter = {
        $or: [
          { userId: req.user!.id },
          { shared: true, sharedWith: req.user!.id },
        ],
      };

      const [dashboards, total] = await Promise.all([
        this.dashboards
          .find(filter)
          .sort({ updatedAt: -1 })
          .skip(skip)
          .limit(limit)
          .toArray(),
        this.dashboards.countDocuments(filter),
      ]);

      res.json({
        dashboards: dashboards.map((d) => ({
          id: d.id,
          name: d.name,
          description: d.description,
          widgetCount: d.widgets.length,
          shared: d.shared,
          updatedAt: d.updatedAt,
          _links: {
            self: `/api/dashboards/${d.id}`,
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
   * POST /api/dashboards/:id/share - Share dashboard
   */
  private async shareDashboard(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;
      const { userIds } = req.body;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can share)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can share');
      }

      await this.dashboards.updateOne(
        { id },
        {
          $set: {
            shared: true,
            sharedWith: userIds || [],
            updatedAt: new Date(),
          },
        }
      );

      res.json({
        id: dashboard.id,
        shared: true,
        sharedWith: userIds || [],
        message: 'Dashboard shared successfully',
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * DELETE /api/dashboards/:id/share - Unshare dashboard
   */
  private async unshareDashboard(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can unshare)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can unshare');
      }

      await this.dashboards.updateOne(
        { id },
        {
          $set: {
            shared: false,
            sharedWith: [],
            updatedAt: new Date(),
          },
        }
      );

      res.json({
        id: dashboard.id,
        shared: false,
        message: 'Dashboard unshared successfully',
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * POST /api/dashboards/:id/widgets - Add widget
   */
  private async addWidget(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;
      const widgetData = req.body;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can modify)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can add widgets');
      }

      const widget: Widget = {
        id: uuidv4(),
        ...widgetData,
      };

      await this.dashboards.updateOne(
        { id },
        {
          $push: { widgets: widget } as any,
          $set: { updatedAt: new Date() },
        }
      );

      res.status(201).json(widget);
    } catch (error) {
      next(error);
    }
  }

  /**
   * PUT /api/dashboards/:id/widgets/:widgetId - Update widget
   */
  private async updateWidget(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id, widgetId } = req.params;
      const updates = req.body;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can modify)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can update widgets');
      }

      const widgetIndex = dashboard.widgets.findIndex((w) => w.id === widgetId);
      if (widgetIndex === -1) {
        throw this.createNotFoundError('Widget not found');
      }

      dashboard.widgets[widgetIndex] = {
        ...dashboard.widgets[widgetIndex],
        ...updates,
        id: widgetId,
      };

      await this.dashboards.updateOne(
        { id },
        {
          $set: {
            widgets: dashboard.widgets,
            updatedAt: new Date(),
          },
        }
      );

      res.json(dashboard.widgets[widgetIndex]);
    } catch (error) {
      next(error);
    }
  }

  /**
   * DELETE /api/dashboards/:id/widgets/:widgetId - Delete widget
   */
  private async deleteWidget(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id, widgetId } = req.params;

      const dashboard = await this.dashboards.findOne({ id });
      if (!dashboard) {
        throw this.createNotFoundError('Dashboard not found');
      }

      // Check authorization (only owner can modify)
      if (dashboard.userId !== req.user!.id) {
        throw this.createForbiddenError('Only dashboard owner can delete widgets');
      }

      await this.dashboards.updateOne(
        { id },
        {
          $pull: { widgets: { id: widgetId } } as any,
          $set: { updatedAt: new Date() },
        }
      );

      res.status(204).send();
    } catch (error) {
      next(error);
    }
  }

  /**
   * Check if user can access dashboard
   */
  private canAccessDashboard(dashboard: Dashboard, userId: string): boolean {
    return (
      dashboard.userId === userId ||
      (dashboard.shared && dashboard.sharedWith?.includes(userId))
    );
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
