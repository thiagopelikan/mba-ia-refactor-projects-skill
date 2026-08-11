"""Model do domínio Usuário (RP-02, RP-04).

Senhas são armazenadas com `generate_password_hash` (salt embutido) e
verificadas com `check_password_hash`. A serialização NUNCA inclui
senha/hash — `GET /usuarios` deixa de expor credenciais.
"""
from werkzeug.security import check_password_hash, generate_password_hash

TIPO_PADRAO = "cliente"


def serializar_usuario(row):
    """Serialização única de usuário — sem `senha`/hash (RP-04)."""
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


class UsuarioModel:
    def __init__(self, db_provider):
        self._db = db_provider

    def listar(self):
        rows = self._db().execute("SELECT * FROM usuarios").fetchall()
        return [serializar_usuario(row) for row in rows]

    def buscar_por_id(self, usuario_id):
        row = self._db().execute(
            "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
        ).fetchone()
        return serializar_usuario(row) if row else None

    def criar(self, nome, email, senha, tipo=TIPO_PADRAO):
        db = self._db()
        cursor = db.execute(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, generate_password_hash(senha), tipo),
        )
        db.commit()
        return cursor.lastrowid

    def autenticar(self, email, senha):
        """Autentica comparando o hash — query parametrizada, nunca senha no SQL."""
        row = self._db().execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if row is None or not check_password_hash(row["senha"], senha):
            return None
        return {
            "id": row["id"],
            "nome": row["nome"],
            "email": row["email"],
            "tipo": row["tipo"],
        }

    def contar(self):
        return self._db().execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
