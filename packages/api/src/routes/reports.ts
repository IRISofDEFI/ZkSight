/**
 * Report retrieval and export endpoints
 */
import { Router, Request, Response, NextFunction } from 'express';
import { AuthMiddleware } from '../auth';
import { ApiError } from '../middleware/errorHandler';
import { MongoClient, Db, Collection } from 'mongodb';

export interface Report {
  reportId: string;
  queryId: string;
  userId?: string;
  title: string;
  executiveSummary: string;
  sections: ReportSection[];
  visualizations: string[];
  metadata: ReportMetadata;
  createdAt: Date;
  expiresAt?: Date;
}

export interface ReportSection {
  title: string;
  content: string;
  order: number;
}

export interface ReportMetadata {
  analysisTypes: string[];
  dataSourcesUsed: string[];
  executionTime: number;
  confidence: number;
}

export class ReportRoutes {
  private router: Router;
  private authMiddleware: AuthMiddleware;
  private db: Db;
  private reports: Collection<Report>;

  constructor(
    authMiddleware: AuthMiddleware,
    mongoClient: MongoClient,
    dbName: string
  ) {
    this.router = Router();
    this.authMiddleware = authMiddleware;
    this.db = mongoClient.db(dbName);
    this.reports = this.db.collection<Report>('reports');
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // Get report by ID
    this.router.get(
      '/:id',
      this.authMiddleware.authenticate,
      this.getReport.bind(this)
    );

    // List reports
    this.router.get(
      '/',
      this.authMiddleware.authenticate,
      this.listReports.bind(this)
    );

    // Export report as PDF
    this.router.get(
      '/:id/export/pdf',
      this.authMiddleware.authenticate,
      this.exportPdf.bind(this)
    );

    // Export report as HTML
    this.router.get(
      '/:id/export/html',
      this.authMiddleware.authenticate,
      this.exportHtml.bind(this)
    );

    // Export report as JSON
    this.router.get(
      '/:id/export/json',
      this.authMiddleware.authenticate,
      this.exportJson.bind(this)
    );
  }

  /**
   * GET /api/reports/:id - Get report by ID
   */
  private async getReport(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const report = await this.reports.findOne({ reportId: id });
      if (!report) {
        throw this.createNotFoundError('Report not found');
      }

      // Check authorization
      if (report.userId && report.userId !== req.user?.id) {
        throw this.createForbiddenError('Access denied');
      }

      res.json({
        reportId: report.reportId,
        queryId: report.queryId,
        title: report.title,
        executiveSummary: report.executiveSummary,
        sections: report.sections,
        visualizations: report.visualizations,
        metadata: report.metadata,
        createdAt: report.createdAt,
        _links: {
          self: `/api/reports/${report.reportId}`,
          query: `/api/queries/${report.queryId}`,
          exports: {
            pdf: `/api/reports/${report.reportId}/export/pdf`,
            html: `/api/reports/${report.reportId}/export/html`,
            json: `/api/reports/${report.reportId}/export/json`,
          },
        },
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/reports - List reports with pagination
   */
  private async listReports(
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

      // Filter by query ID if provided
      if (req.query.queryId) {
        filter.queryId = req.query.queryId;
      }

      const [reports, total] = await Promise.all([
        this.reports
          .find(filter)
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(limit)
          .toArray(),
        this.reports.countDocuments(filter),
      ]);

      res.json({
        reports: reports.map((r) => ({
          reportId: r.reportId,
          queryId: r.queryId,
          title: r.title,
          executiveSummary: r.executiveSummary,
          createdAt: r.createdAt,
          _links: {
            self: `/api/reports/${r.reportId}`,
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
   * GET /api/reports/:id/export/pdf - Export report as PDF
   */
  private async exportPdf(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const report = await this.reports.findOne({ reportId: id });
      if (!report) {
        throw this.createNotFoundError('Report not found');
      }

      // Check authorization
      if (report.userId && report.userId !== req.user?.id) {
        throw this.createForbiddenError('Access denied');
      }

      // TODO: Implement PDF generation using Puppeteer
      // For now, return a placeholder response
      res.status(501).json({
        error: {
          code: 'NOT_IMPLEMENTED',
          message: 'PDF export not yet implemented',
          retryable: false,
        },
        requestId: req.correlationId,
        timestamp: Date.now(),
      });
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/reports/:id/export/html - Export report as HTML
   */
  private async exportHtml(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const report = await this.reports.findOne({ reportId: id });
      if (!report) {
        throw this.createNotFoundError('Report not found');
      }

      // Check authorization
      if (report.userId && report.userId !== req.user?.id) {
        throw this.createForbiddenError('Access denied');
      }

      // Generate HTML
      const html = this.generateHtml(report);

      res.setHeader('Content-Type', 'text/html');
      res.setHeader(
        'Content-Disposition',
        `attachment; filename="report-${report.reportId}.html"`
      );
      res.send(html);
    } catch (error) {
      next(error);
    }
  }

  /**
   * GET /api/reports/:id/export/json - Export report as JSON
   */
  private async exportJson(
    req: Request,
    res: Response,
    next: NextFunction
  ): Promise<void> {
    try {
      const { id } = req.params;

      const report = await this.reports.findOne({ reportId: id });
      if (!report) {
        throw this.createNotFoundError('Report not found');
      }

      // Check authorization
      if (report.userId && report.userId !== req.user?.id) {
        throw this.createForbiddenError('Access denied');
      }

      res.setHeader('Content-Type', 'application/json');
      res.setHeader(
        'Content-Disposition',
        `attachment; filename="report-${report.reportId}.json"`
      );
      res.json(report);
    } catch (error) {
      next(error);
    }
  }

  /**
   * Generate HTML from report
   */
  private generateHtml(report: Report): string {
    const sectionsHtml = report.sections
      .sort((a, b) => a.order - b.order)
      .map(
        (section) => `
        <section>
          <h2>${this.escapeHtml(section.title)}</h2>
          <div>${this.escapeHtml(section.content)}</div>
        </section>
      `
      )
      .join('');

    return `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>${this.escapeHtml(report.title)}</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
          }
          h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
          h2 { color: #34495e; margin-top: 30px; }
          .summary { background: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }
          .metadata { font-size: 0.9em; color: #7f8c8d; margin-top: 30px; }
          section { margin: 20px 0; }
        </style>
      </head>
      <body>
        <h1>${this.escapeHtml(report.title)}</h1>
        <div class="summary">
          <strong>Executive Summary:</strong>
          <p>${this.escapeHtml(report.executiveSummary)}</p>
        </div>
        ${sectionsHtml}
        <div class="metadata">
          <p><strong>Report ID:</strong> ${report.reportId}</p>
          <p><strong>Generated:</strong> ${report.createdAt.toISOString()}</p>
          <p><strong>Data Sources:</strong> ${report.metadata.dataSourcesUsed.join(', ')}</p>
        </div>
      </body>
      </html>
    `;
  }

  /**
   * Escape HTML special characters
   */
  private escapeHtml(text: string): string {
    const map: Record<string, string> = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (m) => map[m]);
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
