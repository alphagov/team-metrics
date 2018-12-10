from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import SQLALCHEMY_DATABASE_URI


class Metrics_DB:
    Session = None

    def init(self):
        engine = create_engine(SQLALCHEMY_DATABASE_URI)
        self.Session = sessionmaker(bind=engine)

    def save(self, obj):
        session = self.Session()

        try:
            session.add(obj)
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
