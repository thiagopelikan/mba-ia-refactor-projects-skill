"""Controller de health check (RP-01, RP-15).

Devolve apenas status e contadores não sensíveis — sem secret_key,
db_path ou flag de debug (o legado vazava os três).
"""
from src.config.settings import APP_VERSION


class HealthController:
    def __init__(self, produto_model, usuario_model, pedido_model):
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model

    def verificar(self):
        return {
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": APP_VERSION,
        }, 200
