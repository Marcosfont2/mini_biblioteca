"""Funções de validação dos dados de um livro.

Cada função valida e devolve o valor já normalizado, ou lança
DadosInvalidosError.
"""
import re

from biblioteca.excecoes import DadosInvalidosError

_PADRAO_ISBN = re.compile(r"\d{13}|\d{9}[\dX]")


def validar_isbn(isbn):
    """ISBN-10 ou ISBN-13 (hífens/espaços são aceitos e removidos)."""
    if not isinstance(isbn, str):
        raise DadosInvalidosError("O ISBN deve ser um texto.")
    normalizado = isbn.replace("-", "").replace(" ", "").upper()
    if not _PADRAO_ISBN.fullmatch(normalizado):
        raise DadosInvalidosError(
            f"ISBN inválido: {isbn!r}. Use 10 ou 13 dígitos."
        )
    return normalizado


def _validar_texto(valor, campo):
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidosError(f"O {campo} deve ser um texto não vazio.")
    return valor.strip()


def validar_titulo(titulo):
    return _validar_texto(titulo, "título")


def validar_autor(autor):
    return _validar_texto(autor, "autor")


def validar_quantidade(quantidade):
    """Inteiro >= 0 (bool é rejeitado, embora seja subclasse de int)."""
    if isinstance(quantidade, bool) or not isinstance(quantidade, int):
        raise DadosInvalidosError("A quantidade deve ser um número inteiro.")
    if quantidade < 0:
        raise DadosInvalidosError("A quantidade não pode ser negativa.")
    return quantidade
