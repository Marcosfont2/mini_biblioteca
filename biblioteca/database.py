"""Conexão e esquema do banco SQLite."""
import sqlite3

CAMINHO_PADRAO = "biblioteca.db"  # banco real da aplicação

ESQUEMA = """
CREATE TABLE IF NOT EXISTS livros (
    isbn       TEXT PRIMARY KEY,
    titulo     TEXT NOT NULL,
    autor      TEXT NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade >= 0)
)
"""


def conectar(caminho=CAMINHO_PADRAO):
    """Abre uma conexão. Os testes passam ':memory:' para não tocar no banco real."""
    return sqlite3.connect(caminho)


def inicializar_banco(conexao):
    with conexao:
        conexao.execute(ESQUEMA)
