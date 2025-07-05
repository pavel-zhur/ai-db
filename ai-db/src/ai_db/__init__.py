"""AI-DB: An AI-native database engine."""

from ai_db.api import AIDB
from ai_db.core.models import PermissionLevel, QueryResult, DataLossIndicator

__version__ = "0.1.0"
__all__ = ["AIDB", "PermissionLevel", "QueryResult", "DataLossIndicator"]