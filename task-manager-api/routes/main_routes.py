"""Rotas utilitárias (/ e /health)."""
from flask import Blueprint, jsonify

from utils.helpers import format_datetime, now_utc

API_NAME = 'Task Manager API'
API_VERSION = '1.0'

main_bp = Blueprint('main', __name__)


@main_bp.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': format_datetime(now_utc())}), 200


@main_bp.route('/')
def index():
    return jsonify({'message': API_NAME, 'version': API_VERSION}), 200
