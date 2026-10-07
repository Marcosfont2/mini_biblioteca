"""Questão 3 – os mesmos comportamentos, agora com unittest."""
import unittest

from biblioteca.biblioteca import Biblioteca
from biblioteca.livro import Livro
from biblioteca.repository import RepositorioMemoria

ISBN = "9780132350884"


class TestCriacaoDeLivro(unittest.TestCase):
    """Funcionalidade 1: criação de livro (equivale a test_livro.py)."""

    def test_criar_livro_com_dados_validos(self):
        livro = Livro(ISBN, "Clean Code", "Robert C. Martin", 3)
        self.assertIsInstance(livro, Livro)
        self.assertIsInstance(livro.quantidade, int)
        self.assertEqual(livro.isbn, ISBN)
        self.assertEqual(livro.titulo, "Clean Code")
        self.assertEqual(livro.quantidade, 3)


class TestDisponibilidade(unittest.TestCase):
    """Funcionalidade 2: disponibilidade (usa setUp no lugar de fixture)."""

    def setUp(self):
        self.biblioteca = Biblioteca(RepositorioMemoria())
        self.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
        self.biblioteca.cadastrar_livro("9780134757599", "Refactoring", "Martin Fowler", 0)

    def test_livro_com_exemplares_esta_disponivel(self):
        self.assertTrue(self.biblioteca.verificar_disponibilidade(ISBN))

    def test_livro_sem_exemplares_nao_esta_disponivel(self):
        self.assertFalse(self.biblioteca.verificar_disponibilidade("9780134757599"))


class TestEmprestimoEDevolucao(unittest.TestCase):
    """Funcionalidade 3: empréstimo e devolução."""

    def setUp(self):
        self.biblioteca = Biblioteca(RepositorioMemoria())
        self.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 2)

    def test_emprestimo_reduz_quantidade(self):
        livro = self.biblioteca.emprestar_livro(ISBN)
        self.assertIsInstance(livro, Livro)
        self.assertEqual(livro.quantidade, 1)

    def test_devolucao_aumenta_quantidade(self):
        self.biblioteca.emprestar_livro(ISBN)
        livro = self.biblioteca.devolver_livro(ISBN)
        self.assertEqual(livro.quantidade, 2)


if __name__ == "__main__":
    unittest.main()
