"""Controller de usuários: validação → model → resposta (RP-03/RP-05)."""
import logging

from sqlalchemy import delete

from database import db
from middlewares.error_handler import ConflictError, NotFoundError, ValidationError
from models.task import Task
from models.user import User
from utils.helpers import validate_user_payload

logger = logging.getLogger(__name__)


def _get_user_or_404(user_id):
    user = User.get_by_id(user_id)
    if not user:
        raise NotFoundError('Usuário não encontrado')
    return user


def list_users():
    result = []
    for user, task_count in User.with_task_counts():
        data = user.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result, 200


def get_user(user_id):
    user = _get_user_or_404(user_id)
    data = user.to_dict()
    data['tasks'] = [task.to_dict() for task in Task.for_user(user_id)]
    return data, 200


def create_user(data):
    fields, error = validate_user_payload(data)
    if error:
        raise ValidationError(error)
    if User.get_by_email(fields['email']):
        raise ConflictError('Email já cadastrado')

    user = User(name=fields['name'], email=fields['email'], role=fields['role'])
    user.set_password(fields['password'])
    db.session.add(user)
    db.session.commit()
    logger.info('Usuário criado: %s - %s', user.id, user.name)
    return user.to_dict(), 201


def update_user(user_id, data):
    user = _get_user_or_404(user_id)
    fields, error = validate_user_payload(data, partial=True)
    if error:
        raise ValidationError(error)

    if 'email' in fields:
        existing = User.get_by_email(fields['email'])
        if existing and existing.id != user_id:
            raise ConflictError('Email já cadastrado')

    password = fields.pop('password', None)
    for field, value in fields.items():
        setattr(user, field, value)
    if password:
        user.set_password(password)

    db.session.commit()
    return user.to_dict(), 200


def delete_user(user_id):
    user = _get_user_or_404(user_id)
    # Escrita atômica (RP-07): tasks do usuário + usuário em uma única transação.
    db.session.execute(delete(Task).where(Task.user_id == user_id))
    db.session.delete(user)
    db.session.commit()
    logger.info('Usuário deletado: %s', user_id)
    return {'message': 'Usuário deletado com sucesso'}, 200


def get_user_tasks(user_id):
    _get_user_or_404(user_id)
    return [task.to_brief_dict() for task in Task.for_user(user_id)], 200
