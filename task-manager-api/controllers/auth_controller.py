"""Controller de autenticação: login com token real assinado (RP-04/RP-12)."""
import logging

from middlewares.auth import generate_token
from middlewares.error_handler import ForbiddenError, UnauthorizedError, ValidationError
from models.user import User

logger = logging.getLogger(__name__)


def login(data):
    if not isinstance(data, dict) or not data:
        raise ValidationError('Dados inválidos')

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise ValidationError('Email e senha são obrigatórios')

    user = User.get_by_email(email)
    if not user or not user.check_password(password):
        # Mesma mensagem para usuário inexistente e senha errada (não enumera contas).
        raise UnauthorizedError('Credenciais inválidas')
    if not user.active:
        raise ForbiddenError('Usuário inativo')

    logger.info('Login bem-sucedido: user %s', user.id)
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),  # serialização segura: sem senha/hash (RP-04)
        'token': generate_token(user),  # token assinado com a SECRET_KEY (RP-12)
    }, 200
