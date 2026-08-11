"""Popula o banco com dados iniciais.

- RP-07: todas as escritas (limpeza + usuários + categorias + tasks) em UMA
  transação, com rollback no erro — nada de estado parcial.
- RP-01/RP-04: nenhuma senha hardcoded — usa SEED_DEFAULT_PASSWORD do
  ambiente ou gera senhas aleatórias (impressas uma única vez no console);
  o hash gravado é werkzeug (salt automático), nunca MD5.
"""
import logging
import os
import secrets
from datetime import timedelta

from sqlalchemy import delete

from app import create_app
from database import db
from models.category import Category
from models.task import Task
from models.user import User
from utils.helpers import now_utc

logger = logging.getLogger(__name__)

RANDOM_PASSWORD_BYTES = 12

USERS_SPEC = (
    {'name': 'João Silva', 'email': 'joao@email.com', 'role': 'admin'},
    {'name': 'Maria Santos', 'email': 'maria@email.com', 'role': 'user'},
    {'name': 'Pedro Oliveira', 'email': 'pedro@email.com', 'role': 'manager'},
)

CATEGORIES_SPEC = (
    {'name': 'Backend', 'description': 'Tarefas de backend', 'color': '#3498db'},
    {'name': 'Frontend', 'description': 'Tarefas de frontend', 'color': '#2ecc71'},
    {'name': 'DevOps', 'description': 'Tarefas de infraestrutura', 'color': '#e74c3c'},
    {'name': 'Bug', 'description': 'Correção de bugs', 'color': '#e67e22'},
)


def _resolve_password():
    """Senha do ambiente ou aleatória (nunca hardcoded/versionada)."""
    configured = os.environ.get('SEED_DEFAULT_PASSWORD')
    if configured:
        return configured, False
    return secrets.token_urlsafe(RANDOM_PASSWORD_BYTES), True


def _build_tasks(users, categories):
    """Specs das tasks de exemplo referenciando ids já atribuídos via flush()."""
    joao, maria, pedro = users
    backend, frontend, devops, bug = categories
    today = now_utc()
    return [
        {'title': 'Implementar autenticação JWT', 'description': 'Adicionar autenticação real com JWT', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': backend.id, 'due_date': today - timedelta(days=3)},
        {'title': 'Criar tela de login', 'description': 'Tela de login responsiva', 'status': 'in_progress', 'priority': 2, 'user_id': maria.id, 'category_id': frontend.id, 'due_date': today + timedelta(days=5)},
        {'title': 'Configurar CI/CD', 'description': 'Pipeline com GitHub Actions', 'status': 'done', 'priority': 2, 'user_id': pedro.id, 'category_id': devops.id, 'tags': 'devops,ci,github'},
        {'title': 'Corrigir bug no filtro de busca', 'description': 'Filtro não funciona com caracteres especiais', 'status': 'pending', 'priority': 1, 'user_id': joao.id, 'category_id': bug.id, 'due_date': today - timedelta(days=1)},
        {'title': 'Adicionar paginação na API', 'description': 'Endpoints retornam todos os registros', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'due_date': today + timedelta(days=10)},
        {'title': 'Escrever testes unitários', 'description': 'Cobertura mínima de 80%', 'status': 'pending', 'priority': 2, 'user_id': maria.id, 'category_id': backend.id},
        {'title': 'Documentar API com Swagger', 'description': 'Gerar documentação automática', 'status': 'cancelled', 'priority': 4, 'user_id': pedro.id, 'category_id': backend.id},
        {'title': 'Refatorar models', 'description': 'Melhorar organização dos models', 'status': 'in_progress', 'priority': 3, 'user_id': maria.id, 'category_id': backend.id, 'tags': 'refactor,tech-debt'},
        {'title': 'Configurar monitoramento', 'description': 'Prometheus + Grafana', 'status': 'pending', 'priority': 4, 'user_id': pedro.id, 'category_id': devops.id, 'due_date': today + timedelta(days=20)},
        {'title': 'Melhorar validações de input', 'description': 'Usar marshmallow ou pydantic', 'status': 'pending', 'priority': 3, 'user_id': joao.id, 'category_id': backend.id, 'tags': 'improvement,validation'},
    ]


def seed_data(app):
    with app.app_context():
        generated_credentials = []
        try:
            # Transação única: limpeza + inserções commitam juntas (RP-07).
            db.session.execute(delete(Task))
            db.session.execute(delete(User))
            db.session.execute(delete(Category))

            users = []
            for spec in USERS_SPEC:
                password, was_generated = _resolve_password()
                user = User(name=spec['name'], email=spec['email'], role=spec['role'])
                user.set_password(password)
                users.append(user)
                if was_generated:
                    generated_credentials.append((spec['email'], password))
            db.session.add_all(users)

            categories = [Category(**spec) for spec in CATEGORIES_SPEC]
            db.session.add_all(categories)

            db.session.flush()  # atribui ids sem commitar (mesma transação)

            db.session.add_all(Task(**spec) for spec in _build_tasks(users, categories))
            db.session.commit()
        except Exception:
            db.session.rollback()
            logger.exception('Seed falhou — transação revertida, banco intacto')
            raise

        logger.info('Seed concluído com sucesso!')
        logger.info('  %d usuários', User.count_all())
        logger.info('  %d categorias', Category.count_all())
        logger.info('  %d tasks', len(Task.list_with_relations()))
        for email, password in generated_credentials:
            # Impressa UMA única vez; não fica registrada em nenhum arquivo.
            logger.info('  senha gerada para %s: %s', email, password)


if __name__ == '__main__':
    seed_data(create_app())
