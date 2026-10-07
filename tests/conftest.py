"""Fixtures compartilhadas (Questão 6) e ambiente de integração (Questão 12)."""
from dataclasses import dataclass
import sqlite3

import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.database import conectar, inicializar_banco
from biblioteca.livro import Livro
from biblioteca.repository import LivroRepository, RepositorioMemoria


# ---------------------------------------------------------------- Questão 6
@pytest.fixture
def livro():
    """Livro válido com 3 exemplares."""
    return Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)


@pytest.fixture
def livro_disponivel():
    """Livro com 2 exemplares (pode ser emprestado)."""
    return Livro("9780134757599", "Refactoring", "Martin Fowler", 2)


@pytest.fixture
def livro_indisponivel():
    """Livro com 0 exemplares (empréstimo deve ser bloqueado)."""
    return Livro("9780135957059", "The Pragmatic Programmer", "Andrew Hunt", 0)


@pytest.fixture
def repositorio():
    return RepositorioMemoria()


@pytest.fixture
def biblioteca(repositorio):
    return Biblioteca(repositorio)


# --------------------------------------------------------------- Questão 12
@dataclass
class Ambiente:
    conexao: sqlite3.Connection
    repositorio: LivroRepository
    biblioteca: Biblioteca


@pytest.fixture
def ambiente_integracao():
    # SETUP: banco SQLite em memória + tabela + repositório + biblioteca reais
    conexao = conectar(":memory:")
    inicializar_banco(conexao)
    repositorio = LivroRepository(conexao)
    yield Ambiente(conexao, repositorio, Biblioteca(repositorio))
    # TEARDOWN: fecha a conexão (o banco em memória deixa de existir)
    conexao.close()
