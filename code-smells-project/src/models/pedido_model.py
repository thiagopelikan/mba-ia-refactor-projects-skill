"""Model do domínio Pedido (RP-02, RP-05, RP-07, RP-09, RP-14, RP-15).

- Criação de pedido é ATÔMICA: validação de estoque, INSERT do pedido,
  INSERT dos itens e baixa de estoque commitam juntos ou revertem juntos.
- Leitura de pedidos usa UM JOIN (elimina o N+1 do legado) e existe em um
  único método parametrizado por filtro (elimina a duplicação
  get_pedidos_usuario/get_todos_pedidos).
- Regras de negócio (faixas de desconto, transição de status com devolução
  de estoque) vivem aqui, testáveis sem HTTP.
"""
from src.exceptions import NotFoundError, ValidationError

STATUS_PENDENTE = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_ENVIADO = "enviado"
STATUS_ENTREGUE = "entregue"
STATUS_CANCELADO = "cancelado"
STATUS_VALIDOS = (
    STATUS_PENDENTE,
    STATUS_APROVADO,
    STATUS_ENVIADO,
    STATUS_ENTREGUE,
    STATUS_CANCELADO,
)

PRODUTO_DESCONHECIDO = "Desconhecido"

# Faixas de desconto do relatório de vendas (RP-15 — antes eram magic numbers).
# Ordem decrescente: aplica-se o percentual da primeira faixa excedida.
FAIXAS_DESCONTO = (
    (10_000, 0.10),
    (5_000, 0.05),
    (1_000, 0.02),
)


def calcular_desconto(faturamento):
    """Regra de domínio nomeada e testável sem banco/HTTP."""
    for limite, percentual in FAIXAS_DESCONTO:
        if faturamento > limite:
            return faturamento * percentual
    return 0


class PedidoModel:
    def __init__(self, db_provider):
        self._db = db_provider

    def criar_com_itens(self, usuario_id, itens):
        """Cria o pedido com itens e baixa de estoque em UMA transação (RP-07)."""
        db = self._db()
        try:
            total = 0
            precos = {}
            for item in itens:
                produto = db.execute(
                    "SELECT id, nome, preco, estoque FROM produtos WHERE id = ?",
                    (item["produto_id"],),
                ).fetchone()
                if produto is None:
                    raise ValidationError(
                        f"Produto {item['produto_id']} não encontrado",
                        extra={"sucesso": False},
                    )
                if produto["estoque"] < item["quantidade"]:
                    raise ValidationError(
                        f"Estoque insuficiente para {produto['nome']}",
                        extra={"sucesso": False},
                    )
                precos[item["produto_id"]] = produto["preco"]
                total += produto["preco"] * item["quantidade"]

            cursor = db.execute(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PENDENTE, total),
            )
            pedido_id = cursor.lastrowid

            for item in itens:
                db.execute(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade,"
                    " preco_unitario) VALUES (?, ?, ?, ?)",
                    (
                        pedido_id,
                        item["produto_id"],
                        item["quantidade"],
                        precos[item["produto_id"]],
                    ),
                )
                db.execute(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )

            db.commit()
        except Exception:
            db.rollback()
            raise

        return {"pedido_id": pedido_id, "total": total}

    def listar(self, usuario_id=None):
        """Lista pedidos com itens em UMA query com JOIN (RP-09); o filtro por
        usuário reaproveita a mesma implementação (RP-14)."""
        sql = (
            "SELECT p.id, p.usuario_id, p.status, p.total, p.criado_em,"
            " i.produto_id, i.quantidade, i.preco_unitario,"
            " pr.nome AS produto_nome"
            " FROM pedidos p"
            " LEFT JOIN itens_pedido i ON i.pedido_id = p.id"
            " LEFT JOIN produtos pr ON pr.id = i.produto_id"
        )
        params = ()
        if usuario_id is not None:
            sql += " WHERE p.usuario_id = ?"
            params = (usuario_id,)
        sql += " ORDER BY p.id, i.id"

        rows = self._db().execute(sql, params).fetchall()

        pedidos = {}
        for row in rows:
            pedido = pedidos.setdefault(
                row["id"],
                {
                    "id": row["id"],
                    "usuario_id": row["usuario_id"],
                    "status": row["status"],
                    "total": row["total"],
                    "criado_em": row["criado_em"],
                    "itens": [],
                },
            )
            if row["produto_id"] is not None:
                pedido["itens"].append(
                    {
                        "produto_id": row["produto_id"],
                        "produto_nome": row["produto_nome"] or PRODUTO_DESCONHECIDO,
                        "quantidade": row["quantidade"],
                        "preco_unitario": row["preco_unitario"],
                    }
                )
        return list(pedidos.values())

    def atualizar_status(self, pedido_id, novo_status):
        """Transição de status como regra de domínio (RP-05): cancelamento
        devolve o estoque dos itens, na mesma transação do UPDATE."""
        db = self._db()
        pedido = db.execute(
            "SELECT id, status FROM pedidos WHERE id = ?", (pedido_id,)
        ).fetchone()
        if pedido is None:
            raise NotFoundError("Pedido não encontrado")

        try:
            if novo_status == STATUS_CANCELADO and pedido["status"] != STATUS_CANCELADO:
                itens = db.execute(
                    "SELECT produto_id, quantidade FROM itens_pedido WHERE pedido_id = ?",
                    (pedido_id,),
                ).fetchall()
                for item in itens:
                    db.execute(
                        "UPDATE produtos SET estoque = estoque + ? WHERE id = ?",
                        (item["quantidade"], item["produto_id"]),
                    )
            db.execute(
                "UPDATE pedidos SET status = ? WHERE id = ?",
                (novo_status, pedido_id),
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

    def relatorio_vendas(self):
        """Relatório consolidado em uma única query agregada."""
        row = self._db().execute(
            "SELECT COUNT(*) AS total_pedidos,"
            " COALESCE(SUM(total), 0) AS faturamento,"
            " COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS pendentes,"
            " COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS aprovados,"
            " COALESCE(SUM(CASE WHEN status = ? THEN 1 ELSE 0 END), 0) AS cancelados"
            " FROM pedidos",
            (STATUS_PENDENTE, STATUS_APROVADO, STATUS_CANCELADO),
        ).fetchone()

        total_pedidos = row["total_pedidos"]
        faturamento = row["faturamento"]
        desconto = calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, 2),
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "pedidos_pendentes": row["pendentes"],
            "pedidos_aprovados": row["aprovados"],
            "pedidos_cancelados": row["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, 2) if total_pedidos > 0 else 0,
        }

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
