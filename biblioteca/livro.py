"""Entidade Livro: dados + regras de estoque de um único título."""
from dataclasses import dataclass

from biblioteca.excecoes import SemExemplaresError
from biblioteca.validators import (
    validar_autor,
    validar_isbn,
    validar_quantidade,
    validar_titulo,
)


@dataclass
class Livro:
    isbn: str
    titulo: str
    autor: str
    quantidade: int  # exemplares disponíveis

    def __post_init__(self):
        self.isbn = validar_isbn(self.isbn)
        self.titulo = validar_titulo(self.titulo)
        self.autor = validar_autor(self.autor)
        self.quantidade = validar_quantidade(self.quantidade)

    @property
    def disponivel(self):
        return self.quantidade > 0

    def emprestar(self):
        if not self.disponivel:
            raise SemExemplaresError(
                f"Não há exemplares disponíveis de '{self.titulo}'."
            )
        self.quantidade -= 1

    def devolver(self):
        self.quantidade += 1
