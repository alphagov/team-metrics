from sqlalchemy import and_

from app import db
from app.models import TeamMetric


def dao_get_sprints():
    return db.Session().query(TeamMetric).all()


def dao_get_sprints_started_from(_project_id, _started_on):
    return db.Session().query(TeamMetric).filter(and_(
            TeamMetric.project_id == _project_id,
            TeamMetric.started_on >= _started_on
        )).all()


def dao_add_sprint(metric):
    metric_exists = db.Session().query(TeamMetric).filter_by(
        project_id=metric.project_id,
        sprint_id=str(metric.sprint_id)).first()

    if metric_exists:
        return

    db.save(TeamMetric(**metric.__dict__))


def dao_upsert_sprint(metric):
    db_metric = db.Session().query(TeamMetric).filter_by(
        project_id=metric.project_id,
        sprint_id=str(metric.sprint_id)).first()

    if db_metric:
        db.update(
            TeamMetric,
            filters={'project_id': metric.project_id, 'sprint_id': metric.sprint_id},
            **metric.__dict__
        )
    else:
        db.save(TeamMetric(**metric.__dict__))
