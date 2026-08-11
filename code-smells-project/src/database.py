"""Infraestrutura de banco (RP-06).

Conexão SQLite com escopo de request via `flask.g` + `teardown_appcontext` —
substitui o singleton global thread-unsafe (`check_same_thread=False`) do
código legado. O schema/seed é criado uma única vez no boot, pelo
composition root (`src/app.py`).
"""
import logging
import sqlite3

from flask import current_app, g
from werkzeug.security import generate_password_hash

logger = logging.getLogger(__name__)

_SCHEMA = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        descricao TEXT,
        preco REAL,
        estoque INTEGER,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        email TEXT,
        senha TEXT,
        tipo TEXT DEFAULT 'cliente',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER,
        produto_id INTEGER,
        quantidade INTEGER,
        preco_unitario REAL
    )
    """,
)

_SEED_PRODUTOS = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

# Senhas de seed em claro APENAS aqui como dado de desenvolvimento;
# são gravadas no banco já com hash (RP-04).
_SEED_USUARIOS = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


def init_app(app):
    """Registra o teardown da conexão e garante schema/seed no boot."""
    app.teardown_appcontext(close_db)
    inicializar_banco(app.config["DATABASE_PATH"])


def get_db():
    """Conexão SQLite com escopo de request (criada e usada na mesma thread)."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def inicializar_banco(database_path):
    """Cria as tabelas e o seed inicial (senhas com hash) se o banco estiver vazio."""
    conn = sqlite3.connect(database_path)
    try:
        for ddl in _SCHEMA:
            conn.execute(ddl)
        conn.commit()

        total_produtos = conn.execute("SELECT COUNT(*) FROM produtos").fetchone()[0]
        if total_produtos == 0:
            conn.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria)"
                " VALUES (?, ?, ?, ?, ?)",
                _SEED_PRODUTOS,
            )
            conn.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                [
                    (nome, email, generate_password_hash(senha), tipo)
                    for nome, email, senha, tipo in _SEED_USUARIOS
                ],
            )
            conn.commit()
            logger.info(
                "Banco %s inicializado com seed (%d produtos, %d usuários)",
                database_path,
                len(_SEED_PRODUTOS),
                len(_SEED_USUARIOS),
            )
    finally:
        conn.close()
