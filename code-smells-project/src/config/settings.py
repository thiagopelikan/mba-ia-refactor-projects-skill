"""Configuração da aplicação (RP-01).

Todos os valores configuráveis/sensíveis vêm de variáveis de ambiente —
nada hardcoded no restante do código. As chaves esperadas estão
documentadas em `.env.example` na raiz do projeto.
"""
import os
from dataclasses import dataclass

# Constante de aplicação (não é configuração sensível/por ambiente).
APP_VERSION = "1.0.0"

_DEFAULT_DATABASE_PATH = "loja.db"
_DEFAULT_HOST = "127.0.0.1"
_DEFAULT_PORT = 5000


class ConfigError(RuntimeError):
    """Configuração ausente ou inválida — a aplicação não deve subir."""


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_path: str
    host: str
    port: int
    debug: bool
    cors_origins: tuple


def load_settings(env=None) -> Settings:
    """Carrega a configuração a partir do ambiente.

    SECRET_KEY é obrigatória (sem default): falhar no boot é melhor do que
    rodar assinando sessões/tokens com uma chave vazia ou previsível.
    """
    env = os.environ if env is None else env

    secret_key = env.get("SECRET_KEY", "").strip()
    if not secret_key:
        raise ConfigError(
            "SECRET_KEY é obrigatória e não foi definida. "
            "Exporte a variável de ambiente (veja .env.example)."
        )

    try:
        port = int(env.get("PORT", str(_DEFAULT_PORT)))
    except ValueError as exc:
        raise ConfigError("PORT deve ser um número inteiro.") from exc

    cors_origins = tuple(
        origem.strip()
        for origem in env.get("CORS_ORIGINS", "").split(",")
        if origem.strip()
    )

    return Settings(
        secret_key=secret_key,
        database_path=env.get("DATABASE_PATH", _DEFAULT_DATABASE_PATH),
        host=env.get("HOST", _DEFAULT_HOST),
        port=port,
        debug=env.get("FLASK_DEBUG", "0") == "1",
        cors_origins=cors_origins,
    )
