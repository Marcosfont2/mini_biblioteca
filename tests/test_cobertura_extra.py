"""Questão 14 – testes adicionados APÓS analisar o relatório de cobertura.

O relatório inicial mostrou repository.py com 82%: faltavam os caminhos de erro
do repositório SQLite (falhas de banco), o listar() do SQLite e as exceções do
repositório em memória.
"""
import pytest

from biblioteca.excecoes import (
    ErroPersistenciaError,
    LivroDuplicadoError,
    LivroNaoEncontradoError,
)
from biblioteca.livro import Livro
from biblioteca.repository import RepositorioMemoria

LIVRO_A = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
LIVRO_B = Livro("9780134757599", "Refactoring", "Martin Fowler", 2)


# --- repositório em memória: exceções que não eram exercitadas -----------------
def test_repositorio_memoria_salvar_duplicado():
    repo = RepositorioMemoria()
    repo.salvar(LIVRO_A)
    with pytest.raises(LivroDuplicadoError):
        repo.salvar(LIVRO_A)


def test_repositorio_memoria_atualizar_inexistente():
    with pytest.raises(LivroNaoEncontradoError):
        RepositorioMemoria().atualizar(LIVRO_A)


# --- repositório SQLite: listar() ----------------------------------------------
def test_repositorio_sqlite_listar_ordenado_por_isbn(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    repo.salvar(LIVRO_B)  # ISBN maior, salvo primeiro de propósito
    repo.salvar(LIVRO_A)
    assert repo.listar() == [LIVRO_A, LIVRO_B]


def test_repositorio_sqlite_listar_vazio(ambiente_integracao):
    assert ambiente_integracao.repositorio.listar() == []


# --- repositório SQLite: falhas do banco viram ErroPersistenciaError ----------
@pytest.mark.parametrize(
    "operacao",
    [
        pytest.param(lambda r: r.salvar(LIVRO_A), id="salvar"),
        pytest.param(lambda r: r.atualizar(LIVRO_A), id="atualizar"),
        pytest.param(lambda r: r.buscar_por_isbn(LIVRO_A.isbn), id="buscar_por_isbn"),
        pytest.param(lambda r: r.existe(LIVRO_A.isbn), id="existe"),
        pytest.param(lambda r: r.listar(), id="listar"),
    ],
)
def test_banco_indisponivel_gera_erro_de_persistencia(ambiente_integracao, operacao):
    ambiente_integracao.conexao.close()  # simula banco inacessível
    with pytest.raises(ErroPersistenciaError):
        operacao(ambiente_integracao.repositorio)
