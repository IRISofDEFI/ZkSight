/**
 * Distributed tracing configuration using OpenTelemetry.
 * 
 * This module provides instrumentation for tracing requests across services
 * and external dependencies.
 */
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-grpc';
import { BatchSpanProcessor, ConsoleSpanExporter } from '@opentelemetry/sdk-trace-base';
import { trace, context, Span, SpanStatusCode, SpanKind } from '@opentelemetry/api';
import { W3CTraceContextPropagator } from '@opentelemetry/core';

let sdk: NodeSDK | null = null;
let tracer: ReturnType<typeof trace.getTracer> | null = null;

/**
 * Initialize OpenTelemetry tracing
 */
export function setupTracing(
  serviceName: string = 'chimera-api',
  serviceVersion: string = '1.0.0',
  jaegerEndpoint?: string,
  enableConsoleExport: boolean = false,
): void {
  const resource = Resource.default().merge(
    new Resource({
      [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
      [SemanticResourceAttributes.SERVICE_VERSION]: serviceVersion,
    }),
  );

  const traceExporter = jaegerEndpoint || process.env.OTEL_EXPORTER_OTLP_ENDPOINT
    ? new OTLPTraceExporter({
        url: jaegerEndpoint || process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
      })
    : undefined;

  const spanProcessors = [];
  
  if (traceExporter) {
    spanProcessors.push(new BatchSpanProcessor(traceExporter));
  }
  
  if (enableConsoleExport) {
    spanProcessors.push(new BatchSpanProcessor(new ConsoleSpanExporter()));
  }

  sdk = new NodeSDK({
    resource,
    spanProcessor: spanProcessors.length > 0 ? spanProcessors[0] : undefined,
    instrumentations: [
      getNodeAutoInstrumentations({
        '@opentelemetry/instrumentation-fs': {
          enabled: false, // Disable fs instrumentation to reduce noise
        },
      }),
    ],
    textMapPropagator: new W3CTraceContextPropagator(),
  });

  sdk.start();
  tracer = trace.getTracer(serviceName, serviceVersion);
}

/**
 * Shutdown tracing gracefully
 */
export async function shutdownTracing(): Promise<void> {
  if (sdk) {
    await sdk.shutdown();
  }
}

/**
 * Get the tracer instance
 */
export function getTracer(): ReturnType<typeof trace.getTracer> {
  if (!tracer) {
    throw new Error('Tracing not initialized. Call setupTracing() first.');
  }
  return tracer;
}

/**
 * Create a new span
 */
export function createSpan(
  name: string,
  attributes?: Record<string, string | number | boolean>,
  kind: SpanKind = SpanKind.INTERNAL,
): Span {
  const currentTracer = getTracer();
  const span = currentTracer.startSpan(name, {
    kind,
    attributes,
  });
  return span;
}

/**
 * Decorator to trace a function
 */
export function traceFunction(
  name?: string,
  attributes?: Record<string, string | number | boolean>,
) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor,
  ) {
    const originalMethod = descriptor.value;
    const spanName = name || `${target.constructor.name}.${propertyKey}`;

    descriptor.value = async function (...args: any[]) {
      const currentTracer = getTracer();
      return currentTracer.startActiveSpan(spanName, async (span) => {
        try {
          if (attributes) {
            Object.entries(attributes).forEach(([key, value]) => {
              span.setAttribute(key, value);
            });
          }

          span.setAttribute('function.name', propertyKey);
          span.setAttribute('function.class', target.constructor.name);

          const result = await originalMethod.apply(this, args);
          span.setStatus({ code: SpanStatusCode.OK });
          return result;
        } catch (error) {
          span.setStatus({
            code: SpanStatusCode.ERROR,
            message: error instanceof Error ? error.message : String(error),
          });
          span.recordException(error as Error);
          throw error;
        } finally {
          span.end();
        }
      });
    };

    return descriptor;
  };
}

/**
 * Trace an async function
 */
export async function traceAsync<T>(
  name: string,
  fn: (span: Span) => Promise<T>,
  attributes?: Record<string, string | number | boolean>,
  kind: SpanKind = SpanKind.INTERNAL,
): Promise<T> {
  const currentTracer = getTracer();
  return currentTracer.startActiveSpan(
    name,
    { kind, attributes },
    async (span) => {
      try {
        const result = await fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : String(error),
        });
        span.recordException(error as Error);
        throw error;
      } finally {
        span.end();
      }
    },
  );
}

