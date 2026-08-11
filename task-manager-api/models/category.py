"""Model de Category: schema e queries do domínio."""
from sqlalchemy import func, select

from database import db
from models.task import Task
from utils.helpers import DEFAULT_COLOR, format_datetime, now_utc


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    color = db.Column(db.String(7), default=DEFAULT_COLOR)
    created_at = db.Column(db.DateTime, default=now_utc)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'created_at': format_datetime(self.created_at),
        }

    # -- Queries do domínio --------------------------------------------------
    @classmethod
    def get_by_id(cls, category_id):
        return db.session.get(cls, category_id)

    @classmethod
    def count_all(cls):
        return db.session.execute(select(func.count()).select_from(cls)).scalar_one()

    @classmethod
    def with_task_counts(cls):
        """Categorias + task_count em UMA query (RP-09; antes um COUNT por categoria)."""
        stmt = (
            select(cls, func.count(Task.id))
            .outerjoin(Task, Task.category_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()
