"""Rota de autenticação — fina: parsing de request e delegação ao controller."""
from flask import Blueprint, jsonify, request

from controllers import auth_controller

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    body, status = auth_controller.login(request.get_json(silent=True))
    return jsonify(body), status
