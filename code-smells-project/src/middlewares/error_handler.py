"""Error handling centralizado (RP-08).

Único ponto que converte exceções em respostas HTTP padronizadas —
elimina os try/except duplicados por handler do legado, que vazavam
`str(e)` para o cliente. Erros inesperados são logados por completo no
servidor e respondidos com mensagem genérica.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from src.exceptions import ApiError

logger = logging.getLogger(__name__)

MENSAGEM_ERRO_INTERNO = "Erro interno"


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify(err.to_payload()), err.status

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        if isinstance(err, HTTPException):
            # 404 de rota inexistente, 405 de método errado etc.
            return jsonify({"erro": err.description}), err.code
        logger.exception("Erro não tratado")
        return jsonify({"erro": MENSAGEM_ERRO_INTERNO}), 500
