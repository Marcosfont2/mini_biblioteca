# Atividade Avaliativa – Unidade I
## Desenvolvimento e Teste de um Mini Sistema de Biblioteca

| | |
|---|---|
| **Disciplina** | Testes de Software I |
| **Curso** | Ciência da Computação |
| **Aluno(a)** | _(preencher)_ |
| **Matrícula** | _(preencher)_ |
| **Data de entrega** | _(preencher)_ |

> **Como ler este documento.** Para cada questão o texto segue a ordem pedida no enunciado: **(1) objetivo do teste → (2) código desenvolvido → (3) resultado da execução → (4) interpretação**. Todas as saídas de terminal abaixo foram geradas executando o projeto (Python 3.12, pytest 9.1, pytest-cov 7.1), não foram digitadas à mão.

**Resultado final da suíte:** `111 passed` · **Cobertura:** `100%` (era 93% antes da Questão 14).

---

## Visão geral do projeto

```text
mini_biblioteca/
├── README.md
├── biblioteca
│   ├── __init__.py
│   ├── biblioteca.py
│   ├── database.py
│   ├── excecoes.py
│   ├── livro.py
│   ├── repository.py
│   └── validators.py
├── pytest.ini
├── relatorio_cobertura.txt
├── requirements.txt
└── tests
    ├── __init__.py
    ├── conftest.py
    ├── test_biblioteca.py
    ├── test_cobertura_extra.py
    ├── test_excecoes.py
    ├── test_fixtures.py
    ├── test_integracao.py
    ├── test_livro.py
    ├── test_mocks.py
    ├── test_repository.py
    ├── test_unittest_biblioteca.py
    └── test_validadores.py
```

**Como executar** (a partir da pasta `mini_biblioteca/`):

```bash
pip install -r requirements.txt
python -m pytest -v                       # toda a suíte (pytest + unittest)
python -m pytest --cov=biblioteca         # cobertura
python -m unittest discover -s tests -p "test_*.py" -v   # só os testes escritos em unittest
```

**Arquitetura em camadas** (a seta significa "depende de"):

```text
        testes
          │
          ▼
   ┌──────────────┐     ┌────────────┐
   │  Biblioteca  │────▶│ validators │   regras de formato (ISBN, título…)
   │ (serviço)    │     └────────────┘
   │              │     ┌────────────┐
   │              │────▶│   Livro    │   dados + regra de estoque
   └──────┬───────┘     └────────────┘
          │ usa (injeção de dependência)
          ▼
   ┌───────────────────┐        ┌────────────────┐
   │ RepositorioMemoria│   ou   │ LivroRepository│──▶ database.py ──▶ SQLite
   └───────────────────┘        └────────────────┘
```

A `Biblioteca` **recebe** o repositório pelo construtor. Essa decisão de projeto é o que torna o sistema testável: nos testes unitários o repositório pode ser trocado por um *mock*; nos testes de integração, por um repositório real (memória ou SQLite).

---

# PARTE I – TESTES UNITÁRIOS

## Questão 1 – Construção e organização inicial do sistema

### 1. Objetivo
Ter um código organizado, com responsabilidades separadas, em que seja claro **o que** será testado. Sem essa separação, não há "unidade" a isolar.

### 2. Código desenvolvido

**(a) Estrutura de diretórios:** ver a árvore na "Visão geral". Código da aplicação em `biblioteca/`, código de teste em `tests/`.

**(b) Código:**

`biblioteca/excecoes.py`
```python
"""Exceções do domínio da biblioteca."""


class BibliotecaError(Exception):
    """Classe base de todas as exceções do sistema."""


class DadosInvalidosError(BibliotecaError, ValueError):
    """Dados de entrada inválidos (ISBN, título, autor ou quantidade)."""


class LivroDuplicadoError(BibliotecaError):
    """Tentativa de cadastrar um ISBN que já existe."""


class LivroNaoEncontradoError(BibliotecaError):
    """Operação sobre um ISBN que não está cadastrado."""


class SemExemplaresError(BibliotecaError):
    """Empréstimo solicitado sem exemplares disponíveis."""


class ErroPersistenciaError(BibliotecaError):
    """Falha ao acessar o mecanismo de armazenamento."""
```

`biblioteca/validators.py`
```python
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
```

`biblioteca/livro.py`
```python
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
```

`biblioteca/repository.py`
```python
"""Repositórios: camada responsável por armazenar e recuperar livros."""
import sqlite3
from dataclasses import replace

from biblioteca.excecoes import (
    ErroPersistenciaError,
    LivroDuplicadoError,
    LivroNaoEncontradoError,
)
from biblioteca.livro import Livro


class RepositorioMemoria:
    """Repositório em dicionário (sem persistência). Guarda cópias dos livros."""

    def __init__(self):
        self._livros = {}

    def salvar(self, livro):
        if livro.isbn in self._livros:
            raise LivroDuplicadoError(f"ISBN já cadastrado: {livro.isbn}")
        self._livros[livro.isbn] = replace(livro)

    def atualizar(self, livro):
        if livro.isbn not in self._livros:
            raise LivroNaoEncontradoError(f"ISBN não encontrado: {livro.isbn}")
        self._livros[livro.isbn] = replace(livro)

    def buscar_por_isbn(self, isbn):
        livro = self._livros.get(isbn)
        return replace(livro) if livro else None

    def existe(self, isbn):
        return isbn in self._livros

    def listar(self):
        return [replace(self._livros[i]) for i in sorted(self._livros)]


class LivroRepository:
    """Repositório SQLite. Recebe a conexão pronta (injeção de dependência)."""

    def __init__(self, conexao):
        self._conexao = conexao

    # --- auxiliares: convertem erros do sqlite3 em erro do domínio ---
    def _escrever(self, sql, parametros, acao):
        try:
            with self._conexao:  # commit/rollback automático
                return self._conexao.execute(sql, parametros).rowcount
        except sqlite3.Error as erro:
            raise ErroPersistenciaError(f"Falha ao {acao}: {erro}") from erro

    def _ler(self, sql, parametros, acao):
        try:
            return self._conexao.execute(sql, parametros).fetchall()
        except sqlite3.Error as erro:
            raise ErroPersistenciaError(f"Falha ao {acao}: {erro}") from erro

    # --- operações públicas ---
    def salvar(self, livro):
        try:
            with self._conexao:
                self._conexao.execute(
                    "INSERT INTO livros (isbn, titulo, autor, quantidade) "
                    "VALUES (?, ?, ?, ?)",
                    (livro.isbn, livro.titulo, livro.autor, livro.quantidade),
                )
        except sqlite3.IntegrityError as erro:
            raise LivroDuplicadoError(f"ISBN já cadastrado: {livro.isbn}") from erro
        except sqlite3.Error as erro:
            raise ErroPersistenciaError(f"Falha ao salvar: {erro}") from erro

    def atualizar(self, livro):
        alteradas = self._escrever(
            "UPDATE livros SET titulo = ?, autor = ?, quantidade = ? WHERE isbn = ?",
            (livro.titulo, livro.autor, livro.quantidade, livro.isbn),
            "atualizar livro",
        )
        if alteradas == 0:
            raise LivroNaoEncontradoError(f"ISBN não encontrado: {livro.isbn}")

    def buscar_por_isbn(self, isbn):
        linhas = self._ler(
            "SELECT isbn, titulo, autor, quantidade FROM livros WHERE isbn = ?",
            (isbn,),
            "buscar livro",
        )
        return Livro(*linhas[0]) if linhas else None

    def existe(self, isbn):
        linhas = self._ler(
            "SELECT 1 FROM livros WHERE isbn = ?", (isbn,), "verificar existência"
        )
        return bool(linhas)

    def listar(self):
        linhas = self._ler(
            "SELECT isbn, titulo, autor, quantidade FROM livros ORDER BY isbn",
            (),
            "listar livros",
        )
        return [Livro(*linha) for linha in linhas]
```

`biblioteca/database.py`
```python
"""Conexão e esquema do banco SQLite."""
import sqlite3

CAMINHO_PADRAO = "biblioteca.db"  # banco real da aplicação

ESQUEMA = """
CREATE TABLE IF NOT EXISTS livros (
    isbn       TEXT PRIMARY KEY,
    titulo     TEXT NOT NULL,
    autor      TEXT NOT NULL,
    quantidade INTEGER NOT NULL CHECK (quantidade >= 0)
)
"""


def conectar(caminho=CAMINHO_PADRAO):
    """Abre uma conexão. Os testes passam ':memory:' para não tocar no banco real."""
    return sqlite3.connect(caminho)


def inicializar_banco(conexao):
    with conexao:
        conexao.execute(ESQUEMA)
```

`biblioteca/biblioteca.py`
```python
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
```

**(c) Responsabilidade de cada módulo, classe e função**

