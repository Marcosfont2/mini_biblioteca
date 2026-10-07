"""Serviço de biblioteca: regras de negócio sobre cadastro, empréstimo e devolução."""
from biblioteca.excecoes import LivroDuplicadoError, LivroNaoEncontradoError
from biblioteca.livro import Livro
from biblioteca.validators import validar_isbn


class Biblioteca:
    def __init__(self, repositorio):
        self._repositorio = repositorio

    def cadastrar_livro(self, isbn, titulo, autor, quantidade):
        livro = Livro(isbn, titulo, autor, quantidade)  # valida os dados
        if self._repositorio.existe(livro.isbn):
            raise LivroDuplicadoError(f"ISBN já cadastrado: {livro.isbn}")
        self._repositorio.salvar(livro)
        return livro

    def consultar_livro(self, isbn):
        isbn_normalizado = validar_isbn(isbn)
        livro = self._repositorio.buscar_por_isbn(isbn_normalizado)
        if livro is None:
            raise LivroNaoEncontradoError(f"ISBN não encontrado: {isbn_normalizado}")
        return livro

    def verificar_disponibilidade(self, isbn):
        return self.consultar_livro(isbn).disponivel

    def emprestar_livro(self, isbn):
        livro = self.consultar_livro(isbn)
        livro.emprestar()
        self._repositorio.atualizar(livro)
        return livro

    def devolver_livro(self, isbn):
        livro = self.consultar_livro(isbn)
        livro.devolver()
        self._repositorio.atualizar(livro)
        return livro
