"""MongoDB models for agents"""

from .user import UserProfile, UserPreferences, ApiKey
from .dashboard import Dashboard, Widget, WidgetConfig
from .report import ReportDocument, Report, AnalysisResponse
from .alert import AlertRule, AlertHistory, AlertCondition
from .query import QueryHistory, QueryIntent, ExtractedEntity

__all__ = [
    'UserProfile',
    'UserPreferences',
    'ApiKey',
    'Dashboard',
    'Widget',
    'WidgetConfig',
    'ReportDocument',
    'Report',
    'AnalysisResponse',
    'AlertRule',
    'AlertHistory',
    'AlertCondition',
    'QueryHistory',
    'QueryIntent',
    'ExtractedEntity',
]
