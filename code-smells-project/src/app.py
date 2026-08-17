"""Composition root (RP-03, RP-06).

Monta a aplicação: carrega a Config, cria o app Flask, injeta as
dependências (db_provider → models → controllers → rotas) e registra
blueprints e o middleware de erro. Nenhuma regra de negócio, nenhuma
rota inline, nenhum SQL.

Uso: `python app.py` (na raiz do projeto) ou `python -m src.app`.
"""
import logging

from flask import Flask
from flask_cors import CORS

from src import database
from src.config.settings import load_settings
from src.controllers.health_controller import HealthController
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.usuario_controller import UsuarioController
from src.middlewares.auth import criar_auth_required
from src.middlewares.error_handler import register_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel
from src.services.notificador import Notificador
from src.services.token_service import TokenService
from src.views.routes import (
    criar_rotas_pedidos,
    criar_rotas_produtos,
    criar_rotas_sistema,
    criar_rotas_usuarios,
)

logger = logging.getLogger(__name__)


def _configurar_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def create_app(settings=None):
    settings = settings or load_settings()
    _configurar_logging()

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.secret_key
    app.config["DEBUG"] = settings.debug
    app.config["DATABASE_PATH"] = settings.database_path

    # CORS restrito às origens configuradas (vazio = sem CORS liberado).
    if settings.cors_origins:
        CORS(app, origins=list(settings.cors_origins))

    # Infra: conexão por request (flask.g) + schema/seed no boot.
    database.init_app(app)

    # Models (recebem o provider da conexão com escopo de request).
    produto_model = ProdutoModel(database.get_db)
    usuario_model = UsuarioModel(database.get_db)
    pedido_model = PedidoModel(database.get_db)

    # Colaboradores.
    notificador = Notificador()
    token_service = TokenService(settings.secret_key)

    # Middleware de auth (RP-12): decorator com o TokenService injetado,
    # aplicado às rotas sensíveis (AP-05/AP-06). Sempre ligado — sem flag.
    auth_required = criar_auth_required(token_service)

    # Controllers.
    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model, token_service)
    pedido_controller = PedidoController(pedido_model, notificador)
    health_controller = HealthController(produto_model, usuario_model, pedido_model)

    # Rotas + middlewares.
    app.register_blueprint(criar_rotas_sistema(health_controller))
    app.register_blueprint(criar_rotas_produtos(produto_controller, auth_required))
    app.register_blueprint(criar_rotas_usuarios(usuario_controller, auth_required))
    app.register_blueprint(criar_rotas_pedidos(pedido_controller, auth_required))
    register_error_handlers(app)

    return app


def main():
    settings = load_settings()
    app = create_app(settings)
    logger.info("Servidor iniciado em http://%s:%s", settings.host, settings.port)
    app.run(host=settings.host, port=settings.port, debug=settings.debug)


if __name__ == "__main__":
    main()
