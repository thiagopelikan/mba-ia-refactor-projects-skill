"""Model de User: schema, hashing seguro de senha e queries do domínio."""
from sqlalchemy import case, func, select
from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from models.task import Task
from utils.helpers import STATUS_DONE, format_datetime, now_utc


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=now_utc)

    # -- Serialização segura (RP-04): NUNCA inclui senha/hash ----------------
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': format_datetime(self.created_at),
        }

    # -- Senha (RP-04): werkzeug com salt automático, no lugar de MD5 --------
    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password or '', pwd)

    def is_admin(self):
        return self.role == 'admin'

    # -- Queries do domínio --------------------------------------------------
    @classmethod
    def get_by_id(cls, user_id):
        return db.session.get(cls, user_id)

    @classmethod
    def get_by_email(cls, email):
        return db.session.execute(select(cls).where(cls.email == email)).scalar_one_or_none()

    @classmethod
    def count_all(cls):
        return db.session.execute(select(func.count()).select_from(cls)).scalar_one()

    @classmethod
    def with_task_counts(cls):
        """Usuários + task_count em UMA query (RP-09; antes lazy load por usuário)."""
        stmt = (
            select(cls, func.count(Task.id))
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()

    @classmethod
    def productivity_stats(cls):
        """(id, nome, total_tasks, completed_tasks) por usuário em UMA query."""
        completed = func.count(case((Task.status == STATUS_DONE, 1)))
        stmt = (
            select(cls.id, cls.name, func.count(Task.id), completed)
            .outerjoin(Task, Task.user_id == cls.id)
            .group_by(cls.id, cls.name)
            .order_by(cls.id)
        )
        return db.session.execute(stmt).all()