| Módulo | Elemento | Responsabilidade |
|---|---|---|
| `excecoes.py` | `BibliotecaError` | Classe-base: permite capturar qualquer erro do domínio de uma vez. |
| | `DadosInvalidosError` | Dado de entrada inválido. Também herda de `ValueError`, o que é natural para "valor inválido". |
| | `LivroDuplicadoError` | ISBN já cadastrado. |
| | `LivroNaoEncontradoError` | Operação sobre ISBN inexistente. |
| | `SemExemplaresError` | Empréstimo com estoque zero. |
| | `ErroPersistenciaError` | Falha do mecanismo de armazenamento (ex.: banco inacessível). |
| `validators.py` | `validar_isbn` | Aceita ISBN-10/13, remove hífens/espaços, normaliza para maiúsculas e devolve o ISBN limpo. |
| | `validar_titulo`, `validar_autor` | Texto não vazio (remove espaços nas pontas). Usam o auxiliar `_validar_texto`. |
| | `validar_quantidade` | Inteiro `>= 0`; rejeita `float`, `str`, `None` e `bool`. |
| `livro.py` | `Livro` | Entidade com `isbn`, `titulo`, `autor`, `quantidade`. Valida tudo ao ser criada (`__post_init__`). |
| | `Livro.disponivel` | `True` se `quantidade > 0`. |
| | `Livro.emprestar()` | Diminui 1 exemplar; lança `SemExemplaresError` se não houver. |
| | `Livro.devolver()` | Aumenta 1 exemplar. |
| `repository.py` | `RepositorioMemoria` | Armazena livros num dicionário (guarda **cópias**, como um banco faria). |
| | `LivroRepository` | Armazena livros no SQLite: `salvar`, `atualizar`, `buscar_por_isbn`, `existe`, `listar`. Traduz erros do `sqlite3` para erros do domínio. |
| `database.py` | `conectar`, `inicializar_banco`, `ESQUEMA` | Abre a conexão (o caminho é parâmetro) e cria a tabela `livros`. |
| `biblioteca.py` | `Biblioteca` | Regras de negócio: `cadastrar_livro`, `consultar_livro`, `verificar_disponibilidade`, `emprestar_livro`, `devolver_livro`. Não sabe *como* os dados são guardados. |

### 3. Resultado da execução
Importar e usar o sistema manualmente (smoke test):

```text
>>> b = Biblioteca(RepositorioMemoria())
>>> b.cadastrar_livro('9780132350884', 'Clean Code', 'Robert C. Martin', 1)
>>> print(b.emprestar_livro('978-0-13-235088-4'))
Livro(isbn='9780132350884', titulo='Clean Code', autor='Robert C. Martin', quantidade=0)
```

### 4. Interpretação
O sistema cumpre todas as operações mínimas do enunciado. A separação em camadas é a decisão mais importante para os testes: a regra de estoque mora em `Livro`, as regras de cadastro/busca em `Biblioteca`, e a gravação em repositórios. **Analogia:** é uma cozinha com estações separadas (corte, fogão, empratamento). Se o prato sai ruim, você sabe qual estação inspecionar; numa cozinha onde uma só pessoa faz tudo, qualquer teste teria de olhar o prato inteiro.

---

## Questão 2 – Primeiros testes unitários com pytest

### 1. Objetivo
Verificar, isoladamente, as operações principais: criar livro, ISBN, título, autor, quantidade, cadastro, consulta, disponibilidade, empréstimo e devolução. Cada teste segue o padrão **Arrange–Act–Assert (AAA)**:

```text
 ARRANGE            ACT               ASSERT
 prepara o     ─▶   executa a    ─▶   compara com o
 cenário            operação          resultado esperado
```

### 2. Código desenvolvido
`tests/test_livro.py` (os comentários `# Arrange`, `# Act` e `# Assert` marcam as linhas de cada fase em `test_criar_livro_com_dados_validos`, `test_isbn_com_hifens_e_normalizado`, `test_emprestar_reduz_um_exemplar` e `test_devolver_aumenta_um_exemplar`):
```python
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
```

`tests/test_biblioteca.py` (AAA marcado em quatro testes):
```python
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
```

### 3. Resultado da execução
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 15 items

tests/test_livro.py::test_criar_livro_com_dados_validos PASSED
tests/test_livro.py::test_isbn_com_hifens_e_normalizado PASSED
tests/test_livro.py::test_titulo_e_autor_tem_espacos_removidos PASSED
tests/test_livro.py::test_quantidade_de_exemplares_e_inteira PASSED
tests/test_livro.py::test_livro_com_exemplares_esta_disponivel PASSED
tests/test_livro.py::test_livro_sem_exemplares_nao_esta_disponivel PASSED
tests/test_livro.py::test_emprestar_reduz_um_exemplar PASSED
tests/test_livro.py::test_devolver_aumenta_um_exemplar PASSED
tests/test_biblioteca.py::test_cadastrar_livro_retorna_o_livro_cadastrado PASSED
tests/test_biblioteca.py::test_consultar_livro_existente PASSED
tests/test_biblioteca.py::test_consultar_aceita_isbn_com_hifens PASSED
tests/test_biblioteca.py::test_livro_com_exemplares_esta_disponivel PASSED
tests/test_biblioteca.py::test_livro_sem_exemplares_nao_esta_disponivel PASSED
tests/test_biblioteca.py::test_emprestar_livro_reduz_a_quantidade_no_repositorio PASSED
tests/test_biblioteca.py::test_devolver_livro_aumenta_a_quantidade_no_repositorio PASSED

============================== 15 passed in 0.02s ==============================
```

### 4. Interpretação
Todos passaram: cada operação se comporta como especificado. Dois cuidados de desenho:

- Em `test_emprestar_livro_reduz_a_quantidade_no_repositorio` o *Assert* **relê o livro do repositório** em vez de olhar o objeto devolvido. Assim o teste confirma que a mudança foi realmente gravada, não só mudada em memória.
- Esses testes de `Biblioteca` usam um `RepositorioMemoria` real (um repositório simples, sem banco). Isso os torna rápidos, mas não são isolamento total. O isolamento estrito, com *mock*, é o tema da Questão 7.

Note também a repetição de `Biblioteca(RepositorioMemoria())` e do cadastro inicial em quase todo teste. Isso é de propósito: é o problema que a Questão 6 resolve.

---

## Questão 3 – Testes utilizando unittest

### 1. Objetivo
Reescrever três funcionalidades já testadas com pytest, agora no `unittest`: **(1) criação de livro, (2) disponibilidade, (3) empréstimo e devolução**. O objetivo do teste é o mesmo; muda a estrutura do framework.

### 2. Código desenvolvido
`tests/test_unittest_biblioteca.py`:
```python
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
```

### 3. Resultado da execução
Comando: `python -m unittest discover -s tests -p "test_unittest*.py" -v`
```text
test_criar_livro_com_dados_validos (test_unittest_biblioteca.TestCriacaoDeLivro.test_criar_livro_com_dados_validos) ... ok
test_livro_com_exemplares_esta_disponivel (test_unittest_biblioteca.TestDisponibilidade.test_livro_com_exemplares_esta_disponivel) ... ok
test_livro_sem_exemplares_nao_esta_disponivel (test_unittest_biblioteca.TestDisponibilidade.test_livro_sem_exemplares_nao_esta_disponivel) ... ok
test_devolucao_aumenta_quantidade (test_unittest_biblioteca.TestEmprestimoEDevolucao.test_devolucao_aumenta_quantidade) ... ok
test_emprestimo_reduz_quantidade (test_unittest_biblioteca.TestEmprestimoEDevolucao.test_emprestimo_reduz_quantidade) ... ok

----------------------------------------------------------------------
Ran 5 tests in 0.000s

OK
```

### 4. Interpretação e diferença entre pytest e unittest
Os recursos pedidos foram usados: `assertEqual` (valores), `assertTrue`/`assertFalse` (disponibilidade) e `assertIsInstance` (tipos). `setUp()` recria a biblioteca antes de **cada** teste, evitando que um teste contamine outro.

**Principal diferença observada:**

| | pytest | unittest |
|---|---|---|
| Estrutura | Funções simples `def test_x():` | Classe que herda de `unittest.TestCase`, com métodos `test_x(self)` |
| Verificação | O `assert` do próprio Python (`assert a == b`) | Métodos específicos: `self.assertEqual(a, b)`, `assertTrue`, … |
| Preparação | *Fixtures* injetadas por nome de parâmetro | `setUp()` / `tearDown()` na classe |
| Mensagem de falha | Mostra a expressão e os valores reintrospectados (ex.: `assert 3 == 2`) | Mostra a mensagem do método de asserção (ex.: `3 != 2`) |

Resumindo: pytest exige **menos código cerimonial** e lê quase como Python comum; unittest é mais verboso, porém vem na biblioteca padrão (nenhuma instalação) e impõe uma estrutura uniforme. Os dois coexistem no mesmo projeto, e o pytest também executa testes escritos em unittest.

---

## Questão 4 – Parametrização, classes de equivalência e valores-limite

### 1. Objetivo
Executar o **mesmo raciocínio de teste** com vários dados, escolhidos por técnica e não por palpite. Foram parametrizadas quatro regras (o enunciado pedia duas, uma delas sobre a quantidade de exemplares):

1. **Quantidade de exemplares** (obrigatória): inteiro `>= 0`.
2. **Formato do ISBN**: 10 ou 13 caracteres úteis, com normalização.
3. **Empréstimo × estoque**: com estoque `>= 1` empresta; com `0` bloqueia.
4. **Título e autor**: texto não vazio.

### 2. Código desenvolvido

**Critério de seleção dos dados.**
- **Classes de equivalência:** dividi as entradas em grupos que o sistema deve tratar do mesmo jeito. Basta um representante por grupo.
- **Análise de valores-limite:** os defeitos costumam morar na fronteira entre grupos (`>` vs `>=`, `< 0` vs `<= 0`). Por isso testo o valor de cada lado da fronteira.

**Tabela da regra 1 – quantidade (valores `-1`, `0`, `1` e `2` do enunciado + extras):**

| Entrada | Classe | Resultado esperado |
|---|---|---|
| `-2` | inválida (negativa) | `DadosInvalidosError` |
| `-1` | **limite** inválido (logo abaixo do mínimo) | `DadosInvalidosError` |
| `0` | **limite** válido (menor valor aceito) | aceita → `0` |
| `1` | **limite+1** válido | aceita → `1` |
| `2` | válida (nominal) | aceita → `2` |
| `10000` | válida (grande) | aceita → `10000` |
| `1.5`, `"2"`, `None` | inválida (tipo errado) | `DadosInvalidosError` |
| `True` | inválida (tipo errado: `bool` é `int` em Python, mas não é uma quantidade) | `DadosInvalidosError` |

```text
 quantidade:  … -2   -1  │  0    1    2   …   10000
              └─ inválida ─┘└────── válida ───────────▶
                      limite: -1 | 0
