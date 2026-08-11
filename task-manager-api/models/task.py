"""Model de Task: schema, regras de domínio e queries do domínio (estilo SQLAlchemy 2.x)."""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import selectinload

from database import db
from utils.helpers import (
    MAX_PRIORITY,
    MIN_PRIORITY,
    STATUS_DONE,
    TERMINAL_STATUSES,
    VALID_STATUSES,
    ensure_utc,
    format_datetime,
    now_utc,
)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=now_utc)
    updated_at = db.Column(db.DateTime, default=now_utc, onupdate=now_utc)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    # -- Serialização (única implementação; rotas não remontam dicts) --------
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at),
            'due_date': format_datetime(self.due_date),
            'tags': self.tags.split(',') if self.tags else [],
        }

    def to_brief_dict(self):
        """Shape reduzido do contrato de GET /users/<id>/tasks."""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'created_at': format_datetime(self.created_at),
            'due_date': format_datetime(self.due_date),
            'overdue': self.is_overdue(),
        }

    # -- Regras de domínio ---------------------------------------------------
    @staticmethod
    def validate_status(new_status):
        return new_status in VALID_STATUSES

    @staticmethod
    def validate_priority(priority):
        return MIN_PRIORITY <= priority <= MAX_PRIORITY

    def is_overdue(self):
        """Única implementação da regra de atraso (antes copiada 6x nas rotas)."""
        if not self.due_date or self.status in TERMINAL_STATUSES:
            return False
        return ensure_utc(self.due_date) < now_utc()

    def days_overdue(self):
        return (now_utc() - ensure_utc(self.due_date)).days

    # -- Queries do domínio --------------------------------------------------
    @classmethod
    def get_by_id(cls, task_id):
        return db.session.get(cls, task_id)

    @classmethod
    def list_with_relations(cls):
        """Todas as tasks com user/category em 3 queries fixas (RP-09, sem N+1)."""
        stmt = select(cls).options(selectinload(cls.user), selectinload(cls.category))
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def search(cls, text=None, status=None, priority=None, user_id=None):
        stmt = select(cls)
        if text:
            pattern = f'%{text}%'
            stmt = stmt.where(or_(cls.title.like(pattern), cls.description.like(pattern)))
        if status:
            stmt = stmt.where(cls.status == status)
        if priority is not None:
            stmt = stmt.where(cls.priority == priority)
        if user_id is not None:
            stmt = stmt.where(cls.user_id == user_id)
        return db.session.execute(stmt).scalars().all()

    @classmethod
    def for_user(cls, user_id):
        return db.session.execute(select(cls).where(cls.user_id == user_id)).scalars().all()

    @classmethod
    def counts_by_status(cls):
        """Contagem por status em UMA query (antes: 4-5 counts separados)."""
        rows = db.session.execute(select(cls.status, func.count()).group_by(cls.status)).all()
        counts = {status: 0 for status in VALID_STATUSES}
        for status, count in rows:
            counts[status] = count
        return counts

    @classmethod
    def counts_by_priority(cls):
        """Contagem por prioridade em UMA query (antes: 5 counts separados)."""
        rows = db.session.execute(select(cls.priority, func.count()).group_by(cls.priority)).all()
        counts = {priority: 0 for priority in range(MIN_PRIORITY, MAX_PRIORITY + 1)}
        for priority, count in rows:
            if priority in counts:
                counts[priority] = count
        return counts

    @classmethod
    def overdue_tasks(cls):
        """Tasks atrasadas: pré-filtro no SQL, decisão final tz-safe em is_overdue()."""
        stmt = select(cls).where(cls.due_date.is_not(None), cls.status.not_in(TERMINAL_STATUSES))
        return [task for task in db.session.execute(stmt).scalars() if task.is_overdue()]

    @classmethod
    def count_created_since(cls, moment):
        moment = ensure_utc(moment).replace(tzinfo=None)  # storage é naive-UTC
        stmt = select(func.count()).select_from(cls).where(cls.created_at >= moment)
        return db.session.execute(stmt).scalar_one()

    @classmethod
    def count_completed_since(cls, moment):
        moment = ensure_utc(moment).replace(tzinfo=None)
        stmt = (
            select(func.count())
            .select_from(cls)
            .where(cls.status == STATUS_DONE, cls.updated_at >= moment)
        )
        return db.session.execute(stmt).scalar_one()
