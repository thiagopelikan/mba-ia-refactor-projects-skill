"""Colaborador de notificações (RP-05, RP-15).

Substitui os `print("ENVIANDO EMAIL/SMS/PUSH ...")` inline dos handlers.
É injetado pelo composition root nos controllers; integrações reais
(email/SMS/push) entram aqui sem tocar nas rotas.
"""
import logging


class Notificador:
    def __init__(self, logger=None):
        self._logger = logger or logging.getLogger(__name__)

    def pedido_criado(self, pedido_id, usuario_id):
        self._logger.info(
            "Notificação (email/sms/push): pedido %s criado para usuário %s",
            pedido_id,
            usuario_id,
        )

    def pedido_aprovado(self, pedido_id):
        self._logger.info(
            "Notificação: pedido %s aprovado — preparar envio", pedido_id
        )

    def pedido_cancelado(self, pedido_id):
        self._logger.info(
            "Notificação: pedido %s cancelado — estoque devolvido", pedido_id
        )
