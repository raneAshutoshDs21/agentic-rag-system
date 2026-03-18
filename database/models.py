"""
SQLAlchemy ORM models for the agentic RAG system.
Defines all database table structures.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    Text,
    DateTime,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from core.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

Base = declarative_base()


class QueryHistory(Base):
    """Stores all user queries and their answers."""

    __tablename__ = "query_history"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    query      = Column(Text, nullable=False)
    answer     = Column(Text, nullable=False)
    route      = Column(String(50))
    score      = Column(Float, default=0.0)
    success    = Column(Boolean, default=True)
    timestamp  = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<QueryHistory id={self.id} "
            f"session={self.session_id} "
            f"score={self.score}>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id"        : self.id,
            "session_id": self.session_id,
            "query"     : self.query,
            "answer"    : self.answer,
            "route"     : self.route,
            "score"     : self.score,
            "success"   : self.success,
            "timestamp" : str(self.timestamp)
        }


class ToolResult(Base):
    """Stores tool execution results."""

    __tablename__ = "tool_results"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    tool_name  = Column(String(50), nullable=False, index=True)
    query      = Column(Text, nullable=False)
    result     = Column(Text, nullable=False)
    success    = Column(Boolean, default=True)
    extra_info = Column(Text)
    timestamp  = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<ToolResult id={self.id} "
            f"tool={self.tool_name} "
            f"success={self.success}>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id"        : self.id,
            "tool_name" : self.tool_name,
            "query"     : self.query,
            "result"    : self.result,
            "success"   : self.success,
            "extra_info": self.extra_info,
            "timestamp" : str(self.timestamp)
        }


class ShortTermMemoryRecord(Base):
    """Stores short-term conversation memory."""

    __tablename__ = "short_term_memory"

    id        = Column(Integer, primary_key=True, autoincrement=True)
    session   = Column(String(100), nullable=False, index=True)
    role      = Column(String(20), nullable=False)
    content   = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<ShortTermMemory id={self.id} "
            f"session={self.session} "
            f"role={self.role}>"
        )


class LongTermMemoryRecord(Base):
    """Stores long-term persistent facts."""

    __tablename__ = "long_term_memory"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    key        = Column(String(200), unique=True, nullable=False)
    value      = Column(Text, nullable=False)
    category   = Column(String(50), default="general")
    extra_info = Column(Text)
    timestamp  = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return (
            f"<LongTermMemory id={self.id} "
            f"key={self.key} "
            f"category={self.category}>"
        )


class ResponseCacheRecord(Base):
    """Stores cached responses."""

    __tablename__ = "response_cache"

    cache_key  = Column(String(32), primary_key=True)
    query      = Column(Text, nullable=False)
    response   = Column(Text, nullable=False)
    score      = Column(Float, default=0.0)
    hit_count  = Column(Integer, default=0)
    created_at = Column(Float, nullable=False)
    last_hit   = Column(Float)

    def __repr__(self):
        return (
            f"<ResponseCache key={self.cache_key[:8]} "
            f"hits={self.hit_count}>"
        )


def get_engine(db_path: str = None):
    """
    Create SQLAlchemy engine.

    Args:
        db_path: Optional database path override

    Returns:
        SQLAlchemy engine instance
    """
    path = db_path or settings.sqlite_db_path
    return create_engine(
        f"sqlite:///{path}",
        echo         = False,
        connect_args = {"check_same_thread": False}
    )


def init_db(db_path: str = None):
    """
    Initialize database and create all tables.

    Args:
        db_path: Optional database path override

    Returns:
        SQLAlchemy session factory
    """
    engine  = get_engine(db_path)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    logger.info(
        f"Database initialized | "
        f"path={db_path or settings.sqlite_db_path}"
    )
    return Session