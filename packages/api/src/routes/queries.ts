/**
 * Query submission and management endpoints
 */
import { Router, Request, Response, NextFunction } from 'express';
import { v4 as uuidv4 } from 'uuid';
import { EventPublisher } from '../messaging';
import { AuthMiddleware } from '../auth';
import { ApiError } from '../middleware/errorHandler';
import { MongoClient, Db, Collection } from 'mongodb';

export interface QuerySubmission {
  query: string;
  userId?: string;
  sessionId?: string;
  context?: Record<string, any>;
}

export interface QueryRecord {
  queryId: string;
  userId?: string;
  sessionId: string;
  query: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  context?: Record<string, any>;
  result?: {
    reportId?: string;
    error?: string;
  };
  createdAt: Date;
  updatedAt: Date;
}

export class QueryRoutes {
  private router: Router;
  private publisher: EventPublisher;
  private authMiddleware: AuthMiddleware;
  private db: Db;
  private queries: Collection<QueryRecord>;

  constructor(
    publisher: EventPublisher,
    authMiddleware: AuthMiddleware,
    mongoClient: MongoClient,
    dbName: string
  ) {
    this.router = Router();
    this.publisher = publisher;
    this.authMiddleware = authMiddleware;
    this.db = mongoClient.db(dbName);
    this.queries = this.db.collection<QueryRecord>('queries');
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Submit new query
    this.router.post(
      '/',
      this.authMiddleware.authenticate,
      this.submitQuery.bind(this)
    );

    // Get query status
    this.router.get(
      '/:id',
      this.authMiddleware.authenticate,
      this.getQueryStatus.bind(this)
    );

    // Cancel query
    this.router.delete(
      '/:id',
      this.authMiddleware.authenticate,
      this.cancelQuery.bind(this)
    );

    // List user queries
    this.router.get(
      '/',
      this.authMiddleware.authenticate,
      this.listQueries.bind(this)
    );
  }

  /**
   * POST /api/queries - Submit new query
   */
  private async submitQuery(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { query, sessionId, context }: QuerySubmission = req.body;

      if (!query || typeof query !== 'string') {
        throw this.createValidationError('Query text is required');
      }

      // Create query record
      const queryId = uuidv4();
      const queryRecord: QueryRecord = {
        queryId,
        userId: req.user?.id,
        sessionId: sessionId || uuidv4(),
        query,
        status: 'pending',
        context,
        createdAt: new Date(),
        updatedAt: new Date(),
      };

      await this.queries.insertOne(queryRecord);

      // Publish query event to message bus
      await this.publisher.publish(
        {
          queryId,
          query,
          userId: req.user?.id,
          sessionId: queryRecord.sessionId,
          context,
        },
        'query.submitted',
        {
          correlationId: req.correlationId,
        }
      );

      res.status(202).json({
        queryId,
        status: 'pending',
        message: 'Query submitted successfully',
        _links: {
          self: `/api/queries/${queryId}`,
          cancel: `/api/queries/${queryId}`,
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/queries/:id - Get query status
   */
  private async getQueryStatus(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const query = await this.queries.findOne({ queryId: id });
      if (!query) {
        throw this.createNotFoundError('Query not found');
      }

      // Check authorization
      if (query.userId && query.userId !== req.user?.id) {
        throw this.createForbiddenError('Access denied');
      }

      res.json({
        queryId: query.queryId,
        status: query.status,
        query: query.query,
        result: query.result,
        createdAt: query.createdAt,
        updatedAt: query.updatedAt,
        _links: {
          self: `/api/queries/${query.queryId}`,
          cancel: query.status === 'pending' || query.status === 'processing'
            ? `/api/queries/${query.queryId}`
            : undefined,
          report: query.result?.reportId
            ? `/api/reports/${query.result.reportId}`
            : undefined,
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * DELETE /api/queries/:id - Cancel query
   */
  private async cancelQuery(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const query = await this.queries.findOne({ queryId: id });
      if (!query) {
        throw this.createNotFoundError('Query not found');
      }

      // Check authorization
      if (query.userId && query.userId !== req.user?.id) {
        throw this.createForbiddenError('Access denied');
      }

      // Check if cancellable
      if (query.status !== 'pending' && query.status !== 'processing') {
        throw this.createValidationError('Query cannot be cancelled');
      }

      // Update status
      await this.queries.updateOne(
        { queryId: id },
        {
          $set: {
            status: 'cancelled',
            updatedAt: new Date(),
          },
        }
      );

      // Publish cancellation event
      await this.publisher.publish(
        { queryId: id },
        'query.cancelled',
        { correlationId: req.correlationId }
      );

      res.json({
        queryId: id,
        status: 'cancelled',
        message: 'Query cancelled successfully',
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/queries - List user queries
   */
  private async listQueries(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const page = parseInt(req.query.page as string) || 1;
      const limit = Math.min(parseInt(req.query.limit as string) || 20, 100);
      const skip = (page - 1) * limit;

      const filter: any = {};
      if (req.user?.id) {
        filter.userId = req.user.id;
      }

      const [queries, total] = await Promise.all([
        this.queries
          .find(filter)
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(limit)
          .toArray(),
        this.queries.countDocuments(filter),
      ]);

      res.json({
        queries: queries.map((q) => ({
          queryId: q.queryId,
          query: q.query,
          status: q.status,
          createdAt: q.createdAt,
          _links: {
            self: `/api/queries/${q.queryId}`,
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
