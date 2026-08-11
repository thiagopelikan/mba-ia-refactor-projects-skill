"""Composition root: App Factory (RP-03).

Apenas composição — cria a app, carrega a Config, inicializa extensões,
registra blueprints e o error handler central. Nenhuma lógica de negócio,
nenhuma rota inline, nenhum efeito colateral no import do módulo.
"""
import logging

from flask import Flask
from flask_cors import CORS

from config import settings
from database import db
from middlewares.error_handler import register_error_handlers
from routes.auth_routes import auth_bp
from routes.category_routes import category_bp
from routes.main_routes import main_bp
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

BLUEPRINTS = (main_bp, task_bp, user_bp, auth_bp, category_bp, report_bp)


def create_app(config_object=settings):
    logging.basicConfig(
        level=getattr(logging, str(getattr(config_object, 'LOG_LEVEL', 'INFO')).upper(), logging.INFO),
        format='%(asctime)s %(levelname)s %(name)s: %(message)s',
    )

    app = Flask(__name__)
    app.config.from_object(config_object)

    CORS(app, origins=getattr(config_object, 'CORS_ORIGINS', '*'))
    db.init_app(app)

    for blueprint in BLUEPRINTS:
        app.register_blueprint(blueprint)

    register_error_handlers(app)

    # Criação de schema dentro da factory (antes: efeito colateral do import).
    with app.app_context():
        db.create_all()

    return app


if __name__ == '__main__':
    application = create_app()
    application.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
