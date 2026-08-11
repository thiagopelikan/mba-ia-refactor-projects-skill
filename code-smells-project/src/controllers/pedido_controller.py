"""Controller do domínio Pedido (RP-03, RP-05, RP-11).

Handler fino: valida entrada, delega ao model (que é transacional) e
dispara notificações via colaborador injetado — nada de `print` nem
regra de negócio na rota.
"""
from src.exceptions import ValidationError
from src.models.pedido_model import STATUS_APROVADO, STATUS_CANCELADO, STATUS_VALIDOS


def _validar_pedido(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not isinstance(usuario_id, int) or isinstance(usuario_id, bool):
        raise ValidationError("Usuario ID deve ser um número inteiro")
    if not isinstance(itens, list) or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Cada item deve ter produto_id e quantidade")
        if not isinstance(item["produto_id"], int) or isinstance(item["produto_id"], bool):
            raise ValidationError("produto_id deve ser um número inteiro")
        if (
            not isinstance(item["quantidade"], int)
            or isinstance(item["quantidade"], bool)
            or item["quantidade"] <= 0
        ):
            raise ValidationError("quantidade deve ser um número inteiro positivo")

    return usuario_id, itens


class PedidoController:
    def __init__(self, pedido_model, notificador):
        self._pedidos = pedido_model
        self._notificador = notificador

    def criar(self, dados):
        usuario_id, itens = _validar_pedido(dados)
        resultado = self._pedidos.criar_com_itens(usuario_id, itens)
        self._notificador.pedido_criado(resultado["pedido_id"], usuario_id)
        return {
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }, 201

    def listar_todos(self):
        return {"dados": self._pedidos.listar(), "sucesso": True}, 200

    def listar_por_usuario(self, usuario_id):
        return {"dados": self._pedidos.listar(usuario_id=usuario_id), "sucesso": True}, 200

    def atualizar_status(self, pedido_id, dados):
        if not dados:
            raise ValidationError("Dados inválidos")
        novo_status = dados.get("status", "")
        if novo_status not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")

        self._pedidos.atualizar_status(pedido_id, novo_status)

        if novo_status == STATUS_APROVADO:
            self._notificador.pedido_aprovado(pedido_id)
        elif novo_status == STATUS_CANCELADO:
            self._notificador.pedido_cancelado(pedido_id)

        return {"sucesso": True, "mensagem": "Status atualizado"}, 200

    def relatorio_vendas(self):
        return {"dados": self._pedidos.relatorio_vendas(), "sucesso": True}, 200
