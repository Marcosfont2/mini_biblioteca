"""Questão 4 – parametrização, classes de equivalência e valores-limite."""
import pytest

from biblioteca.excecoes import DadosInvalidosError, SemExemplaresError
from biblioteca.livro import Livro
from biblioteca.validators import (
    validar_autor,
    validar_isbn,
    validar_quantidade,
    validar_titulo,
)

# ------------------------------------------------ Regra 1: quantidade >= 0
# Partições: inválida (< 0) | válida (>= 0). Limite entre elas: -1 | 0.
# Também testamos o vizinho superior do limite (1), um valor nominal (2),
# um valor grande e entradas de tipo errado (outra classe inválida).
@pytest.mark.parametrize(
    "entrada",
    [
        pytest.param(0, id="LIMITE-valida-0"),
        pytest.param(1, id="LIMITE+1-valida-1"),
        pytest.param(2, id="nominal-valida-2"),
        pytest.param(10_000, id="valida-grande"),
    ],
)
def test_quantidade_valida(entrada):
    assert validar_quantidade(entrada) == entrada


@pytest.mark.parametrize(
    "entrada",
    [
        pytest.param(-1, id="LIMITE-1-invalida-menos1"),
        pytest.param(-2, id="invalida-menos2"),
        pytest.param(-1000, id="invalida-muito-negativa"),
        pytest.param(1.5, id="tipo-invalido-float"),
        pytest.param("2", id="tipo-invalido-str"),
        pytest.param(True, id="tipo-invalido-bool"),
        pytest.param(None, id="tipo-invalido-None"),
    ],
)
def test_quantidade_invalida(entrada):
    with pytest.raises(DadosInvalidosError):
        validar_quantidade(entrada)


# ------------------------------------------------------ Regra 2: formato do ISBN
@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("9780132350884", "9780132350884"),        # ISBN-13 puro
        ("978-0-13-235088-4", "9780132350884"),    # com hífens
        ("978 0 13 235088 4", "9780132350884"),    # com espaços
        ("0306406152", "0306406152"),              # ISBN-10
        ("080442957x", "080442957X"),              # ISBN-10 terminado em x
    ],
)
def test_isbn_valido_e_normalizado(entrada, esperado):
    assert validar_isbn(entrada) == esperado


@pytest.mark.parametrize(
    "entrada",
    [
        "",                  # vazio
        "123456789",         # 9 dígitos  (limite: tamanho 10 - 1)
        "12345678901",       # 11 dígitos (entre 10 e 13)
        "978013235088",      # 12 dígitos (limite: 13 - 1)
        "97801323508845",    # 14 dígitos (limite: 13 + 1)
        "97801323508AB",     # letras no meio
        "ISBN-INVALIDO",
        None,
        9780132350884,       # int, não str
    ],
)
def test_isbn_invalido(entrada):
    with pytest.raises(DadosInvalidosError):
        validar_isbn(entrada)


# ------------------------------------------ Regra 3: empréstimo x estoque
# (estoque inicial, deve funcionar?, estoque final esperado)
@pytest.mark.parametrize(
    "estoque, deve_emprestar, estoque_final",
    [
        pytest.param(2, True, 1, id="nominal-2"),
        pytest.param(1, True, 0, id="LIMITE-ultimo-exemplar"),
        pytest.param(0, False, 0, id="LIMITE-sem-exemplares"),
    ],
)
def test_regra_de_emprestimo_por_estoque(estoque, deve_emprestar, estoque_final):
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", estoque)
    if deve_emprestar:
        livro.emprestar()
    else:
        with pytest.raises(SemExemplaresError):
            livro.emprestar()
    assert livro.quantidade == estoque_final


# -------------------------------------------- Regra 4: título e autor não vazios
@pytest.mark.parametrize("funcao", [validar_titulo, validar_autor])
@pytest.mark.parametrize("entrada", ["", "   ", "\t\n", None, 123])
def test_texto_obrigatorio_invalido(funcao, entrada):
    with pytest.raises(DadosInvalidosError):
        funcao(entrada)
