import os
import uuid

from sqlalchemy import create_engine, Column, Float, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base


from team_metrics import DeclarativeBase


class TeamMetric(DeclarativeBase):
    __tablename__ = "team_metric"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String, index=False, unique=True, nullable=False)
    sprint_id = Column(String, index=False, unique=True, nullable=False)
    started_on = Column(DateTime, nullable=False)
    ended_on = Column(DateTime, nullable=False)
    source = Column(String, index=False, unique=True, nullable=False)
    cycle_time = Column(String, index=False, unique=True, nullable=False)
    process_cycle_efficiency = Column(Float, index=False, unique=True, nullable=False)
    num_completed = Column(Integer, index=False, unique=True, nullable=False)
    num_incomplete = Column(Integer, index=False, unique=True, nullable=False)
