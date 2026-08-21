from app.db.base import Base
from app.db.session import engine


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)
