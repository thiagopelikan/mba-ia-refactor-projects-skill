"""Middleware de autenticação (RP-12) — LIGADO por padrão.

Fábrica de decorator no estilo de DI do projeto: o composition root
(`src/app.py`) injeta o `TokenService` e obtém o decorator `auth_required`,
que as rotas sensíveis (AP-05/AP-06) aplicam SEMPRE — não existe flag para
desligar a autenticação.

Contrato: exige `Authorization: Bearer <token>`; ausente ou inválido →
`AuthError` (401 JSON via o error handler central); válido → segue e expõe
o payload autenticado em `flask.g.usuario_autenticado`.
"""
from functools import wraps

from flask import g, request

from src.exceptions import AuthError

_BEARER_PREFIX = "Bearer "


def criar_auth_required(token_service):
    """Cria o decorator `auth_required` com o TokenService injetado."""

    def auth_required(handler):
        @wraps(handler)
        def wrapper(*args, **kwargs):
            header = request.headers.get("Authorization", "")
            if not header.startswith(_BEARER_PREFIX):
                raise AuthError(
                    "Autenticação obrigatória: envie o header "
                    "'Authorization: Bearer <token>'",
                    extra={"sucesso": False},
                )

            token = header[len(_BEARER_PREFIX):].strip()
            payload = token_service.validar(token)
            if payload is None:
                raise AuthError(
                    "Token inválido ou expirado", extra={"sucesso": False}
                )

            g.usuario_autenticado = payload
            return handler(*args, **kwargs)

        return wrapper

    return auth_required
