import os
import uuid
from datetime import timedelta

from sqlalchemy import Column, Float, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class TeamMetric(Base):
    __tablename__ = "team_metric"

    project_id = Column(String, index=False, nullable=False, primary_key=True)
    sprint_id = Column(String, index=False, nullable=False, primary_key=True)
    started_on = Column(DateTime, nullable=False)
    ended_on = Column(DateTime, nullable=False)
    source = Column(String, index=False, nullable=False)
    avg_cycle_time = Column(Integer, index=False, nullable=False)
    process_cycle_efficiency = Column(Float, index=False, nullable=False)
    num_completed = Column(Integer, index=False, nullable=False)
    num_incomplete = Column(Integer, index=False, nullable=False)

    def serialize(self):
        return {
            'project_id': self.project_id,
            'sprint_id': self.sprint_id,
            'started_on': str(self.started_on),
            'ended_on': str(self.ended_on),
            'source': self.source,
            'avg_cycle_time': str(timedelta(seconds=int(self.avg_cycle_time))),
            'process_cycle_efficiency': self.process_cycle_efficiency,
            'num_completed': self.num_completed,
            'num_incomplete': self.num_incomplete
        }


class GitMetric(Base):
    __tablename__ = "git_metric"

    team_id = Column(String, index=False, nullable=False, primary_key=True)
    name = Column(String, index=False, nullable=False, primary_key=True)
    pr_number = Column(Integer, index=False, nullable=False, primary_key=True)
    start_date = Column(DateTime, index=False, nullable=False, primary_key=False)
    end_date = Column(DateTime, index=False, nullable=False, primary_key=False)
    diff_count = Column(Integer, index=False, nullable=False, primary_key=False)
    total_diff_count = Column(Integer, index=False, nullable=False, primary_key=False)
    comments_count = Column(Integer, index=False, nullable=True, primary_key=False)

    def serialize(self):
        return {
            'team_id': self.team_id,
            'name': self.name,
            'pr_number': self.pr_number,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'diff_count': self.diff_count,
            'total_diff_count': self.total_diff_count,
            'comments_count': self.comments_count,
        }
