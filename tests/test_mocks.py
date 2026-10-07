"""Questões 7 e 8 – isolamento de dependências com Mock/patch e side_effect.

Unidade testada: Biblioteca (regras de negócio).
Dependência isolada: o repositório (LivroRepository), que no sistema real
acessa o SQLite. Aqui nenhum banco é criado.
"""
from unittest.mock import create_autospec, patch

import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.excecoes import (
    ErroPersistenciaError,
    LivroDuplicadoError,
)
from biblioteca.livro import Livro
from biblioteca.repository import LivroRepository

ISBN = "9780132350884"


@pytest.fixture
def repo_mock():
    """Dublê do repositório: tem exatamente a interface de LivroRepository."""
    return create_autospec(LivroRepository, instance=True)


# ============================== Questão 7 ====================================
def test_cadastrar_livro_novo_consulta_existencia_e_salva(repo_mock):
    # Arrange
    repo_mock.existe.return_value = False          # return_value configurado
    biblioteca = Biblioteca(repo_mock)
    # Act
    livro = biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    # Assert – comportamento: quem foi chamado, quantas vezes e com quê
    repo_mock.existe.assert_called_once_with(ISBN)
    repo_mock.salvar.assert_called_once_with(livro)


def test_cadastrar_livro_duplicado_nao_chama_salvar(repo_mock):
    repo_mock.existe.return_value = True
    biblioteca = Biblioteca(repo_mock)
    with pytest.raises(LivroDuplicadoError):
        biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    repo_mock.salvar.assert_not_called()


def test_consultar_livro_devolve_o_que_o_repositorio_retorna(repo_mock):
    esperado = Livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    repo_mock.buscar_por_isbn.return_value = esperado
    biblioteca = Biblioteca(repo_mock)

    resultado = biblioteca.consultar_livro(ISBN)

    assert resultado is esperado
    repo_mock.buscar_por_isbn.assert_called_once_with(ISBN)


def test_emprestar_persiste_o_livro_atualizado(repo_mock):
    livro = Livro(ISBN, "Clean Code", "Robert C. Martin", 2)
    repo_mock.buscar_por_isbn.return_value = livro
    biblioteca = Biblioteca(repo_mock)

    biblioteca.emprestar_livro(ISBN)

    assert livro.quantidade == 1
    repo_mock.atualizar.assert_called_once_with(livro)


@patch("biblioteca.biblioteca.validar_isbn")
def test_consultar_usa_o_isbn_normalizado_pelo_validador(mock_validar, repo_mock):
    # patch substitui a função validar_isbn *dentro do módulo biblioteca.biblioteca*
    mock_validar.return_value = "ISBN-NORMALIZADO"
    repo_mock.buscar_por_isbn.return_value = Livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    biblioteca = Biblioteca(repo_mock)

    biblioteca.consultar_livro("entrada qualquer")

    mock_validar.assert_called_once_with("entrada qualquer")
    repo_mock.buscar_por_isbn.assert_called_once_with("ISBN-NORMALIZADO")


# ============================== Questão 8 ====================================
def test_disponibilidade_com_respostas_sucessivas_do_repositorio(repo_mock):
    """SITUAÇÃO NORMAL: o repositório responde diferente a cada chamada."""
    repo_mock.buscar_por_isbn.side_effect = [
        Livro(ISBN, "Clean Code", "Robert C. Martin", 1),   # 1ª chamada: há exemplar
        Livro(ISBN, "Clean Code", "Robert C. Martin", 0),   # 2ª chamada: acabou
    ]
    biblioteca = Biblioteca(repo_mock)

    assert biblioteca.verificar_disponibilidade(ISBN) is True
    assert biblioteca.verificar_disponibilidade(ISBN) is False
    assert repo_mock.buscar_por_isbn.call_count == 2


def test_cadastro_propaga_falha_do_repositorio(repo_mock):
    """SITUAÇÃO DE FALHA: o banco falha ao salvar."""
    repo_mock.existe.return_value = False
    repo_mock.salvar.side_effect = ErroPersistenciaError("Falha simulada do banco")
    biblioteca = Biblioteca(repo_mock)

    with pytest.raises(ErroPersistenciaError, match="Falha simulada"):
        biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)

    repo_mock.salvar.assert_called_once()


def test_emprestimo_propaga_falha_ao_atualizar(repo_mock):
    """SITUAÇÃO DE FALHA: a leitura funciona, mas gravar o empréstimo falha."""
    repo_mock.buscar_por_isbn.return_value = Livro(ISBN, "Clean Code", "Robert C. Martin", 2)
    repo_mock.atualizar.side_effect = ErroPersistenciaError("disco cheio")
    biblioteca = Biblioteca(repo_mock)

    with pytest.raises(ErroPersistenciaError, match="disco cheio"):
        biblioteca.emprestar_livro(ISBN)