```

**Tabela da regra 3 – empréstimo × estoque:**

| Estoque | Classe | Resultado esperado |
|---|---|---|
| `2` | válida nominal | empresta; estoque final `1` |
| `1` | limite (último exemplar) | empresta; estoque final `0` |
| `0` | limite (sem exemplares) | `SemExemplaresError`; estoque continua `0` |

**Tabela da regra 2 – ISBN (comprimentos):** `9` dígitos (inválido, limite −1), `10` (válido), `11` e `12` (inválidos), `13` (válido), `14` (inválido, limite +1), além de letras no meio, vazio, `None` e `int`.

`tests/test_validadores.py`:
```python
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
```

### 3. Resultado da execução
Testes parametrizados da quantidade (cada linha = um caso; o *id* indica a classe):
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 38 items / 27 deselected / 11 selected

tests/test_validadores.py::test_quantidade_valida[LIMITE-valida-0] PASSED
tests/test_validadores.py::test_quantidade_valida[LIMITE+1-valida-1] PASSED
tests/test_validadores.py::test_quantidade_valida[nominal-valida-2] PASSED
tests/test_validadores.py::test_quantidade_valida[valida-grande] PASSED
tests/test_validadores.py::test_quantidade_invalida[LIMITE-1-invalida-menos1] PASSED
tests/test_validadores.py::test_quantidade_invalida[invalida-menos2] PASSED
tests/test_validadores.py::test_quantidade_invalida[invalida-muito-negativa] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-float] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-str] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-bool] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-None] PASSED

====================== 11 passed, 27 deselected in 0.02s =======================
```

### 4. Interpretação
Cada `pytest.param(..., id=...)` vira um teste independente com nome legível. Se um caso falhar, o relatório diz exatamente qual (por exemplo, `LIMITE-1-invalida-menos1`), em vez de um genérico "o teste da quantidade falhou". O par `-1 | 0` é o mais valioso: pegaria o erro clássico de escrever `quantidade <= 0` no lugar de `< 0`, que um teste só com `5` jamais notaria.

---

## Questão 5 – Testando exceções

### 1. Objetivo
Garantir que situações inválidas **sejam rejeitadas** com a exceção correta:

| Cenário | Exceção esperada |
|---|---|
| Cadastro com dados inválidos | `DadosInvalidosError` |
| Cadastro duplicado | `LivroDuplicadoError` |
| Empréstimo de livro inexistente | `LivroNaoEncontradoError` |
| Empréstimo com quantidade zero | `SemExemplaresError` |
| Devolução de livro inexistente | `LivroNaoEncontradoError` |

### 2. Código desenvolvido
As regras foram implementadas na Questão 1 (módulos `livro.py`, `validators.py`, `biblioteca.py`). Os testes, com `pytest.raises()` e, ao final do arquivo, com `assertRaises()`:

`tests/test_excecoes.py`:
```python
"""Questão 5 – testes de exceções (pytest.raises e assertRaises)."""
import unittest

import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.excecoes import (
    DadosInvalidosError,
    LivroDuplicadoError,
    LivroNaoEncontradoError,
    SemExemplaresError,
)
from biblioteca.repository import RepositorioMemoria

ISBN = "9780132350884"
OUTRO_ISBN = "9780134757599"


# 1. cadastro com dados inválidos --------------------------------------------
@pytest.mark.parametrize(
    "isbn, titulo, autor, quantidade",
    [
        pytest.param("123", "Clean Code", "Robert C. Martin", 1, id="isbn-curto"),
        pytest.param(ISBN, "", "Robert C. Martin", 1, id="titulo-vazio"),
        pytest.param(ISBN, "Clean Code", "   ", 1, id="autor-so-espacos"),
        pytest.param(ISBN, "Clean Code", "Robert C. Martin", -1, id="quantidade-negativa"),
        pytest.param(ISBN, "Clean Code", "Robert C. Martin", "3", id="quantidade-texto"),
    ],
)
def test_cadastro_com_dados_invalidos(biblioteca, isbn, titulo, autor, quantidade):
    with pytest.raises(DadosInvalidosError):
        biblioteca.cadastrar_livro(isbn, titulo, autor, quantidade)


def test_cadastro_invalido_nao_grava_nada(biblioteca, repositorio):
    with pytest.raises(DadosInvalidosError):
        biblioteca.cadastrar_livro(ISBN, "", "Robert C. Martin", 1)
    assert repositorio.listar() == []


# 2. cadastro duplicado -----------------------------------------------------
def test_cadastro_duplicado(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    with pytest.raises(LivroDuplicadoError, match="já cadastrado"):
        biblioteca.cadastrar_livro(ISBN, "Outro Título", "Outro Autor", 5)


def test_cadastro_duplicado_preserva_o_livro_original(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 1)
    with pytest.raises(LivroDuplicadoError):
        biblioteca.cadastrar_livro(ISBN, "Outro Título", "Outro Autor", 5)
    assert biblioteca.consultar_livro(ISBN).titulo == "Clean Code"


# 3. empréstimo de livro inexistente -----------------------------------------
def test_emprestimo_de_livro_inexistente(biblioteca):
    with pytest.raises(LivroNaoEncontradoError):
        biblioteca.emprestar_livro(OUTRO_ISBN)


# 4. empréstimo com quantidade zero ------------------------------------------
def test_emprestimo_sem_exemplares(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
    with pytest.raises(SemExemplaresError, match="Clean Code"):
        biblioteca.emprestar_livro(ISBN)


def test_emprestimo_sem_exemplares_nao_deixa_estoque_negativo(biblioteca):
    biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
    with pytest.raises(SemExemplaresError):
        biblioteca.emprestar_livro(ISBN)
    assert biblioteca.consultar_livro(ISBN).quantidade == 0


# 5. devolução de livro inexistente ------------------------------------------
def test_devolucao_de_livro_inexistente(biblioteca):
    with pytest.raises(LivroNaoEncontradoError):
        biblioteca.devolver_livro(OUTRO_ISBN)


# Versão unittest (assertRaises) -------------------------------------------
class TestExcecoesUnittest(unittest.TestCase):
    def setUp(self):
        self.biblioteca = Biblioteca(RepositorioMemoria())

    def test_emprestimo_de_livro_inexistente(self):
        with self.assertRaises(LivroNaoEncontradoError):
            self.biblioteca.emprestar_livro(OUTRO_ISBN)

    def test_emprestimo_sem_exemplares_e_mensagem(self):
        self.biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 0)
        with self.assertRaises(SemExemplaresError) as contexto:
            self.biblioteca.emprestar_livro(ISBN)
        self.assertIn("Clean Code", str(contexto.exception))
```

### 3. Resultado da execução
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 14 items

tests/test_excecoes.py::test_cadastro_com_dados_invalidos[isbn-curto] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[titulo-vazio] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[autor-so-espacos] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[quantidade-negativa] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[quantidade-texto] PASSED
tests/test_excecoes.py::test_cadastro_invalido_nao_grava_nada PASSED
tests/test_excecoes.py::test_cadastro_duplicado PASSED
tests/test_excecoes.py::test_cadastro_duplicado_preserva_o_livro_original PASSED
tests/test_excecoes.py::test_emprestimo_de_livro_inexistente PASSED
tests/test_excecoes.py::test_emprestimo_sem_exemplares PASSED
tests/test_excecoes.py::test_emprestimo_sem_exemplares_nao_deixa_estoque_negativo PASSED
tests/test_excecoes.py::test_devolucao_de_livro_inexistente PASSED
tests/test_excecoes.py::TestExcecoesUnittest::test_emprestimo_de_livro_inexistente PASSED
tests/test_excecoes.py::TestExcecoesUnittest::test_emprestimo_sem_exemplares_e_mensagem PASSED

