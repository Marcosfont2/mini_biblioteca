"""Questão 6 – reutilização de fixtures (definidas em conftest.py)."""
import pytest

from biblioteca.excecoes import SemExemplaresError


# --- livro_disponivel (usada em 3 testes) ------------------------------------
def test_livro_disponivel_esta_disponivel(livro_disponivel):
    assert livro_disponivel.disponivel is True


def test_livro_disponivel_pode_ser_emprestado(livro_disponivel):
    livro_disponivel.emprestar()
    assert livro_disponivel.quantidade == 1


def test_livro_disponivel_emprestado_duas_vezes_fica_indisponivel(livro_disponivel):
    livro_disponivel.emprestar()
    livro_disponivel.emprestar()
    assert livro_disponivel.disponivel is False


# --- livro_indisponivel (usada em 3 testes) --------------------------------
def test_livro_indisponivel_nao_esta_disponivel(livro_indisponivel):
    assert livro_indisponivel.disponivel is False


def test_livro_indisponivel_bloqueia_emprestimo(livro_indisponivel):
    with pytest.raises(SemExemplaresError):
        livro_indisponivel.emprestar()


def test_livro_indisponivel_volta_a_ficar_disponivel_apos_devolucao(livro_indisponivel):
    livro_indisponivel.devolver()
    assert livro_indisponivel.disponivel is True


# --- livro + biblioteca (fixtures compostas: biblioteca depende de repositorio)
def test_biblioteca_cadastra_e_consulta_livro_da_fixture(biblioteca, livro):
    biblioteca.cadastrar_livro(livro.isbn, livro.titulo, livro.autor, livro.quantidade)
    assert biblioteca.consultar_livro(livro.isbn) == livro


def test_biblioteca_empresta_livro_da_fixture(biblioteca, livro):
    biblioteca.cadastrar_livro(livro.isbn, livro.titulo, livro.autor, livro.quantidade)
    biblioteca.emprestar_livro(livro.isbn)
    assert biblioteca.consultar_livro(livro.isbn).quantidade == livro.quantidade - 1


def test_cada_teste_recebe_um_repositorio_novo(repositorio):
    # a fixture é recriada a cada teste: nenhum livro "vaza" de outro teste
    assert repositorio.listar() == []
