from datetime import datetime

from sqlalchemy import Column, String, DateTime, Float, Integer, UniqueConstraint
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import create_engine

Base = declarative_base()
_ENGINE_CACHE: dict[str, Engine] = {}
_SESSION_CACHE: dict[str, sessionmaker] = {}

class CDMRecord(Base):
    """
    SQLAlchemy model for Conjunction Data Messages (CDMs).
    Addresses the requirement for a central data repository.
    """
    __tablename__ = 'cdm_records'
    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, unique=True, nullable=False)
    creation_date = Column(DateTime, nullable=False, index=True)
    tca = Column(DateTime, nullable=False, index=True)
    sat1_id = Column(String, nullable=False, index=True)
    sat2_id = Column(String, nullable=False)
    constellation = Column(String, index=True)
    miss_distance = Column(Float, nullable=False)
    event_id = Column(String, nullable=False, index=True)
    ingested_at = Column(DateTime, nullable=False, index=True, default=datetime.utcnow)
    raw_json = Column(JSONB, nullable=False)
    __table_args__ = (
        UniqueConstraint('message_id', name='_message_id_uc'),
    )

    def __repr__(self):
        return f"<CDMRecord(id={self.message_id}, sat1={self.sat1_id}, tca={self.tca})>"

def _get_engine(db_url: str) -> Engine:
    engine = _ENGINE_CACHE.get(db_url)
    if engine is None:
        engine = create_engine(db_url, pool_pre_ping=True)
        _ENGINE_CACHE[db_url] = engine
    return engine


def get_db_session(db_url):
    """Returns a cached session factory for the configured database."""
    Session = _SESSION_CACHE.get(db_url)
    if Session is None:
        Session = sessionmaker(bind=_get_engine(db_url))
        _SESSION_CACHE[db_url] = Session
    return Session


def create_schema(db_url):
    """Creates all configured database tables and returns the engine."""
    engine = _get_engine(db_url)
    Base.metadata.create_all(engine)
    return engine
