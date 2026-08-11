"""Infraestrutura de autenticação (RP-12 / AP-05 / AP-06).

O /login agora emite um token REAL, assinado com a SECRET_KEY da Config
(itsdangerous — dependência do próprio Flask), com validade configurável e
verificável por `verify_token()` / `@auth_required` / `@admin_required`.

LIMITAÇÃO ACEITA (documentada, como nos Projetos 1 e 2): o contrato do
baseline exercita DELETEs e rotas administrativas SEM header Authorization
e espera sucesso (200). Exigir auth quebraria o contrato, portanto os
decorators abaixo NÃO estão aplicados às rotas do baseline por padrão —
a infraestrutura está pronta para ser ativada rota a rota:

    @task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
    @auth_required          # ou @admin_required
    def delete_task(task_id): ...
"""
from functools import wraps

from flask import current_app, g, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from middlewares.error_handler import ForbiddenError, UnauthorizedError

_TOKEN_SALT = 'task-manager-auth-token'
_BEARER_PREFIX = 'Bearer '


def _serializer():
    return URLSafeTimedSerializer(current_app.config['SECRET_KEY'], salt=_TOKEN_SALT)


def generate_token(user):
    """Gera token assinado com a SECRET_KEY carregando id e role do usuário."""
    return _serializer().dumps({'user_id': user.id, 'role': user.role})


def verify_token(token, max_age=None):
    """Valida assinatura e idade do token; devolve o payload ou levanta 401."""
    if max_age is None:
        max_age = current_app.config.get('AUTH_TOKEN_MAX_AGE_SECONDS', 28800)
    try:
        return _serializer().loads(token, max_age=max_age)
    except SignatureExpired as exc:
        raise UnauthorizedError('Token expirado') from exc
    except BadSignature as exc:
        raise UnauthorizedError('Token inválido') from exc


def auth_required(func):
    """Exige `Authorization: Bearer <token>` válido; expõe o payload em g.auth."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        header = request.headers.get('Authorization', '')
        if not header.startswith(_BEARER_PREFIX):
            raise UnauthorizedError('Não autenticado')
        g.auth = verify_token(header[len(_BEARER_PREFIX):])
        return func(*args, **kwargs)

    return wrapper


def admin_required(func):
    """Como @auth_required, mas exige role admin no token."""

    @wraps(func)
    @auth_required
    def wrapper(*args, **kwargs):
        if g.auth.get('role') != 'admin':
            raise ForbiddenError('Acesso restrito a administradores')
        return func(*args, **kwargs)

    return wrapper
