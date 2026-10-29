from app.db.base import Base
from app.db.session import engine
from app.models import Evidence, Investigation, ProductEvent, Release


def initialize_database() -> None:
    _ = (Evidence, Investigation, ProductEvent, Release)
    Base.metadata.create_all(bind=engine)
