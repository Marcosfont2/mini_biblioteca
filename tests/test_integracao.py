"""Questões 9, 10, 11 e 12 – testes de integração (SEM mocks).

Componentes reais envolvidos: Biblioteca + validadores + Livro + repositório
(+ SQLite real em memória, quando a fixture `ambiente_integracao` é usada).
"""
import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.database import conectar, inicializar_banco
from biblioteca.excecoes import LivroDuplicadoError
from biblioteca.livro import Livro
from biblioteca.repository import LivroRepository, RepositorioMemoria

ISBN = "9780132350884"


# ================================ Questão 9 ===================================
def test_integracao_cadastro_pesquisa_e_emprestimo():
    # Arrange: tudo real, nenhum Mock
    biblioteca = Biblioteca(RepositorioMemoria())

    # 1. cadastrar
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 2)
    # 2. pesquisar o livro cadastrado
    encontrado = biblioteca.consultar_livro(ISBN)
    assert encontrado.titulo == "Clean Code"
    # 3. confirmar que há exemplares
    assert biblioteca.verificar_disponibilidade(ISBN) is True
    assert encontrado.quantidade == 2
    # 4. emprestar
    biblioteca.emprestar_livro(ISBN)
    # 5. consultar novamente
    depois = biblioteca.consultar_livro(ISBN)
    # 6. a quantidade disponível foi reduzida
    assert depois.quantidade == 1


# ================================ Questão 10 ==================================
def test_integracao_fluxo_completo(ambiente_integracao):
    biblioteca = ambiente_integracao.biblioteca

    # cadastrar
    cadastrado = biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    assert cadastrado == Livro(ISBN, "Clean Code", "Robert C. Martin", 1)

    # consultar (o livro pode ser encontrado)
    inicial = biblioteca.consultar_livro(ISBN)
    assert inicial.titulo == "Clean Code"
    assert inicial.quantidade == 1

    # emprestar -> exemplares diminuem
    biblioteca.emprestar_livro(ISBN)
    apos_emprestimo = biblioteca.consultar_livro(ISBN)
    assert apos_emprestimo.quantidade == 0
    assert biblioteca.verificar_disponibilidade(ISBN) is False

    # devolver -> exemplares aumentam
    biblioteca.devolver_livro(ISBN)
    apos_devolucao = biblioteca.consultar_livro(ISBN)
    assert apos_devolucao.quantidade == 1

    # estado final == estado inicial
    assert apos_devolucao == inicial


# ================================ Questão 11 ==================================
def test_persistencia_cadastro_grava_linha_no_banco(ambiente_integracao):
    amb = ambiente_integracao

    amb.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)

    # consulta SQL direta, sem passar pelo repositório: o dado está mesmo no banco
    linhas = amb.conexao.execute(
        "SELECT isbn, titulo, autor, quantidade FROM livros"
    ).fetchall()
    assert linhas == [(ISBN, "Clean Code", "Robert C. Martin", 3)]


def test_persistencia_recupera_dados_iguais_aos_cadastrados(ambiente_integracao):
    amb = ambiente_integracao
    cadastrado = Livro(ISBN, "Clean Code", "Robert C. Martin", 3)

    amb.repositorio.salvar(cadastrado)                 # persistir
    recuperado = amb.repositorio.buscar_por_isbn(ISBN)  # nova consulta ao banco

    assert recuperado is not cadastrado                # veio do banco, não da memória
    assert recuperado == cadastrado                    # mas os dados são idênticos


def test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca(ambiente_integracao):
    amb = ambiente_integracao
    amb.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 2)
    amb.biblioteca.emprestar_livro(ISBN)

    # simula "reiniciar o sistema": objetos novos, mesmo banco
    outra_biblioteca = Biblioteca(LivroRepository(amb.conexao))

    assert outra_biblioteca.consultar_livro(ISBN).quantidade == 1


def test_persistencia_cadastro_duplicado_nao_cria_segunda_linha(ambiente_integracao):
    amb = ambiente_integracao
    amb.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)

    with pytest.raises(LivroDuplicadoError):
        amb.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 9)

    total = amb.conexao.execute("SELECT COUNT(*) FROM livros").fetchone()[0]
    assert total == 1
    assert amb.biblioteca.consultar_livro(ISBN).quantidade == 3


def test_persistencia_em_arquivo_sobrevive_ao_fechamento_da_conexao(tmp_path):
    # arquivo temporário: não interfere no biblioteca.db da aplicação
    caminho = tmp_path / "teste_biblioteca.db"

    primeira = conectar(str(caminho))
    inicializar_banco(primeira)
    Biblioteca(LivroRepository(primeira)).cadastrar_livro(
        ISBN, "Clean Code", "Robert C. Martin", 3
    )
    primeira.close()  # fecha tudo: só o arquivo guarda o dado

    segunda = conectar(str(caminho))  # reabre
    try:
        livro = Biblioteca(LivroRepository(segunda)).consultar_livro(ISBN)
        assert livro == Livro(ISBN, "Clean Code", "Robert C. Martin", 3)
    finally:
        segunda.close()
