from sqlalchemy import and_

from app import db
from app.models import GitMetric


def dao_get_git_metrics():
    return db.Session().query(GitMetric).all()


def dao_get_git_metrics_between_daterange(team_id, start_date, end_date):
    return db.Session().query(GitMetric).filter(
        and_(
            GitMetric.team_id == team_id,
            GitMetric.end_date >= start_date,
            GitMetric.end_date <= end_date,
        )
    ).order_by(GitMetric.end_date).all()


def dao_upsert_git_metric(metric):
    db_metric = db.Session().query(GitMetric).filter_by(
        team_id=metric["team_id"],
        name=metric["name"],
        pr_number=metric["pr_number"]).first()

    if db_metric:
        db.update(
            GitMetric,
            filters={'team_id': metric["team_id"], 'name': metric["name"], 'pr_number': metric["pr_number"]},
            **metric
        )
    else:
        db.save(GitMetric(**metric))
