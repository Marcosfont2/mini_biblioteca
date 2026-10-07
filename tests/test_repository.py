"""Testes do repositório SQLite contra um banco REAL em memória (":memory:")."""
import pytest

from biblioteca.excecoes import LivroDuplicadoError, LivroNaoEncontradoError
from biblioteca.livro import Livro


def test_salvar_e_buscar_devolve_livro_igual(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)

    repo.salvar(livro)

    assert repo.buscar_por_isbn("9780132350884") == livro


def test_buscar_isbn_inexistente_retorna_none(ambiente_integracao):
    assert ambiente_integracao.repositorio.buscar_por_isbn("9780132350884") is None


def test_existe(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    assert repo.existe("9780132350884") is False
    repo.salvar(Livro("9780132350884", "Clean Code", "Robert C. Martin", 3))
    assert repo.existe("9780132350884") is True


def test_salvar_isbn_duplicado_lanca_erro(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    repo.salvar(livro)
    with pytest.raises(LivroDuplicadoError):
        repo.salvar(livro)


def test_atualizar_altera_a_quantidade(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    repo.salvar(livro)
    livro.emprestar()

    repo.atualizar(livro)

    assert repo.buscar_por_isbn(livro.isbn).quantidade == 2


def test_atualizar_livro_inexistente_lanca_erro(ambiente_integracao):
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    with pytest.raises(LivroNaoEncontradoError):
        ambiente_integracao.repositorio.atualizar(livro)
