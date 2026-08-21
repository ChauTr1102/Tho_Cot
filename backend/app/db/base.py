# Import all the models, so that Base has them before being
# imported by Alembic or database initialization
from app.db.base_class import Base  # noqa
from app.models.item import Item  # noqa
from app.models.campaign import Campaign  # noqa
