import os
import uuid
from datetime import timedelta

from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TeamMetric(Base):
    __tablename__ = "team_metric"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(String, index=False, nullable=False)
    sprint_id = Column(Integer, index=False, nullable=False)
    started_on = Column(DateTime, nullable=False)
    ended_on = Column(DateTime, nullable=False)
    source = Column(String, index=False, nullable=False)
    cycle_time = Column(String, index=False, nullable=False)
    process_cycle_efficiency = Column(Float, index=False, nullable=False)
    num_completed = Column(Integer, index=False, nullable=False)
    num_incomplete = Column(Integer, index=False, nullable=False)

    def serialize(self):
        return {
            'id': str(self.id),
            'project_id': self.project_id,
            'sprint_id': self.sprint_id,
            'started_on': str(self.started_on),
            'ended_on': str(self.ended_on),
            'source': self.source,
            'cycle_time': self.cycle_time,
            'process_cycle_efficiency': self.process_cycle_efficiency,
            'num_completed': self.num_completed,
            'num_incomplete': self.num_incomplete
        }