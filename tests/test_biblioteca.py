"""Questão 2 – testes unitários (pytest) da Biblioteca, ainda SEM fixtures.

Repare na repetição de `Biblioteca(RepositorioMemoria())` e do cadastro em
todo teste: é o problema que as fixtures da Questão 6 resolvem.
"""
from biblioteca.biblioteca import Biblioteca
from biblioteca.repository import RepositorioMemoria

ISBN = "9780132350884"


def test_cadastrar_livro_retorna_o_livro_cadastrado():
    # Arrange
    biblioteca = Biblioteca(RepositorioMemoria())
    # Act
    livro = biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    # Assert
    assert livro.isbn == ISBN
    assert livro.quantidade == 3


def test_consultar_livro_existente():
    # Arrange
    biblioteca = Biblioteca(RepositorioMemoria())
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    # Act
    livro = biblioteca.consultar_livro(ISBN)
    # Assert
    assert livro.titulo == "Clean Code"
    assert livro.autor == "Robert C. Martin"


def test_consultar_aceita_isbn_com_hifens():
    biblioteca = Biblioteca(RepositorioMemoria())
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    assert biblioteca.consultar_livro("978-0-13-235088-4").isbn == ISBN


def test_livro_com_exemplares_esta_disponivel():
    biblioteca = Biblioteca(RepositorioMemoria())
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    assert biblioteca.verificar_disponibilidade(ISBN) is True


def test_livro_sem_exemplares_nao_esta_disponivel():
    biblioteca = Biblioteca(RepositorioMemoria())
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
    assert biblioteca.verificar_disponibilidade(ISBN) is False


def test_emprestar_livro_reduz_a_quantidade_no_repositorio():
    # Arrange
    biblioteca = Biblioteca(RepositorioMemoria())
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 2)
    # Act
    biblioteca.emprestar_livro(ISBN)
    # Assert (relê do repositório, não do objeto devolvido)
    assert biblioteca.consultar_livro(ISBN).quantidade == 1


def test_devolver_livro_aumenta_a_quantidade_no_repositorio():
    # Arrange
    biblioteca = Biblioteca(RepositorioMemoria())
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    biblioteca.emprestar_livro(ISBN)
    # Act
    biblioteca.devolver_livro(ISBN)
    # Assert
    assert biblioteca.consultar_livro(ISBN).quantidade == 1
