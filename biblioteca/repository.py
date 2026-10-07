"""Repositórios: camada responsável por armazenar e recuperar livros."""
import sqlite3
from dataclasses import replace

from biblioteca.excecoes import (
    ErroPersistenciaError,
    LivroDuplicadoError,
    LivroNaoEncontradoError,
)
from biblioteca.livro import Livro


class RepositorioMemoria:
    """Repositório em dicionário (sem persistência). Guarda cópias dos livros."""

    def __init__(self):
        self._livros = {}

    def salvar(self, livro):
        if livro.isbn in self._livros:
            raise LivroDuplicadoError(f"ISBN já cadastrado: {livro.isbn}")
        self._livros[livro.isbn] = replace(livro)

    def atualizar(self, livro):
        if livro.isbn not in self._livros:
            raise LivroNaoEncontradoError(f"ISBN não encontrado: {livro.isbn}")
        self._livros[livro.isbn] = replace(livro)

    def buscar_por_isbn(self, isbn):
        livro = self._livros.get(isbn)
        return replace(livro) if livro else None

    def existe(self, isbn):
        return isbn in self._livros

    def listar(self):
        return [replace(self._livros[i]) for i in sorted(self._livros)]


class LivroRepository:
    """Repositório SQLite. Recebe a conexão pronta (injeção de dependência)."""

    def __init__(self, conexao):
        self._conexao = conexao

    # --- auxiliares: convertem erros do sqlite3 em erro do domínio ---
    def _escrever(self, sql, parametros, acao):
        try:
            with self._conexao:  # commit/rollback automático
                return self._conexao.execute(sql, parametros).rowcount
        except sqlite3.Error as erro:
            raise ErroPersistenciaError(f"Falha ao {acao}: {erro}") from erro

    def _ler(self, sql, parametros, acao):
        try:
            return self._conexao.execute(sql, parametros).fetchall()
        except sqlite3.Error as erro:
            raise ErroPersistenciaError(f"Falha ao {acao}: {erro}") from erro

    # --- operações públicas ---
    def salvar(self, livro):
        try:
            with self._conexao:
                self._conexao.execute(
                    "INSERT INTO livros (isbn, titulo, autor, quantidade) "
                    "VALUES (?, ?, ?, ?)",
                    (livro.isbn, livro.titulo, livro.autor, livro.quantidade),
                )
        except sqlite3.IntegrityError as erro:
            raise LivroDuplicadoError(f"ISBN já cadastrado: {livro.isbn}") from erro
        except sqlite3.Error as erro:
            raise ErroPersistenciaError(f"Falha ao salvar: {erro}") from erro

    def atualizar(self, livro):
        alteradas = self._escrever(
            "UPDATE livros SET titulo = ?, autor = ?, quantidade = ? WHERE isbn = ?",
            (livro.titulo, livro.autor, livro.quantidade, livro.isbn),
            "atualizar livro",
        )
        if alteradas == 0:
            raise LivroNaoEncontradoError(f"ISBN não encontrado: {livro.isbn}")

    def buscar_por_isbn(self, isbn):
        linhas = self._ler(
            "SELECT isbn, titulo, autor, quantidade FROM livros WHERE isbn = ?",
            (isbn,),
            "buscar livro",
        )
        return Livro(*linhas[0]) if linhas else None

    def existe(self, isbn):
        linhas = self._ler(
            "SELECT 1 FROM livros WHERE isbn = ?", (isbn,), "verificar existência"
        )
        return bool(linhas)

    def listar(self):
        linhas = self._ler(
            "SELECT isbn, titulo, autor, quantidade FROM livros ORDER BY isbn",
            (),
            "listar livros",
        )
        return [Livro(*linha) for linha in linhas]