============================== 14 passed in 0.02s ==============================
```

### 4. Interpretação
**Por que receber a exceção esperada é sucesso?** Um teste verifica se o sistema se comporta **como especificado**. A especificação diz "impedir empréstimo sem exemplares" e "impedir operações quando o livro não existe". Impedir significa recusar de forma explícita. Logo, a exceção é o comportamento correto e a **ausência** dela é o defeito. O `with pytest.raises(X)` inverte a lógica: se `X` for lançada o teste passa; se nada for lançado, falha com `DID NOT RAISE`; se outra exceção for lançada, ela escapa e o teste também falha.

**Analogia:** é o teste do alarme de incêndio. O alarme soar diante de fumaça é o resultado certo. Se ele ficasse mudo, é aí que o teste reprovaria.

Os testes vão além de "lançou": verificam também o **efeito colateral**. Um cadastro inválido não grava nada; um duplicado preserva o livro original; um empréstimo recusado não deixa o estoque negativo. O `match="..."` e o `assertIn(..., str(contexto.exception))` confirmam que a mensagem identifica o problema.

---

## Questão 6 – Utilização de fixtures

### 1. Objetivo
Eliminar a repetição de preparação (Arrange) compartilhando objetos prontos entre testes.

### 2. Código desenvolvido
Fixtures criadas em `tests/conftest.py` (o pytest as descobre automaticamente, sem `import`). As de interesse desta questão são `livro`, `livro_disponivel`, `livro_indisponivel`, `repositorio` e `biblioteca`; a `ambiente_integracao` é da Questão 12:

```python
"""Fixtures compartilhadas (Questão 6) e ambiente de integração (Questão 12)."""
from dataclasses import dataclass
import sqlite3

import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.database import conectar, inicializar_banco
from biblioteca.livro import Livro
from biblioteca.repository import LivroRepository, RepositorioMemoria


# ---------------------------------------------------------------- Questão 6
@pytest.fixture
def livro():
    """Livro válido com 3 exemplares."""
    return Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)


@pytest.fixture
def livro_disponivel():
    """Livro com 2 exemplares (pode ser emprestado)."""
    return Livro("9780134757599", "Refactoring", "Martin Fowler", 2)


@pytest.fixture
def livro_indisponivel():
    """Livro com 0 exemplares (empréstimo deve ser bloqueado)."""
    return Livro("9780135957059", "The Pragmatic Programmer", "Andrew Hunt", 0)


@pytest.fixture
def repositorio():
    return RepositorioMemoria()


@pytest.fixture
def biblioteca(repositorio):
    return Biblioteca(repositorio)
```

Uso das fixtures (`tests/test_fixtures.py`):
```python
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
```

| Fixture | Usada em (exemplos) | Nº de testes em `test_fixtures.py` |
|---|---|---|
| `livro_disponivel` | disponibilidade, empréstimo, esgotar o estoque | 3 |
| `livro_indisponivel` | indisponibilidade, bloqueio do empréstimo, devolução | 3 |
| `livro` | cadastro + consulta, cadastro + empréstimo | 2 |
| `repositorio` | teste de isolamento; também alimenta `biblioteca` | 1 direto + todos que usam `biblioteca` |
| `biblioteca` | cadastro/consulta/empréstimo e todo o `test_excecoes.py` | 2 aqui + dezenas em `test_excecoes.py` |

### 3. Resultado da execução
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 9 items

tests/test_fixtures.py::test_livro_disponivel_esta_disponivel PASSED
tests/test_fixtures.py::test_livro_disponivel_pode_ser_emprestado PASSED
tests/test_fixtures.py::test_livro_disponivel_emprestado_duas_vezes_fica_indisponivel PASSED
tests/test_fixtures.py::test_livro_indisponivel_nao_esta_disponivel PASSED
tests/test_fixtures.py::test_livro_indisponivel_bloqueia_emprestimo PASSED
tests/test_fixtures.py::test_livro_indisponivel_volta_a_ficar_disponivel_apos_devolucao PASSED
tests/test_fixtures.py::test_biblioteca_cadastra_e_consulta_livro_da_fixture PASSED
tests/test_fixtures.py::test_biblioteca_empresta_livro_da_fixture PASSED
tests/test_fixtures.py::test_cada_teste_recebe_um_repositorio_novo PASSED

============================== 9 passed in 0.01s ===============================
```

### 4. Interpretação
**Repetição eliminada.** Na Questão 2, quase todo teste de `Biblioteca` começava com:

```python
biblioteca = Biblioteca(RepositorioMemoria())                      # montar o serviço
biblioteca.cadastrar_livro(ISBN, "Clean Code", "Robert C. Martin", 3)  # montar o dado
```

e todo teste de livro repetia `Livro("9780132350884", "Clean Code", ...)`. Agora essa preparação existe **uma vez** em `conftest.py`. Se um dia o construtor de `Biblioteca` mudar, edita-se um só lugar, e não dezenas de testes.

Outros pontos:
- As fixtures são **recriadas a cada teste**. O último teste do arquivo confirma que o repositório chega vazio, então nenhum livro "vaza" entre testes (isso evita testes que só passam numa certa ordem).
- `biblioteca` **depende de** `repositorio`: o pytest resolve a cadeia sozinho (composição de fixtures).
- O nome da fixture é o próprio parâmetro do teste, o que deixa o *Arrange* visível na assinatura.

---

## Questão 7 – Isolamento de dependências com Mock/Patch

### 1. Objetivo
Testar **somente a lógica de `Biblioteca`**, sem que um repositório real (e muito menos um banco) participe. A dependência isolada é o **repositório** (`LivroRepository`), que é quem toca o SQLite.

### 2. Código desenvolvido
`tests/test_mocks.py`, parte da Questão 7 (as importações e a fixture `repo_mock` vêm antes):

```python
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
```

### 3. Resultado da execução
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 8 items

tests/test_mocks.py::test_cadastrar_livro_novo_consulta_existencia_e_salva PASSED
tests/test_mocks.py::test_cadastrar_livro_duplicado_nao_chama_salvar PASSED
tests/test_mocks.py::test_consultar_livro_devolve_o_que_o_repositorio_retorna PASSED
tests/test_mocks.py::test_emprestar_persiste_o_livro_atualizado PASSED
tests/test_mocks.py::test_consultar_usa_o_isbn_normalizado_pelo_validador PASSED
tests/test_mocks.py::test_disponibilidade_com_respostas_sucessivas_do_repositorio PASSED
tests/test_mocks.py::test_cadastro_propaga_falha_do_repositorio PASSED
tests/test_mocks.py::test_emprestimo_propaga_falha_ao_atualizar PASSED

============================== 8 passed in 0.07s ===============================
```

### 4. Interpretação
- **`create_autospec(LivroRepository, instance=True)`** cria um dublê que tem exatamente os métodos da classe real. Se o código chamar `repo.salvr(...)` (erro de digitação) ou usar argumentos incompatíveis, o teste falha. Um `Mock()` comum aceitaria tudo.
- **`return_value`** é configurado em `existe`, `buscar_por_isbn` etc. para controlar o que a dependência "responde".
- **`assert_called_once_with(...)`** verifica o **comportamento de colaboração**: `Biblioteca` consultou `existe` uma vez com o ISBN certo e depois chamou `salvar` com o livro criado. `assert_not_called()` prova que um cadastro duplicado **não** chega a gravar.
- **`@patch("biblioteca.biblioteca.validar_isbn")`** substitui a função *no módulo onde ela é usada* (e não onde foi definida), e prova que o ISBN devolvido pelo validador é o que chega ao repositório.

**Por que continua sendo um teste unitário mesmo com dependências no código original?** Porque o que define uma unidade testada é o **que está sob avaliação**, não a ausência de dependências no código. Aqui a unidade é `Biblioteca`; seu colaborador foi trocado por um dublê controlado. Assim: (a) o teste não cria banco nem usa disco, e roda em milissegundos; (b) só falha se a lógica de `Biblioteca` estiver errada, nunca por defeito do SQLite; (c) é determinístico. **Analogia:** é testar o piloto automático de um avião num simulador de voo, sem precisar de um avião real nem de céu aberto.

---

## Questão 8 – Comportamentos diferentes da dependência

### 1. Objetivo
Usar `side_effect` para a mesma dependência (o **repositório**) se comportar de maneiras distintas: uma **normal** (respostas sucessivas) e outra de **falha**.

### 2. Código desenvolvido
Parte da Questão 8 em `tests/test_mocks.py`:

```python
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
```

**Dependência simulada:** o repositório (`buscar_por_isbn`, `salvar` e `atualizar`).

**Por que simular?** Provocar de verdade uma falha de disco ou um banco que responde diferente a cada chamada é difícil, lento e não repetível. Com `side_effect` isso vira uma linha de código, e o resultado é sempre o mesmo.

**Resultado esperado em cada cenário:**

| Cenário | Configuração da dependência | Resultado esperado |
|---|---|---|
| Normal | `buscar_por_isbn.side_effect = [livro(qtd=1), livro(qtd=0)]` | 1ª verificação → `True`; 2ª → `False`; repositório chamado 2 vezes |
| Falha ao salvar | `salvar.side_effect = ErroPersistenciaError("Falha simulada do banco")` | `cadastrar_livro` propaga `ErroPersistenciaError`; `salvar` foi chamado 1 vez |
| Falha ao atualizar | `atualizar.side_effect = ErroPersistenciaError("disco cheio")` | `emprestar_livro` propaga `ErroPersistenciaError` |

### 3. Resultado da execução
Os mesmos testes da saída da Questão 7 (arquivo `test_mocks.py`); os de `side_effect` são:

```text
tests/test_mocks.py::test_disponibilidade_com_respostas_sucessivas_do_repositorio PASSED
tests/test_mocks.py::test_cadastro_propaga_falha_do_repositorio PASSED
tests/test_mocks.py::test_emprestimo_propaga_falha_ao_atualizar PASSED
```

### 4. Interpretação
Uma lista em `side_effect` entrega um valor por chamada, o que simula uma dependência cujo estado muda com o tempo. Uma **exceção** em `side_effect` simula a falha. O teste mostra que `Biblioteca` **não engole** o erro: ele sobe para quem chamou, que é o comportamento desejado, porque o chamador precisa saber que a operação não foi concluída. Esse caminho de falha dificilmente seria exercitado num teste com banco real.

---

# PARTE II – TESTES DE INTEGRAÇÃO

```text
 TESTE UNITÁRIO                         TESTE DE INTEGRAÇÃO
 ┌───────────┐   ┌─────────┐            ┌───────────┐   ┌───────────┐   ┌────────┐
 │Biblioteca │──▶│  MOCK   │            │Biblioteca │──▶│Repositório│──▶│ SQLite │
 └───────────┘   └─────────┘            └───────────┘   └───────────┘   └────────┘
  unidade real + dependência falsa       tudo real, o resultado final é observado
