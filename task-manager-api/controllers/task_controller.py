"""Controller de tasks: validação → model → resposta (RP-03/RP-05).

Handlers de rota delegam para cá; erros são levantados como exceções
tipadas e convertidos pelo error handler central (RP-08).
"""
import logging

from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import STATUS_DONE, calculate_percentage, validate_task_payload

logger = logging.getLogger(__name__)


def _get_task_or_404(task_id):
    task = Task.get_by_id(task_id)
    if not task:
        raise NotFoundError('Task não encontrada')
    return task


def _ensure_related_exist(fields):
    """Preserva o contrato: user/category inexistentes em POST/PUT → 404."""
    if fields.get('user_id') and not User.get_by_id(fields['user_id']):
        raise NotFoundError('Usuário não encontrado')
    if fields.get('category_id') and not Category.get_by_id(fields['category_id']):
        raise NotFoundError('Categoria não encontrada')


def list_tasks():
    result = []
    for task in Task.list_with_relations():
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        data['user_name'] = task.user.name if task.user else None
        data['category_name'] = task.category.name if task.category else None
        result.append(data)
    return result, 200


def get_task(task_id):
    task = _get_task_or_404(task_id)
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data, 200


def create_task(data):
    fields, error = validate_task_payload(data)
    if error:
        raise ValidationError(error)
    _ensure_related_exist(fields)

    task = Task(**fields)
    db.session.add(task)
    db.session.commit()
    logger.info('Task criada: %s - %s', task.id, task.title)
    return task.to_dict(), 201


def update_task(task_id, data):
    task = _get_task_or_404(task_id)
    fields, error = validate_task_payload(data, partial=True)
    if error:
        raise ValidationError(error)
    _ensure_related_exist(fields)

    for field, value in fields.items():
        setattr(task, field, value)
    db.session.commit()
    logger.info('Task atualizada: %s', task.id)
    return task.to_dict(), 200


def delete_task(task_id):
    task = _get_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    logger.info('Task deletada: %s', task_id)
    return {'message': 'Task deletada com sucesso'}, 200


def search_tasks(args):
    text = args.get('q', '')
    status = args.get('status', '')
    priority_raw = args.get('priority', '')
    user_id_raw = args.get('user_id', '')

    priority = None
    if priority_raw:
        try:
            priority = int(priority_raw)
        except ValueError:
            raise ValidationError("Parâmetro 'priority' deve ser um número inteiro")

    user_id = None
    if user_id_raw:
        try:
            user_id = int(user_id_raw)
        except ValueError:
            raise ValidationError("Parâmetro 'user_id' deve ser um número inteiro")

    tasks = Task.search(
        text=text or None, status=status or None, priority=priority, user_id=user_id
    )
    return [task.to_dict() for task in tasks], 200


def get_stats():
    counts = Task.counts_by_status()
    total = sum(counts.values())
    stats = {
        'total': total,
        'pending': counts['pending'],
        'in_progress': counts['in_progress'],
        'done': counts[STATUS_DONE],
        'cancelled': counts['cancelled'],
        'overdue': len(Task.overdue_tasks()),
        'completion_rate': calculate_percentage(counts[STATUS_DONE], total),
    }
    return stats, 200
