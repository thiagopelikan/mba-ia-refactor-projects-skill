"""Rotas de usuários — finas: parsing de request e delegação ao controller.

DELETE /users/<id> exige role admin (@admin_required, RP-12 / AP-05):
deletar usuário é ação administrativa e apaga as tasks dele em cascata.
"""
from flask import Blueprint, jsonify, request

from controllers import user_controller
from middlewares.auth import admin_required

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    body, status = user_controller.list_users()
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    body, status = user_controller.get_user(user_id)
    return jsonify(body), status


@user_bp.route('/users', methods=['POST'])
def create_user():
    body, status = user_controller.create_user(request.get_json(silent=True))
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    body, status = user_controller.update_user(user_id, request.get_json(silent=True))
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    body, status = user_controller.delete_user(user_id)
    return jsonify(body), status


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    body, status = user_controller.get_user_tasks(user_id)
    return jsonify(body), status
