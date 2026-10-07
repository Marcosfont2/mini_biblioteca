"""Questão 5 – testes de exceções (pytest.raises e assertRaises)."""
import unittest

import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.excecoes import (
    DadosInvalidosError,
    LivroDuplicadoError,
    LivroNaoEncontradoError,
    SemExemplaresError,
)
from biblioteca.repository import RepositorioMemoria

ISBN = "9780132350884"
OUTRO_ISBN = "9780134757599"


# 1. cadastro com dados inválidos --------------------------------------------
@pytest.mark.parametrize(
    "isbn, titulo, autor, quantidade",
    [
        pytest.param("123", "Clean Code", "Robert C. Martin", 1, id="isbn-curto"),
        pytest.param(ISBN, "", "Robert C. Martin", 1, id="titulo-vazio"),
        pytest.param(ISBN, "Clean Code", "   ", 1, id="autor-so-espacos"),
        pytest.param(ISBN, "Clean Code", "Robert C. Martin", -1, id="quantidade-negativa"),
        pytest.param(ISBN, "Clean Code", "Robert C. Martin", "3", id="quantidade-texto"),
    ],
)
def test_cadastro_com_dados_invalidos(biblioteca, isbn, titulo, autor, quantidade):
    with pytest.raises(DadosInvalidosError):
        biblioteca.cadastrar_livro(isbn, titulo, autor, quantidade)


def test_cadastro_invalido_nao_grava_nada(biblioteca, repositorio):
    with pytest.raises(DadosInvalidosError):
        biblioteca.cadastrar_livro(ISBN, "", "Robert C. Martin", 1)
    assert repositorio.listar() == []


# 2. cadastro duplicado -----------------------------------------------------
def test_cadastro_duplicado(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    with pytest.raises(LivroDuplicadoError, match="já cadastrado"):
        biblioteca.cadastrar_livro(ISBN, "Outro Título", "Outro Autor", 5)


def test_cadastro_duplicado_preserva_o_livro_original(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    with pytest.raises(LivroDuplicadoError):
        biblioteca.cadastrar_livro(ISBN, "Outro Título", "Outro Autor", 5)
    assert biblioteca.consultar_livro(ISBN).titulo == "Clean Code"


# 3. empréstimo de livro inexistente -----------------------------------------
def test_emprestimo_de_livro_inexistente(biblioteca):
    with pytest.raises(LivroNaoEncontradoError):
        biblioteca.emprestar_livro(OUTRO_ISBN)


# 4. empréstimo com quantidade zero ------------------------------------------
def test_emprestimo_sem_exemplares(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
    with pytest.raises(SemExemplaresError, match="Clean Code"):
        biblioteca.emprestar_livro(ISBN)


def test_emprestimo_sem_exemplares_nao_deixa_estoque_negativo(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
    with pytest.raises(SemExemplaresError):
        biblioteca.emprestar_livro(ISBN)
    assert biblioteca.consultar_livro(ISBN).quantidade == 0


# 5. devolução de livro inexistente ------------------------------------------
def test_devolucao_de_livro_inexistente(biblioteca):
    with pytest.raises(LivroNaoEncontradoError):
        biblioteca.devolver_livro(OUTRO_ISBN)


# Versão unittest (assertRaises) -------------------------------------------
class TestExcecoesUnittest(unittest.TestCase):
    def setUp(self):
        self.biblioteca = Biblioteca(RepositorioMemoria())

    def test_emprestimo_de_livro_inexistente(self):
        with self.assertRaises(LivroNaoEncontradoError):
            self.biblioteca.emprestar_livro(OUTRO_ISBN)

    def test_emprestimo_sem_exemplares_e_mensagem(self):
        self.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
        with self.assertRaises(SemExemplaresError) as contexto:
            self.biblioteca.emprestar_livro(ISBN)
        self.assertIn("Clean Code", str(contexto.exception))