```

## Questão 9 – Primeiro teste de integração

### 1. Objetivo
Verificar o fluxo **cadastrar → pesquisar → confirmar disponibilidade → emprestar → consultar de novo → estoque reduzido**, sem nenhum mock. Componentes reais: `Biblioteca`, `validators`, `Livro` e `RepositorioMemoria`.

```text
cadastrar ─▶ consultar ─▶ disponível? ─▶ emprestar ─▶ consultar ─▶ quantidade -1
```

### 2. Código desenvolvido
`tests/test_integracao.py` (início do arquivo e Questão 9):

```python
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
```

### 3. Resultado da execução
```text
tests/test_integracao.py::test_integracao_cadastro_pesquisa_e_emprestimo PASSED
```

### 4. Interpretação
O teste passa, então a saída de cada componente é aceita corretamente pelo seguinte: o `Livro` criado pelo cadastro é aceito pelo repositório, o repositório devolve algo que `consultar_livro` entende, e a mudança de estoque feita em `Livro.emprestar()` chega ao repositório via `atualizar`. Note que o teste usa **apenas a API pública** da `Biblioteca`, como um usuário real faria.

---

## Questão 10 – Integração do fluxo completo

### 1. Objetivo
Acompanhar o ciclo completo: **cadastrar → consultar → emprestar → consultar → devolver → consultar**, confirmando em cada etapa o estado esperado e que o estado final é igual ao inicial.

### 2. Código desenvolvido
```python
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
```

### 3. Resultado da execução
```text
tests/test_integracao.py::test_integracao_fluxo_completo PASSED
```

### 4. Interpretação
**Componentes integrados neste teste** (todos reais):

```text
 Biblioteca ─▶ validators ─▶ Livro ─▶ LivroRepository ─▶ database.py ─▶ SQLite (:memory:)
```

Verificações feitas: o livro é cadastrado com os dados corretos (comparação de igualdade com um `Livro` esperado); pode ser encontrado; o estoque **diminui** após o empréstimo (`1 → 0`) e a disponibilidade vira `False`; **aumenta** após a devolução (`0 → 1`); e o estado final é idêntico ao inicial (`apos_devolucao == inicial`). Essa última verificação garante que empréstimo e devolução são operações inversas, sem efeitos colaterais (por exemplo, título ou autor alterados sem querer).

---

## Questão 11 – Teste de integração com persistência

### 1. Objetivo
Provar que os dados foram **efetivamente armazenados e recuperados**, e não apenas que `salvar()` foi chamado. Fluxo: inicializar banco → cadastrar → persistir → **nova consulta** → recuperar → comparar.

```text
 cadastrar ─▶ salvar (INSERT) ─▶ ler novamente (SELECT) ─▶ comparar com o original
```

### 2. Código desenvolvido
A persistência usa **SQLite** (`database.py` + `LivroRepository`, já mostrados na Questão 1). O banco dos testes é `":memory:"`, que existe só durante a conexão. Há ainda um teste com arquivo temporário (`tmp_path`). Em ambos os casos o `biblioteca.db` da aplicação **não é tocado**, porque o caminho do banco é um parâmetro de `conectar()`.

```python
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
```

Testes do repositório contra o banco real em memória (`tests/test_repository.py`):
```python
"""Testes do repositório SQLite contra um banco REAL em memória (":memory:")."""
import pytest

from biblioteca.excecoes import LivroDuplicadoError, LivroNaoEncontradoError
from biblioteca.livro import Livro


def test_salvar_e_buscar_devolve_livro_igual(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)

    repo.salvar(livro)

    assert repo.buscar_por_isbn("9780132350884") == livro


def test_buscar_isbn_inexistente_retorna_none(ambiente_integracao):
    assert ambiente_integracao.repositorio.buscar_por_isbn("9780132350884") is None


