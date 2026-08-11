"""Error handling centralizado (RP-08).

Único ponto que converte exceções em respostas HTTP JSON padronizadas.
Controllers levantam as exceções tipadas abaixo; nenhum handler de rota
tem try/except próprio e nenhum stack trace vaza para o cliente.
"""
import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

from database import db

logger = logging.getLogger(__name__)


class ApiError(Exception):
    """Base das exceções de aplicação, com status HTTP associado."""

    status_code = 500

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class ValidationError(ApiError):
    status_code = 400


class UnauthorizedError(ApiError):
    status_code = 401


class ForbiddenError(ApiError):
    status_code = 403


class NotFoundError(ApiError):
    status_code = 404


class ConflictError(ApiError):
    status_code = 409


def register_error_handlers(app):
    """Registra os handlers centrais no composition root."""

    @app.errorhandler(ApiError)
    def handle_api_error(error):
        return jsonify({'error': error.message}), error.status_code

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        # 404 de rota inexistente, 405, JSON malformado etc. — sempre JSON.
        return jsonify({'error': error.description}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        db.session.rollback()
        logger.exception('Erro não tratado')
        return jsonify({'error': 'Erro interno'}), 500
