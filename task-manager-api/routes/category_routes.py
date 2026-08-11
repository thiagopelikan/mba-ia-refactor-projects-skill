"""Rotas de categorias — separadas de report_routes (RP-15), finas."""
from flask import Blueprint, jsonify, request

from controllers import category_controller

category_bp = Blueprint('categories', __name__)


@category_bp.route('/categories', methods=['GET'])
def get_categories():
    body, status = category_controller.list_categories()
    return jsonify(body), status


@category_bp.route('/categories', methods=['POST'])
def create_category():
    body, status = category_controller.create_category(request.get_json(silent=True))
    return jsonify(body), status


@category_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    body, status = category_controller.update_category(cat_id, request.get_json(silent=True))
    return jsonify(body), status


@category_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    body, status = category_controller.delete_category(cat_id)
    return jsonify(body), status
