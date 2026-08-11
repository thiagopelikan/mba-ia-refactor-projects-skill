"""Configuração central da aplicação (RP-01).

Todos os valores configuráveis/sensíveis vêm de variáveis de ambiente
(carregadas de um arquivo `.env` local via python-dotenv, se existir).
Zero valores hardcoded no restante do código. As chaves esperadas estão
documentadas em `.env.example`.
"""
import os

from dotenv import load_dotenv

load_dotenv()

# Obrigatória: a aplicação deve falhar cedo em vez de rodar com chave fraca.
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY não definida. Copie .env.example para .env e defina uma '
        'chave forte (ex.: python -c "import secrets; print(secrets.token_hex(32))").'
    )

SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///tasks.db')
SQLALCHEMY_TRACK_MODIFICATIONS = False

DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', '5000'))

# Lista separada por vírgula (ex.: "https://app.exemplo.com,https://admin.exemplo.com").
# Default '*' preserva o comportamento anterior; restrinja por ambiente via env var.
_cors_origins = os.environ.get('CORS_ORIGINS', '*')
CORS_ORIGINS = (
    '*' if _cors_origins.strip() == '*'
    else [origin.strip() for origin in _cors_origins.split(',') if origin.strip()]
)

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

# Validade (em segundos) dos tokens emitidos pelo /login. Default: 8 horas.
AUTH_TOKEN_MAX_AGE_SECONDS = int(os.environ.get('AUTH_TOKEN_MAX_AGE_SECONDS', '28800'))
