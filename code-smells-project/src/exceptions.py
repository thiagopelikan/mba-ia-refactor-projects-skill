"""Exceções tipadas da aplicação (RP-08).

Controllers e models levantam estas exceções; o middleware de erro
(`middlewares/error_handler.py`) as converte em respostas HTTP padronizadas.
Nenhum handler precisa de try/except próprio.
"""


class ApiError(Exception):
    """Base das exceções que viram resposta HTTP."""

    status = 500

    def __init__(self, mensagem, extra=None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        self.extra = extra or {}

    def to_payload(self):
        payload = {"erro": self.mensagem}
        payload.update(self.extra)
        return payload


class ValidationError(ApiError):
    """Entrada inválida → 400."""

    status = 400


class AuthError(ApiError):
    """Falha de autenticação → 401."""

    status = 401


class NotFoundError(ApiError):
    """Recurso inexistente → 404."""

    status = 404
