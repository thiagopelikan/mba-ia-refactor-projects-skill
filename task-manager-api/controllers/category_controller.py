"""Controller de categorias: validação → model → resposta (RP-03/RP-05)."""
import logging

from database import db
from middlewares.error_handler import NotFoundError, ValidationError
from models.category import Category
from utils.helpers import validate_category_payload

logger = logging.getLogger(__name__)


def _get_category_or_404(category_id):
    category = Category.get_by_id(category_id)
    if not category:
        raise NotFoundError('Categoria não encontrada')
    return category


def list_categories():
    result = []
    for category, task_count in Category.with_task_counts():
        data = category.to_dict()
        data['task_count'] = task_count
        result.append(data)
    return result, 200


def create_category(data):
    fields, error = validate_category_payload(data)
    if error:
        raise ValidationError(error)

    category = Category(**fields)
    db.session.add(category)
    db.session.commit()
    logger.info('Categoria criada: %s - %s', category.id, category.name)
    return category.to_dict(), 201


def update_category(category_id, data):
    category = _get_category_or_404(category_id)
    # Antes: data['name'] sem checar get_json() None → TypeError → 500 (AP-13).
    fields, error = validate_category_payload(data, partial=True)
    if error:
        raise ValidationError(error)

    for field, value in fields.items():
        setattr(category, field, value)
    db.session.commit()
    return category.to_dict(), 200


def delete_category(category_id):
    category = _get_category_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    logger.info('Categoria deletada: %s', category_id)
    return {'message': 'Categoria deletada'}, 200
