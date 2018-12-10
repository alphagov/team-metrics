from app import db
from app.models import TeamMetric


def dao_get_sprints():
    return db.Session().query(TeamMetric).all()


def dao_get_sprints_project(project_id):
    return db.Session().query(TeamMetric).filter_by(
        project_id=project_id
    ).all()


def dao_add_sprint(metric):
    metric_exists = db.Session().query(TeamMetric).filter_by(
        project_id=metric.project_id,
        sprint_id=str(metric.sprint_id)).first()

    if metric_exists:
        return

    db.save(TeamMetric(**metric.__dict__))
