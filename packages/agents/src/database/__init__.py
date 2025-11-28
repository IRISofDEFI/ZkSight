"""Database connection utilities"""

from .mongodb import (
    connect_mongodb,
    get_mongodb,
    close_mongodb,
    check_mongodb_health,
    initialize_collections,
)
from .influxdb import (
    initialize_influxdb,
    get_client,
    get_write_api,
    get_query_api,
    create_metric_point,
    write_metric,
    write_metrics_batch,
    close_influxdb,
    setup_influxdb_schema,
    check_influxdb_health,
    MetricType,
    DataSource,
    NetworkType,
)

__all__ = [
    'connect_mongodb',
    'get_mongodb',
    'close_mongodb',
    'check_mongodb_health',
    'initialize_collections',
    'initialize_influxdb',
    'get_client',
    'get_write_api',
    'get_query_api',
    'create_metric_point',
    'write_metric',
    'write_metrics_batch',
    'close_influxdb',
    'setup_influxdb_schema',
    'check_influxdb_health',
    'MetricType',
    'DataSource',
    'NetworkType',
]
