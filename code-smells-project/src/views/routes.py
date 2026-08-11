"""Rotas HTTP (RP-03).

Blueprints por domínio com handlers FINOS: apenas parsing de
request/response, delegando toda a orquestração aos controllers.
Sem SQL, sem regra de negócio, sem efeitos colaterais.

As rotas `/admin/query` (SQL arbitrário) e `/admin/reset-db` (destrutiva)
do legado foram REMOVIDAS (RP-12) — respondem 404.
"""
from flask import Blueprint, jsonify, request

from src.config.settings import APP_VERSION


def _json_body():
    return request.get_json(silent=True)


def criar_rotas_produtos(controller):
    bp = Blueprint("produtos", __name__)

    @bp.get("/produtos")
    def listar_produtos():
        corpo, status = controller.listar()
        return jsonify(corpo), status

    @bp.get("/produtos/busca")
    def buscar_produtos():
        corpo, status = controller.buscar_com_filtros(request.args)
        return jsonify(corpo), status

    @bp.get("/produtos/<int:produto_id>")
    def buscar_produto(produto_id):
        corpo, status = controller.buscar(produto_id)
        return jsonify(corpo), status

    @bp.post("/produtos")
    def criar_produto():
        corpo, status = controller.criar(_json_body())
        return jsonify(corpo), status

    @bp.put("/produtos/<int:produto_id>")
    def atualizar_produto(produto_id):
        corpo, status = controller.atualizar(produto_id, _json_body())
        return jsonify(corpo), status

    @bp.delete("/produtos/<int:produto_id>")
    def deletar_produto(produto_id):
        corpo, status = controller.deletar(produto_id)
        return jsonify(corpo), status

    return bp


def criar_rotas_usuarios(controller):
    bp = Blueprint("usuarios", __name__)

    @bp.get("/usuarios")
    def listar_usuarios():
        corpo, status = controller.listar()
        return jsonify(corpo), status

    @bp.get("/usuarios/<int:usuario_id>")
    def buscar_usuario(usuario_id):
        corpo, status = controller.buscar(usuario_id)
        return jsonify(corpo), status

    @bp.post("/usuarios")
    def criar_usuario():
        corpo, status = controller.criar(_json_body())
        return jsonify(corpo), status

    @bp.post("/login")
    def login():
        corpo, status = controller.login(_json_body())
        return jsonify(corpo), status

    return bp


def criar_rotas_pedidos(controller):
    bp = Blueprint("pedidos", __name__)

    @bp.post("/pedidos")
    def criar_pedido():
        corpo, status = controller.criar(_json_body())
        return jsonify(corpo), status

    @bp.get("/pedidos")
    def listar_todos_pedidos():
        corpo, status = controller.listar_todos()
        return jsonify(corpo), status

    @bp.get("/pedidos/usuario/<int:usuario_id>")
    def listar_pedidos_usuario(usuario_id):
        corpo, status = controller.listar_por_usuario(usuario_id)
        return jsonify(corpo), status

    @bp.put("/pedidos/<int:pedido_id>/status")
    def atualizar_status_pedido(pedido_id):
        corpo, status = controller.atualizar_status(pedido_id, _json_body())
        return jsonify(corpo), status

    @bp.get("/relatorios/vendas")
    def relatorio_vendas():
        corpo, status = controller.relatorio_vendas()
        return jsonify(corpo), status

    return bp


def criar_rotas_sistema(health_controller):
    bp = Blueprint("sistema", __name__)

    @bp.get("/")
    def index():
        return jsonify(
            {
                "mensagem": "Bem-vindo à API da Loja",
                "versao": APP_VERSION,
                "endpoints": {
                    "produtos": "/produtos",
                    "usuarios": "/usuarios",
                    "pedidos": "/pedidos",
                    "login": "/login",
                    "relatorios": "/relatorios/vendas",
                    "health": "/health",
                },
            }
        )

    @bp.get("/health")
    def health_check():
        corpo, status = health_controller.verificar()
        return jsonify(corpo), status

    return bp