def test_existe(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    assert repo.existe("9780132350884") is False
    repo.salvar(Livro("9780132350884", "Clean Code", "Robert C. Martin", 3))
    assert repo.existe("9780132350884") is True


def test_salvar_isbn_duplicado_lanca_erro(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    repo.salvar(livro)
    with pytest.raises(LivroDuplicadoError):
        repo.salvar(livro)


def test_atualizar_altera_a_quantidade(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    repo.salvar(livro)
    livro.emprestar()

    repo.atualizar(livro)

    assert repo.buscar_por_isbn(livro.isbn).quantidade == 2


def test_atualizar_livro_inexistente_lanca_erro(ambiente_integracao):
    livro = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
    with pytest.raises(LivroNaoEncontradoError):
        ambiente_integracao.repositorio.atualizar(livro)
```

### 3. Resultado da execução
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 13 items

tests/test_integracao.py::test_integracao_cadastro_pesquisa_e_emprestimo PASSED
tests/test_integracao.py::test_integracao_fluxo_completo PASSED
tests/test_integracao.py::test_persistencia_cadastro_grava_linha_no_banco PASSED
tests/test_integracao.py::test_persistencia_recupera_dados_iguais_aos_cadastrados PASSED
tests/test_integracao.py::test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca PASSED
tests/test_integracao.py::test_persistencia_cadastro_duplicado_nao_cria_segunda_linha PASSED
tests/test_integracao.py::test_persistencia_em_arquivo_sobrevive_ao_fechamento_da_conexao PASSED
tests/test_repository.py::test_salvar_e_buscar_devolve_livro_igual PASSED
tests/test_repository.py::test_buscar_isbn_inexistente_retorna_none PASSED
tests/test_repository.py::test_existe PASSED
tests/test_repository.py::test_salvar_isbn_duplicado_lanca_erro PASSED
tests/test_repository.py::test_atualizar_altera_a_quantidade PASSED
tests/test_repository.py::test_atualizar_livro_inexistente_lanca_erro PASSED

============================== 13 passed in 0.02s ==============================
```

### 4. Interpretação
- `test_persistencia_cadastro_grava_linha_no_banco` consulta o banco com **SQL direto**, sem passar pelo repositório: prova independente de que a linha existe.
- `test_persistencia_recupera_dados_iguais_aos_cadastrados` usa `recuperado is not cadastrado` + `recuperado == cadastrado`. O primeiro confirma que o objeto veio **do banco** e não da memória; o segundo, que os **dados** são idênticos (a comparação de igualdade vem do `@dataclass`).
- O teste de "nova instância" simula reiniciar o sistema: objetos novos, mesmo banco, e o estoque continua refletindo o empréstimo.
- O teste de arquivo **fecha** a conexão e abre outra: só o arquivo guardou o dado. É o análogo de desligar e religar o computador.
- O duplicado confirma que a falha **não deixa lixo**: continua havendo 1 linha, com o valor original (3).

Um mock de `salvar()` jamais descobriria problemas como esquema errado, falta de `commit`, ordem das colunas ou tipo incorreto. Aqui, qualquer um deles reprovaria o teste.

---

## Questão 12 – Fixture para testes de integração

### 1. Objetivo
Preparar e **desmontar** automaticamente o ambiente (banco, tabela, repositório e biblioteca) de cada teste de integração.

### 2. Código desenvolvido
```python
"""Fixtures compartilhadas (Questão 6) e ambiente de integração (Questão 12)."""
from dataclasses import dataclass
import sqlite3

import pytest

from biblioteca.biblioteca import Biblioteca
from biblioteca.database import conectar, inicializar_banco
from biblioteca.livro import Livro
from biblioteca.repository import LivroRepository, RepositorioMemoria


# ---------------------------------------------------------------- Questão 6
@pytest.fixture
def livro():
    """Livro válido com 3 exemplares."""
    return Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)


@pytest.fixture
def livro_disponivel():
    """Livro com 2 exemplares (pode ser emprestado)."""
    return Livro("9780134757599", "Refactoring", "Martin Fowler", 2)


@pytest.fixture
def livro_indisponivel():
    """Livro com 0 exemplares (empréstimo deve ser bloqueado)."""
    return Livro("9780135957059", "The Pragmatic Programmer", "Andrew Hunt", 0)


@pytest.fixture
def repositorio():
    return RepositorioMemoria()


@pytest.fixture
def biblioteca(repositorio):
    return Biblioteca(repositorio)


# --------------------------------------------------------------- Questão 12
@dataclass
class Ambiente:
    conexao: sqlite3.Connection
    repositorio: LivroRepository
    biblioteca: Biblioteca


@pytest.fixture
def ambiente_integracao():
    # SETUP: banco SQLite em memória + tabela + repositório + biblioteca reais
    conexao = conectar(":memory:")
    inicializar_banco(conexao)
    repositorio = LivroRepository(conexao)
    yield Ambiente(conexao, repositorio, Biblioteca(repositorio))
    # TEARDOWN: fecha a conexão (o banco em memória deixa de existir)
    conexao.close()
```

Usada em: `test_integracao_fluxo_completo`, `test_persistencia_cadastro_grava_linha_no_banco`, `test_persistencia_recupera_dados_iguais_aos_cadastrados`, `test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca`, `test_persistencia_cadastro_duplicado_nao_cria_segunda_linha` e em todos os testes de `test_repository.py`.

### 3. Resultado da execução
Comando: `python -m pytest --setup-show tests/test_integracao.py -k "fluxo_completo or grava_linha"`
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collected 7 items / 5 deselected / 2 selected

tests/test_integracao.py 
        SETUP    F ambiente_integracao
        tests/test_integracao.py::test_integracao_fluxo_completo (fixtures used: ambiente_integracao) .
        TEARDOWN F ambiente_integracao
        SETUP    F ambiente_integracao
        tests/test_integracao.py::test_persistencia_cadastro_grava_linha_no_banco (fixtures used: ambiente_integracao) .
        TEARDOWN F ambiente_integracao

======================= 2 passed, 5 deselected in 0.01s ========================
```

### 4. Interpretação
A saída mostra o ciclo `SETUP → teste → TEARDOWN` repetido **para cada teste**:

- **Setup (antes do `yield`):** abre um SQLite em memória, cria a tabela `livros`, monta `LivroRepository` e `Biblioteca`, e entrega tudo num objeto `Ambiente`. Cada teste começa, portanto, com um banco **vazio e novo**.
- **Execução do teste:** acontece no ponto do `yield`: o pytest pausa a fixture, roda o teste usando o valor entregue e só depois retoma a fixture.
- **Teardown (depois do `yield`):** fecha a conexão. O banco em memória deixa de existir, então nada sobra para o próximo teste. O teardown roda **mesmo se o teste falhar**, evitando vazamento de recursos.

**Analogia:** é montar e desmontar o palco antes e depois de cada apresentação: o próximo artista nunca encontra os cenários do anterior.

---

## Questão 13 – Investigação de falhas

### 1. Objetivo
Demonstrar que a suíte **detecta** um defeito, e não apenas exibe `PASSED`. Esta técnica é chamada de **teste de mutação manual**.

### 2. Código desenvolvido
**Erro introduzido:** em `Livro.emprestar()`, o empréstimo deixa de diminuir o estoque (uma das mutações sugeridas no enunciado).

```diff
@@ -32,7 +32,7 @@ class Livro:
             raise SemExemplaresError(
                 f"Não há exemplares disponíveis de '{self.titulo}'."
             )
-        self.quantidade -= 1
+        pass  # ERRO PROPOSITAL: não diminui o estoque
 
     def devolver(self):
         self.quantidade += 1
```

### 3. Resultado da execução
Resumo da execução com o defeito presente:
```text
FAILED tests/test_biblioteca.py::test_emprestar_livro_reduz_a_quantidade_no_repositorio
FAILED tests/test_biblioteca.py::test_devolver_livro_aumenta_a_quantidade_no_repositorio
FAILED tests/test_fixtures.py::test_livro_disponivel_pode_ser_emprestado - As...
FAILED tests/test_fixtures.py::test_livro_disponivel_emprestado_duas_vezes_fica_indisponivel
FAILED tests/test_fixtures.py::test_biblioteca_empresta_livro_da_fixture - As...
FAILED tests/test_integracao.py::test_integracao_cadastro_pesquisa_e_emprestimo
FAILED tests/test_integracao.py::test_integracao_fluxo_completo - AssertionEr...
FAILED tests/test_integracao.py::test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca
FAILED tests/test_livro.py::test_emprestar_reduz_um_exemplar - AssertionError...
FAILED tests/test_mocks.py::test_emprestar_persiste_o_livro_atualizado - Asse...
FAILED tests/test_repository.py::test_atualizar_altera_a_quantidade - Asserti...
FAILED tests/test_unittest_biblioteca.py::TestEmprestimoEDevolucao::test_devolucao_aumenta_quantidade
FAILED tests/test_unittest_biblioteca.py::TestEmprestimoEDevolucao::test_emprestimo_reduz_quantidade
FAILED tests/test_validadores.py::test_regra_de_emprestimo_por_estoque[nominal-2]
FAILED tests/test_validadores.py::test_regra_de_emprestimo_por_estoque[LIMITE-ultimo-exemplar]
15 failed, 87 passed in 0.16s
```

Mensagem do framework para o teste mais direto (`test_livro.py::test_emprestar_reduz_um_exemplar`):
```text
F                                                                        [100%]
=================================== FAILURES ===================================
_______________________ test_emprestar_reduz_um_exemplar _______________________
tests/test_livro.py:56: in test_emprestar_reduz_um_exemplar
    assert livro.quantidade == 2
E   AssertionError: assert 3 == 2
E    +  where 3 = Livro(isbn='9780132350884', titulo='Clean Code', autor='Robert C. Martin', quantidade=3).quantidade
=========================== short test summary info ============================
FAILED tests/test_livro.py::test_emprestar_reduz_um_exemplar - AssertionError...
1 failed in 0.01s
```

### 4. Interpretação
**Teste que detectou o problema:** `test_emprestar_reduz_um_exemplar` (e outros 14).

**Interpretação da mensagem:** `assert 3 == 2` lê-se "o valor **obtido** (3) é diferente do **esperado** (2)". O pytest ainda mostra o objeto completo (`Livro(..., quantidade=3)`) e a linha exata do `assert` (`tests/test_livro.py:56`). O estoque ficou em 3 depois de um empréstimo, então a operação que deveria diminuí-lo não está fazendo isso. O ponto a inspecionar é `Livro.emprestar()`.

**Correção realizada:** restaurar a linha `self.quantidade -= 1`. Depois disso: `102 passed` (na época; hoje, 111).

**Defeito detectado em várias camadas.** A mesma falha foi pega por testes unitários (`test_livro`, `test_unittest`, `test_validadores`), por testes com mock (`test_emprestar_persiste_o_livro_atualizado`), por testes de repositório e por testes de integração. Isso é desejável: se uma camada tivesse um furo, outra ainda avisaria.

**Outras mutações testadas** (cada uma aplicada, a suíte executada, e o código restaurado):

| Mutação | Resultado da suíte |
|---|---|
| Devolver soma 2 | `4 failed, 98 passed in 0.13s` |
| Permite emprestar com estoque zero | `5 failed, 97 passed in 0.19s` |
| Consulta isbn incorreto | `23 failed, 79 passed in 0.30s` |

Nenhuma mutação sobreviveu (todas reprovaram ao menos 4 testes), indicando que a suíte tem poder de detecção real.

---

## Questão 14 – Cobertura de testes

### 1. Objetivo
Medir quais linhas do código são exercitadas pelos testes, achar lacunas, preenchê-las e comparar. Comando: `python -m pytest --cov=biblioteca --cov-report=term-missing`.

### 2. Código desenvolvido

**Passo 1 – cobertura inicial** (suíte das Questões 1–13, 102 testes):
```text
........................................................................ [ 70%]
..............................                                           [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
biblioteca/__init__.py         0      0   100%
biblioteca/biblioteca.py      30      0   100%
biblioteca/database.py         8      0   100%
biblioteca/excecoes.py         6      0   100%
biblioteca/livro.py           23      0   100%
biblioteca/repository.py      57     10    82%   21, 26, 51-52, 57-58, 71-72, 98-103
biblioteca/validators.py      24      0   100%
--------------------------------------------------------
TOTAL                        148     10    93%
102 passed in 0.26s
```

**Passo 2 – análise do relatório.** O módulo de menor cobertura é `repository.py` (**82%**; 10 linhas sem teste). Mapeando as linhas (`Missing`) para o código:

| Linhas | O que faz | Comportamento importante não testado |
|---|---|---|
| 21 | `RepositorioMemoria.salvar` lança `LivroDuplicadoError` | duplicado no repositório em memória |
| 26 | `RepositorioMemoria.atualizar` lança `LivroNaoEncontradoError` | atualizar livro inexistente em memória |
| 51-52, 57-58, 71-72 | `except sqlite3.Error` → `ErroPersistenciaError` | **banco inacessível / falha do SQLite** |
| 98-103 | `LivroRepository.listar()` | listagem ordenada por ISBN |

O mais importante é a falha de banco: é justamente o comportamento que torna o sistema confiável quando algo dá errado, e nenhum teste o exercitava.

**Passo 3 – novos testes** (`tests/test_cobertura_extra.py`):
```python
"""Questão 14 – testes adicionados APÓS analisar o relatório de cobertura.

O relatório inicial mostrou repository.py com 82%: faltavam os caminhos de erro
do repositório SQLite (falhas de banco), o listar() do SQLite e as exceções do
repositório em memória.
"""
import pytest

from biblioteca.excecoes import (
    ErroPersistenciaError,
    LivroDuplicadoError,
    LivroNaoEncontradoError,
)
from biblioteca.livro import Livro
from biblioteca.repository import RepositorioMemoria

LIVRO_A = Livro("9780132350884", "Clean Code", "Robert C. Martin", 3)
LIVRO_B = Livro("9780134757599", "Refactoring", "Martin Fowler", 2)


# --- repositório em memória: exceções que não eram exercitadas -----------------
def test_repositorio_memoria_salvar_duplicado():
    repo = RepositorioMemoria()
    repo.salvar(LIVRO_A)
    with pytest.raises(LivroDuplicadoError):
        repo.salvar(LIVRO_A)


def test_repositorio_memoria_atualizar_inexistente():
    with pytest.raises(LivroNaoEncontradoError):
        RepositorioMemoria().atualizar(LIVRO_A)


# --- repositório SQLite: listar() ----------------------------------------------
def test_repositorio_sqlite_listar_ordenado_por_isbn(ambiente_integracao):
    repo = ambiente_integracao.repositorio
    repo.salvar(LIVRO_B)  # ISBN maior, salvo primeiro de propósito
    repo.salvar(LIVRO_A)
    assert repo.listar() == [LIVRO_A, LIVRO_B]


def test_repositorio_sqlite_listar_vazio(ambiente_integracao):
    assert ambiente_integracao.repositorio.listar() == []


# --- repositório SQLite: falhas do banco viram ErroPersistenciaError ----------
@pytest.mark.parametrize(
    "operacao",
    [
        pytest.param(lambda r: r.salvar(LIVRO_A), id="salvar"),
        pytest.param(lambda r: r.atualizar(LIVRO_A), id="atualizar"),
        pytest.param(lambda r: r.buscar_por_isbn(LIVRO_A.isbn), id="buscar_por_isbn"),
        pytest.param(lambda r: r.existe(LIVRO_A.isbn), id="existe"),
        pytest.param(lambda r: r.listar(), id="listar"),
    ],
)
def test_banco_indisponivel_gera_erro_de_persistencia(ambiente_integracao, operacao):
    ambiente_integracao.conexao.close()  # simula banco inacessível
    with pytest.raises(ErroPersistenciaError):
        operacao(ambiente_integracao.repositorio)
```

**Passo 4 – cobertura final:**
```text
........................................................................ [ 64%]
.......................................                                  [100%]
================================ tests coverage ================================
_______________ coverage: platform linux, python 3.12.3-final-0 ________________
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
biblioteca/__init__.py         0      0   100%
biblioteca/biblioteca.py      30      0   100%
biblioteca/database.py         8      0   100%
biblioteca/excecoes.py         6      0   100%
biblioteca/livro.py           23      0   100%
biblioteca/repository.py      57      0   100%
biblioteca/validators.py      24      0   100%
--------------------------------------------------------
TOTAL                        148      0   100%
111 passed in 0.25s
```

Execução dos novos testes:
```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
plugins: cov-7.1.0
collecting ... collected 9 items

tests/test_cobertura_extra.py::test_repositorio_memoria_salvar_duplicado PASSED
tests/test_cobertura_extra.py::test_repositorio_memoria_atualizar_inexistente PASSED
tests/test_cobertura_extra.py::test_repositorio_sqlite_listar_ordenado_por_isbn PASSED
tests/test_cobertura_extra.py::test_repositorio_sqlite_listar_vazio PASSED
tests/test_cobertura_extra.py::test_banco_indisponivel_gera_erro_de_persistencia[salvar] PASSED
tests/test_cobertura_extra.py::test_banco_indisponivel_gera_erro_de_persistencia[atualizar] PASSED
tests/test_cobertura_extra.py::test_banco_indisponivel_gera_erro_de_persistencia[buscar_por_isbn] PASSED
tests/test_cobertura_extra.py::test_banco_indisponivel_gera_erro_de_persistencia[existe] PASSED
tests/test_cobertura_extra.py::test_banco_indisponivel_gera_erro_de_persistencia[listar] PASSED

============================== 9 passed in 0.02s ===============================
```

### 3. Resultado da execução — comparação

| | Antes | Depois |
|---|---|---|
| Testes | 102 | 111 |
| Cobertura total | **93%** (138 de 148 linhas) | **100%** (148 de 148) |
| `repository.py` | 82% | 100% |

### 4. Interpretação – por que cobertura alta, sozinha, não garante qualidade?
**Cobertura mede quais linhas foram *executadas*, não se o resultado foi *verificado*.** Um teste que chama `emprestar_livro()` e não tem nenhum `assert` já "cobre" a linha, mas não detectaria nenhum defeito. Em resumo:

1. **Execução ≠ verificação.** Sem asserções significativas, 100% de cobertura pode conviver com 0% de detecção de bugs. O que prova a qualidade desta suíte é a Questão 13, que mostrou mutações sendo detectadas.
2. **Não mede dados nem combinações.** A linha `if quantidade < 0` é "coberta" por um único valor; o erro `<` vs `<=` só aparece com valores-limite (Questão 4).
3. **Não vê o que não foi escrito.** Se uma regra de negócio nunca foi implementada (por exemplo, limitar a devolução ao total de exemplares do acervo), nenhuma linha falta e a cobertura não aponta nada.
4. **Não distingue qualidade do teste.** Um teste frágil, redundante ou acoplado a detalhes internos conta igual a um bom.

Por isso a cobertura serve melhor como **detector de lacunas** (o que não foi testado) do que como **certificado de qualidade**. Foi exatamente assim que a usei: o relatório apontou o tratamento de falhas do banco como ponto cego.

---

# Questão final de síntese

> **Explique, com exemplos do sistema, a diferença entre teste unitário e teste de integração.**

**Resumo em uma frase:** o teste unitário pergunta *"esta peça funciona sozinha?"*; o de integração pergunta *"as peças funcionam juntas?"*. Uma roda perfeita e um motor perfeito não garantem um carro que anda.

| | Teste unitário | Teste de integração |
|---|---|---|
| **Exemplo no projeto** | `test_mocks.py::test_emprestar_persiste_o_livro_atualizado` e `test_livro.py::test_emprestar_reduz_um_exemplar` | `test_integracao.py::test_integracao_fluxo_completo` e `test_persistencia_*` |
| **Componente testado isoladamente** | `Biblioteca` (regras de serviço) e `Livro` (regra de estoque) | Não há um isolado: o alvo é o **conjunto** |
| **Dependências substituídas ou controladas** | O repositório foi trocado por `create_autospec(LivroRepository)`; `validar_isbn` foi trocada via `@patch`; respostas e falhas controladas por `return_value` e `side_effect` | **Nenhuma** substituída. A única "controlada" é o banco, que é real mas descartável (`:memory:` / `tmp_path`) |
| **Componentes usados de forma real** | Só a unidade sob teste | `Biblioteca` → `validators` → `Livro` → `LivroRepository` → `database.py` → SQLite |
| **Velocidade/determinismo** | Altíssimos; sem I/O | Menores, mas ainda rápidos (banco em memória) |
| **Tipo de defeito que detecta** | Erros **de lógica interna**: regra de estoque errada (`-= 1` omitido, `+= 2`), validação com `<` no lugar de `<=`, exceção errada ou ausente, chamada ao repositório com argumentos errados ou que não deveria ocorrer (`salvar` num duplicado), falha do repositório não propagada | Erros **de contrato e de encaixe** entre componentes: SQL com colunas em ordem diferente de `Livro(*linha)`, esquema da tabela incompatível, falta de `commit` (dado "salvo" que some), ISBN normalizado em uma camada e não em outra, estado que não se mantém entre operações |

**Exemplo que mostra a complementaridade.** Suponha que `LivroRepository.atualizar` esquecesse de gravar a `quantidade`:
- Os testes **unitários** de `Biblioteca` continuariam **passando**: o mock aceita qualquer chamada a `atualizar` e `assert_called_once_with(livro)` está satisfeito.
- Já `test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca` **falharia**: leria do banco o estoque antigo.

Inversamente, se `Livro.emprestar()` tivesse a regra errada, o teste unitário de `Livro` apontaria **a linha exata** da causa, enquanto o de integração só diria que "algo no fluxo está errado". Daí a estratégia progressiva da atividade: muitos testes unitários, rápidos e precisos, e menos testes de integração, mais lentos, para cobrir as junções.

---

# Considerações finais e limitações conhecidas

- **Devolução sem teto.** O enunciado pede apenas a quantidade de exemplares *disponíveis*. Sem guardar o total do acervo, o sistema permite devolver mais exemplares do que existem. A cobertura de 100% **não revela** isso (item 3 da Questão 14). Uma evolução natural seria adicionar `quantidade_total` a `Livro` e testar o novo limite.
- **Testes de `Biblioteca` com repositório real em memória** (Questões 2, 5, 6) são "unitários sociáveis": rápidos, porém com um colaborador real. O isolamento estrito está nos testes da Questão 7/8.
- **Sem estado global.** Nenhum teste depende da ordem de execução, nem toca o `biblioteca.db` da aplicação.

# Apêndice – Execução completa da suíte

`python -m pytest -v`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- /usr/bin/python
rootdir: /home/claude/mini_biblioteca
configfile: pytest.ini
testpaths: tests
plugins: cov-7.1.0
collecting ... collected 102 items

tests/test_biblioteca.py::test_cadastrar_livro_retorna_o_livro_cadastrado PASSED
tests/test_biblioteca.py::test_consultar_livro_existente PASSED
tests/test_biblioteca.py::test_consultar_aceita_isbn_com_hifens PASSED
tests/test_biblioteca.py::test_livro_com_exemplares_esta_disponivel PASSED
tests/test_biblioteca.py::test_livro_sem_exemplares_nao_esta_disponivel PASSED
tests/test_biblioteca.py::test_emprestar_livro_reduz_a_quantidade_no_repositorio PASSED
tests/test_biblioteca.py::test_devolver_livro_aumenta_a_quantidade_no_repositorio PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[isbn-curto] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[titulo-vazio] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[autor-so-espacos] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[quantidade-negativa] PASSED
tests/test_excecoes.py::test_cadastro_com_dados_invalidos[quantidade-texto] PASSED
tests/test_excecoes.py::test_cadastro_invalido_nao_grava_nada PASSED
tests/test_excecoes.py::test_cadastro_duplicado PASSED
tests/test_excecoes.py::test_cadastro_duplicado_preserva_o_livro_original PASSED
tests/test_excecoes.py::test_emprestimo_de_livro_inexistente PASSED
tests/test_excecoes.py::test_emprestimo_sem_exemplares PASSED
tests/test_excecoes.py::test_emprestimo_sem_exemplares_nao_deixa_estoque_negativo PASSED
tests/test_excecoes.py::test_devolucao_de_livro_inexistente PASSED
tests/test_excecoes.py::TestExcecoesUnittest::test_emprestimo_de_livro_inexistente PASSED
tests/test_excecoes.py::TestExcecoesUnittest::test_emprestimo_sem_exemplares_e_mensagem PASSED
tests/test_fixtures.py::test_livro_disponivel_esta_disponivel PASSED
tests/test_fixtures.py::test_livro_disponivel_pode_ser_emprestado PASSED
tests/test_fixtures.py::test_livro_disponivel_emprestado_duas_vezes_fica_indisponivel PASSED
tests/test_fixtures.py::test_livro_indisponivel_nao_esta_disponivel PASSED
tests/test_fixtures.py::test_livro_indisponivel_bloqueia_emprestimo PASSED
tests/test_fixtures.py::test_livro_indisponivel_volta_a_ficar_disponivel_apos_devolucao PASSED
tests/test_fixtures.py::test_biblioteca_cadastra_e_consulta_livro_da_fixture PASSED
tests/test_fixtures.py::test_biblioteca_empresta_livro_da_fixture PASSED
tests/test_fixtures.py::test_cada_teste_recebe_um_repositorio_novo PASSED
tests/test_integracao.py::test_integracao_cadastro_pesquisa_e_emprestimo PASSED
tests/test_integracao.py::test_integracao_fluxo_completo PASSED
tests/test_integracao.py::test_persistencia_cadastro_grava_linha_no_banco PASSED
tests/test_integracao.py::test_persistencia_recupera_dados_iguais_aos_cadastrados PASSED
tests/test_integracao.py::test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca PASSED
tests/test_integracao.py::test_persistencia_cadastro_duplicado_nao_cria_segunda_linha PASSED
tests/test_integracao.py::test_persistencia_em_arquivo_sobrevive_ao_fechamento_da_conexao PASSED
tests/test_livro.py::test_criar_livro_com_dados_validos PASSED
tests/test_livro.py::test_isbn_com_hifens_e_normalizado PASSED
tests/test_livro.py::test_titulo_e_autor_tem_espacos_removidos PASSED
tests/test_livro.py::test_quantidade_de_exemplares_e_inteira PASSED
tests/test_livro.py::test_livro_com_exemplares_esta_disponivel PASSED
tests/test_livro.py::test_livro_sem_exemplares_nao_esta_disponivel PASSED
tests/test_livro.py::test_emprestar_reduz_um_exemplar PASSED
tests/test_livro.py::test_devolver_aumenta_um_exemplar PASSED
tests/test_mocks.py::test_cadastrar_livro_novo_consulta_existencia_e_salva PASSED
tests/test_mocks.py::test_cadastrar_livro_duplicado_nao_chama_salvar PASSED
tests/test_mocks.py::test_consultar_livro_devolve_o_que_o_repositorio_retorna PASSED
tests/test_mocks.py::test_emprestar_persiste_o_livro_atualizado PASSED
tests/test_mocks.py::test_consultar_usa_o_isbn_normalizado_pelo_validador PASSED
tests/test_mocks.py::test_disponibilidade_com_respostas_sucessivas_do_repositorio PASSED
tests/test_mocks.py::test_cadastro_propaga_falha_do_repositorio PASSED
tests/test_mocks.py::test_emprestimo_propaga_falha_ao_atualizar PASSED
tests/test_repository.py::test_salvar_e_buscar_devolve_livro_igual PASSED
tests/test_repository.py::test_buscar_isbn_inexistente_retorna_none PASSED
tests/test_repository.py::test_existe PASSED
tests/test_repository.py::test_salvar_isbn_duplicado_lanca_erro PASSED
tests/test_repository.py::test_atualizar_altera_a_quantidade PASSED
tests/test_repository.py::test_atualizar_livro_inexistente_lanca_erro PASSED
tests/test_unittest_biblioteca.py::TestCriacaoDeLivro::test_criar_livro_com_dados_validos PASSED
tests/test_unittest_biblioteca.py::TestDisponibilidade::test_livro_com_exemplares_esta_disponivel PASSED
tests/test_unittest_biblioteca.py::TestDisponibilidade::test_livro_sem_exemplares_nao_esta_disponivel PASSED
tests/test_unittest_biblioteca.py::TestEmprestimoEDevolucao::test_devolucao_aumenta_quantidade PASSED
tests/test_unittest_biblioteca.py::TestEmprestimoEDevolucao::test_emprestimo_reduz_quantidade PASSED
tests/test_validadores.py::test_quantidade_valida[LIMITE-valida-0] PASSED
tests/test_validadores.py::test_quantidade_valida[LIMITE+1-valida-1] PASSED
tests/test_validadores.py::test_quantidade_valida[nominal-valida-2] PASSED
tests/test_validadores.py::test_quantidade_valida[valida-grande] PASSED
tests/test_validadores.py::test_quantidade_invalida[LIMITE-1-invalida-menos1] PASSED
tests/test_validadores.py::test_quantidade_invalida[invalida-menos2] PASSED
tests/test_validadores.py::test_quantidade_invalida[invalida-muito-negativa] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-float] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-str] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-bool] PASSED
tests/test_validadores.py::test_quantidade_invalida[tipo-invalido-None] PASSED
tests/test_validadores.py::test_isbn_valido_e_normalizado[9780132350884-9780132350884] PASSED
tests/test_validadores.py::test_isbn_valido_e_normalizado[978-0-13-235088-4-9780132350884] PASSED
tests/test_validadores.py::test_isbn_valido_e_normalizado[978 0 13 235088 4-9780132350884] PASSED
tests/test_validadores.py::test_isbn_valido_e_normalizado[0306406152-0306406152] PASSED
tests/test_validadores.py::test_isbn_valido_e_normalizado[080442957x-080442957X] PASSED
tests/test_validadores.py::test_isbn_invalido[] PASSED
tests/test_validadores.py::test_isbn_invalido[123456789] PASSED
tests/test_validadores.py::test_isbn_invalido[12345678901] PASSED
tests/test_validadores.py::test_isbn_invalido[978013235088] PASSED
tests/test_validadores.py::test_isbn_invalido[97801323508845] PASSED
tests/test_validadores.py::test_isbn_invalido[97801323508AB] PASSED
tests/test_validadores.py::test_isbn_invalido[ISBN-INVALIDO] PASSED
tests/test_validadores.py::test_isbn_invalido[None] PASSED
tests/test_validadores.py::test_isbn_invalido[9780132350884] PASSED
tests/test_validadores.py::test_regra_de_emprestimo_por_estoque[nominal-2] PASSED
tests/test_validadores.py::test_regra_de_emprestimo_por_estoque[LIMITE-ultimo-exemplar] PASSED
tests/test_validadores.py::test_regra_de_emprestimo_por_estoque[LIMITE-sem-exemplares] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[-validar_titulo] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[-validar_autor] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[   -validar_titulo] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[   -validar_autor] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[\t\n-validar_titulo] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[\t\n-validar_autor] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[None-validar_titulo] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[None-validar_autor] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[123-validar_titulo] PASSED
tests/test_validadores.py::test_texto_obrigatorio_invalido[123-validar_autor] PASSED

============================= 102 passed in 0.10s ==============================
```