/**
 * Trace a synchronous function
 */
export function traceSync<T>(
  name: string,
  fn: (span: Span) => T,
  attributes?: Record<string, string | number | boolean>,
  kind: SpanKind = SpanKind.INTERNAL,
): T {
  const currentTracer = getTracer();
  return currentTracer.startActiveSpan(
    name,
    { kind, attributes },
    (span) => {
      try {
        const result = fn(span);
        span.setStatus({ code: SpanStatusCode.OK });
        return result;
      } catch (error) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error instanceof Error ? error.message : String(error),
        });
        span.recordException(error as Error);
        throw error;
      } finally {
        span.end();
      }
    },
  );
}

/**
 * Inject trace context into carrier (e.g., HTTP headers)
 */
export function injectTraceContext(carrier: Record<string, string>): void {
  const propagator = new W3CTraceContextPropagator();
  propagator.inject(context.active(), carrier, {
    set: (carrier, key, value) => {
      carrier[key] = value;
    },
  });
}

/**
 * Extract trace context from carrier
 */
export function extractTraceContext(carrier: Record<string, string>): void {
  const propagator = new W3CTraceContextPropagator();
  const extractedContext = propagator.extract(context.active(), carrier, {
    get: (carrier, key) => carrier[key],
    keys: (carrier) => Object.keys(carrier),
  });
  context.with(extractedContext, () => {});
}

/**
 * Add event to current span
 */
export function addSpanEvent(
  name: string,
  attributes?: Record<string, string | number | boolean>,
): void {
  const span = trace.getActiveSpan();
  if (span) {
    span.addEvent(name, attributes);
  }
}

/**
 * Set attribute on current span
 */
export function setSpanAttribute(
  key: string,
  value: string | number | boolean,
): void {
  const span = trace.getActiveSpan();
  if (span) {
    span.setAttribute(key, value);
  }
}

/**
 * Mark current span as error
 */
export function setSpanError(error: Error): void {
  const span = trace.getActiveSpan();
  if (span) {
    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: error.message,
    });
    span.recordException(error);
  }
}

/**
 * Helper functions for common tracing patterns
 */

export function traceHttpRequest(
  method: string,
  path: string,
  statusCode?: number,
): Span {
  return createSpan(
    `HTTP ${method} ${path}`,
    {
      'http.method': method,
      'http.route': path,
      ...(statusCode && { 'http.status_code': statusCode }),
    },
    SpanKind.SERVER,
  );
}

export function traceMessageProcessing(
  messageType: string,
  correlationId: string,
): Span {
  return createSpan(
    `message.process.${messageType}`,
    {
      'message.type': messageType,
      'correlation.id': correlationId,
    },
    SpanKind.CONSUMER,
  );
}

export function traceExternalCall(
  service: string,
  operation: string,
): Span {
  return createSpan(
    `external.${service}.${operation}`,
    {
      'service.name': service,
      'operation': operation,
    },
    SpanKind.CLIENT,
  );
}

export function traceDatabaseOperation(
  database: string,
  operation: string,
  collection?: string,
): Span {
  const attributes: Record<string, string> = {
    'db.system': database,
    'db.operation': operation,
  };

  if (collection) {
    attributes['db.collection'] = collection;
  }

  return createSpan(
    `db.${database}.${operation}`,
    attributes,
    SpanKind.CLIENT,
  );
}

/**
 * Middleware to trace HTTP requests
 */
export function tracingMiddleware() {
  return (req: any, res: any, next: any) => {
    const currentTracer = getTracer();
    const span = currentTracer.startSpan(`HTTP ${req.method} ${req.route?.path || req.path}`, {
      kind: SpanKind.SERVER,
      attributes: {
        'http.method': req.method,
        'http.url': req.url,
        'http.route': req.route?.path || req.path,
        'correlation.id': req.correlationId,
      },
    });

    // Store span in request for later access
    req.span = span;

    res.on('finish', () => {
      span.setAttribute('http.status_code', res.statusCode);
      if (res.statusCode >= 400) {
        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: `HTTP ${res.statusCode}`,
        });
      } else {
        span.setStatus({ code: SpanStatusCode.OK });
      }
      span.end();
    });

    next();
  };
}
