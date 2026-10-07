"""Questão 2 – testes unitários (pytest) da entidade Livro. Padrão AAA explícito."""
from biblioteca.livro import Livro


def test_criar_livro_com_dados_validos():
    # Arrange
    isbn, titulo, autor, quantidade = "9780132350884", "Clean Code", "Robert C. Martin", 3
    # Act
    livro = Livro(isbn, titulo, autor, quantidade)
    # Assert
    assert livro.isbn == "9780132350884"
    assert livro.titulo == "Clean Code"
    assert livro.autor == "Robert C. Martin"
    assert livro.quantidade == 3


def test_isbn_com_hifens_e_normalizado():
    # Arrange
    isbn_com_hifens = "978-0-13-235088-4"
    # Act
    livro = Livro(isbn_com_hifens, "Clean Code", "Robert C. Martin", 1)
    # Assert
    assert livro.isbn == "9780132350884"


def test_titulo_e_autor_tem_espacos_removidos():
    # Arrange / Act
    livro = Livro("9780132350884", "  Clean Code  ", " Robert C. Martin ", 1)
    # Assert
    assert livro.titulo == "Clean Code"
    assert livro.autor == "Robert C. Martin"


def test_quantidade_de_exemplares_e_inteira():
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 5)
    assert isinstance(livro.quantidade, int)
    assert livro.quantidade == 5


def test_livro_com_exemplares_esta_disponivel():
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 1)
    assert livro.disponivel is True


def test_livro_sem_exemplares_nao_esta_disponivel():
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 0)
    assert livro.disponivel is False


def test_emprestar_reduz_um_exemplar():
    # Arrange
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    # Act
    livro.emprestar()
    # Assert
    assert livro.quantidade == 2


def test_devolver_aumenta_um_exemplar():
    # Arrange
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 0)
    # Act
    livro.devolver()
    # Assert
    assert livro.quantidade == 1
    assert livro.disponivel is True
