"""Model do domínio Produto (RP-02, RP-03, RP-14).

Todas as queries são parametrizadas com placeholders `?` e a serialização
existe em UM único lugar (`serializar_produto`).
"""

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"


def serializar_produto(row):
    """Serialização única de produto (elimina a duplicação do legado)."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "descricao": row["descricao"],
        "preco": row["preco"],
        "estoque": row["estoque"],
        "categoria": row["categoria"],
        "ativo": row["ativo"],
        "criado_em": row["criado_em"],
    }


class ProdutoModel:
    def __init__(self, db_provider):
        self._db = db_provider

    def listar(self):
        rows = self._db().execute("SELECT * FROM produtos").fetchall()
        return [serializar_produto(row) for row in rows]

    def buscar_por_id(self, produto_id):
        row = self._db().execute(
            "SELECT * FROM produtos WHERE id = ?", (produto_id,)
        ).fetchone()
        return serializar_produto(row) if row else None

    def criar(self, nome, descricao, preco, estoque, categoria):
        db = self._db()
        cursor = db.execute(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
            " VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )
        db.commit()
        return cursor.lastrowid

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        db = self._db()
        db.execute(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?,"
            " categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )
        db.commit()

    def deletar(self, produto_id):
        db = self._db()
        db.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
        db.commit()

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Busca com filtros dinâmicos — cláusulas montadas SEMPRE com placeholders;
        o `%` do LIKE entra no parâmetro, nunca no SQL (RP-02)."""
        sql = "SELECT * FROM produtos WHERE 1=1"
        params = []
        if termo:
            sql += " AND (nome LIKE ? OR descricao LIKE ?)"
            like = f"%{termo}%"
            params.extend([like, like])
        if categoria:
            sql += " AND categoria = ?"
            params.append(categoria)
        if preco_min is not None:
            sql += " AND preco >= ?"
            params.append(preco_min)
        if preco_max is not None:
            sql += " AND preco <= ?"
            params.append(preco_max)

        rows = self._db().execute(sql, params).fetchall()
        return [serializar_produto(row) for row in rows]

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
