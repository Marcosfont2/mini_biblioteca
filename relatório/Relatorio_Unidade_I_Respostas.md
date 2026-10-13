# Atividade Avaliativa – Unidade I
## Desenvolvimento e Teste de um Mini Sistema de Biblioteca

| | |
|---|---|
| **Disciplina** | Testes de Software I |
| **Curso** | Ciência da Computação |
| **Aluno(a)** | Marcos Antônio Fontes Leite |
| **Matrícula** | 20230019430 |
| **Data de entrega** | 13/10/26 |

> Código-fonte, testes e instruções de execução estão na pasta `mini_biblioteca/` (arquivo zip entregue junto). Este documento traz apenas as respostas, as saídas de êxito esperadas e as explicações.

**Execução completa:** `python -m pytest -v` → `111 passed` · **Cobertura:** `python -m pytest --cov=biblioteca` → `100%`

---

## Questão 1 – Construção e organização inicial

**(a) Estrutura**

```text
mini_biblioteca/
├── biblioteca/   excecoes.py · validators.py · livro.py · repository.py · database.py · biblioteca.py
└── tests/        conftest.py · test_livro.py · test_biblioteca.py · test_unittest_biblioteca.py
                  test_validadores.py · test_excecoes.py · test_fixtures.py · test_mocks.py
                  test_repository.py · test_integracao.py · test_cobertura_extra.py
```

**(c) Responsabilidades**

| Módulo | Responsabilidade |
|---|---|
| `excecoes.py` | Exceções do domínio: `DadosInvalidosError`, `LivroDuplicadoError`, `LivroNaoEncontradoError`, `SemExemplaresError`, `ErroPersistenciaError`. |
| `validators.py` | Valida e normaliza ISBN (10/13 dígitos, remove hífens), título e autor (texto não vazio) e quantidade (inteiro ≥ 0). |
| `livro.py` | Entidade `Livro` (ISBN, título, autor, quantidade). Valida ao ser criada; `disponivel`, `emprestar()` (−1, erro se zero) e `devolver()` (+1). |
| `repository.py` | `RepositorioMemoria` (dicionário) e `LivroRepository` (SQLite): `salvar`, `atualizar`, `buscar_por_isbn`, `existe`, `listar`. |
| `database.py` | Abre a conexão (caminho é parâmetro) e cria a tabela `livros`. |
| `biblioteca.py` | Serviço com as regras: cadastrar, consultar, verificar disponibilidade, emprestar e devolver. Recebe o repositório pelo construtor. |

**Explicação:** a regra de estoque fica em `Livro`, as regras de cadastro e busca em `Biblioteca`, e a gravação nos repositórios. Essa separação cria "unidades" claras e permite trocar o repositório por um mock (testes unitários) ou por um real (integração).

---

## Questão 2 – Primeiros testes unitários com pytest

**Arquivos:** `test_livro.py` e `test_biblioteca.py`. Cobrem criação de livro, ISBN, título, autor, quantidade, cadastro, consulta, disponibilidade, empréstimo e devolução. Em todos os testes principais as linhas estão marcadas com os comentários `# Arrange`, `# Act` e `# Assert` (por exemplo, `test_criar_livro_com_dados_validos`, `test_emprestar_reduz_um_exemplar`).

**Saída de êxito esperada:**
```text
tests/test_livro.py::test_criar_livro_com_dados_validos PASSED
tests/test_livro.py::test_emprestar_reduz_um_exemplar PASSED
tests/test_biblioteca.py::test_emprestar_livro_reduz_a_quantidade_no_repositorio PASSED
...
```

**Explicação:** o padrão AAA separa preparação, execução e verificação. No teste de empréstimo o *Assert* relê o livro do repositório, confirmando que a mudança foi gravada e não só alterada em memória.

---

## Questão 3 – Testes com unittest

**Arquivo:** `test_unittest_biblioteca.py`. Funcionalidades reescritas: (1) criação de livro, (2) disponibilidade, (3) empréstimo e devolução. Usa `assertEqual`, `assertTrue`, `assertFalse`, `assertIsInstance` e `setUp()`.

**Saída de êxito esperada** (`python -m unittest discover -s tests -p "test_unittest*.py" -v`):
```text
test_criar_livro_com_dados_validos (...) ... ok
test_livro_com_exemplares_esta_disponivel (...) ... ok
test_livro_sem_exemplares_nao_esta_disponivel (...) ... ok
test_emprestimo_reduz_quantidade (...) ... ok
test_devolucao_aumenta_quantidade (...) ... ok
Ran 5 tests ... OK
```

**Principal diferença observada:** no pytest o teste é uma função comum com `assert` do próprio Python, e a falha mostra os valores (`assert 3 == 2`). No unittest o teste é um método de uma classe que herda de `TestCase`, com métodos de asserção (`self.assertEqual`) e preparação via `setUp()`. O pytest exige menos código; o unittest é mais verboso, mas faz parte da biblioteca padrão.

---

## Questão 4 – Parametrização, classes de equivalência e valores-limite

**Arquivo:** `test_validadores.py`. Regras parametrizadas: (1) **quantidade de exemplares** (≥ 0), (2) formato do ISBN, (3) empréstimo × estoque, (4) título/autor não vazios.

| Entrada (quantidade) | Classe | Resultado esperado |
|---|---|---|
| `-2` | inválida | `DadosInvalidosError` |
| `-1` | **limite** inválido | `DadosInvalidosError` |
| `0` | **limite** válido | aceita |
| `1` | limite + 1, válida | aceita |
| `2` | válida (nominal) | aceita |
| `1.5`, `"2"`, `None`, `True` | inválida (tipo) | `DadosInvalidosError` |

| Estoque | Classe | Resultado esperado |
|---|---|---|
| `2` | válida | empresta → estoque `1` |
| `1` | limite (último exemplar) | empresta → estoque `0` |
| `0` | limite (sem exemplares) | `SemExemplaresError` |

**Saída de êxito esperada:**
```text
test_quantidade_valida[LIMITE-valida-0] PASSED
test_quantidade_valida[LIMITE+1-valida-1] PASSED
test_quantidade_invalida[LIMITE-1-invalida-menos1] PASSED
test_regra_de_emprestimo_por_estoque[LIMITE-ultimo-exemplar] PASSED
```

**Critério de seleção:** classes de equivalência (um representante por grupo tratado igualmente) e análise de valores-limite (testar os dois lados da fronteira, `-1 | 0`), onde ocorrem erros como `<` no lugar de `<=`.

---

## Questão 5 – Testando exceções

**Arquivo:** `test_excecoes.py`.

| Cenário | Exceção esperada |
|---|---|
| Cadastro com dados inválidos | `DadosInvalidosError` |
| Cadastro duplicado | `LivroDuplicadoError` |
| Empréstimo de livro inexistente | `LivroNaoEncontradoError` |
| Empréstimo com quantidade zero | `SemExemplaresError` |
| Devolução de livro inexistente | `LivroNaoEncontradoError` |

Usa `pytest.raises()` em todos e `assertRaises()` (classe `TestExcecoesUnittest`) em dois cenários.

**Saída de êxito esperada:**
```text
tests/test_excecoes.py::test_cadastro_duplicado PASSED
tests/test_excecoes.py::test_emprestimo_sem_exemplares PASSED
tests/test_excecoes.py::TestExcecoesUnittest::test_emprestimo_de_livro_inexistente PASSED
```

**Por que receber a exceção é sucesso:** a especificação manda *impedir* operações inválidas, e impedir significa recusar explicitamente. A exceção é o comportamento correto; sua ausência é o defeito. `pytest.raises` passa se a exceção esperada ocorre, e falha com `DID NOT RAISE` se nada acontece. Os testes também verificam efeitos colaterais (cadastro inválido não grava; empréstimo recusado não deixa estoque negativo).

---

## Questão 6 – Fixtures

**Arquivo:** `conftest.py` (fixtures) e `test_fixtures.py` (uso). Fixtures: `livro`, `livro_disponivel`, `livro_indisponivel`, `repositorio`, `biblioteca`.

| Fixture | Testes em que é usada |
|---|---|
| `livro_disponivel` | 3 (disponibilidade, empréstimo, esgotar estoque) |
| `livro_indisponivel` | 3 (indisponibilidade, bloqueio do empréstimo, devolução) |
| `livro` | 2 (cadastro + consulta, cadastro + empréstimo) |
| `biblioteca` (depende de `repositorio`) | 2 em `test_fixtures.py` e todo `test_excecoes.py` |

**Saída de êxito esperada:**
```text
tests/test_fixtures.py::test_livro_disponivel_pode_ser_emprestado PASSED
tests/test_fixtures.py::test_livro_indisponivel_bloqueia_emprestimo PASSED
tests/test_fixtures.py::test_biblioteca_empresta_livro_da_fixture PASSED
```

**Repetição eliminada:** antes, cada teste repetia `Biblioteca(RepositorioMemoria())`, o cadastro inicial e a criação do `Livro(...)`. Agora essa preparação existe uma vez, em `conftest.py`. A fixture é recriada a cada teste, então nenhum dado "vaza" entre eles.

---

## Questão 7 – Mock/Patch

**Arquivo:** `test_mocks.py`. **Dependência isolada:** o repositório (`LivroRepository`), via `create_autospec`; e a função `validar_isbn`, via `@patch("biblioteca.biblioteca.validar_isbn")`.

- `return_value` configurado em `existe` e `buscar_por_isbn`.
- `assert_called_once_with(...)` confirma que `Biblioteca` consultou e gravou com os argumentos certos.
- `assert_not_called()` confirma que um cadastro duplicado não chama `salvar`.

**Saída de êxito esperada:**
```text
tests/test_mocks.py::test_cadastrar_livro_novo_consulta_existencia_e_salva PASSED
tests/test_mocks.py::test_cadastrar_livro_duplicado_nao_chama_salvar PASSED
tests/test_mocks.py::test_consultar_livro_devolve_o_que_o_repositorio_retorna PASSED
tests/test_mocks.py::test_emprestar_persiste_o_livro_atualizado PASSED
tests/test_mocks.py::test_consultar_usa_o_isbn_normalizado_pelo_validador PASSED
```

**Por que continua sendo unitário:** a unidade sob teste é `Biblioteca`; seu colaborador foi trocado por um dublê controlado. Não há banco nem disco, o teste é determinístico e só falha se a lógica de `Biblioteca` estiver errada. O `autospec` garante que o dublê tem a mesma interface da classe real.

---

## Questão 8 – Comportamentos diferentes da dependência

**Dependência simulada:** o repositório. **Por quê:** provocar uma falha real de banco ou respostas diferentes a cada chamada é difícil e não repetível; com `side_effect` fica determinístico.

| Cenário | Configuração | Resultado esperado |
|---|---|---|
| Normal | `buscar_por_isbn.side_effect = [livro(qtd 1), livro(qtd 0)]` | 1ª verificação `True`, 2ª `False`; 2 chamadas |
| Falha ao salvar | `salvar.side_effect = ErroPersistenciaError(...)` | `cadastrar_livro` propaga o erro |
| Falha ao atualizar | `atualizar.side_effect = ErroPersistenciaError(...)` | `emprestar_livro` propaga o erro |

**Saída de êxito esperada:**
```text
tests/test_mocks.py::test_disponibilidade_com_respostas_sucessivas_do_repositorio PASSED
tests/test_mocks.py::test_cadastro_propaga_falha_do_repositorio PASSED
tests/test_mocks.py::test_emprestimo_propaga_falha_ao_atualizar PASSED
```

**Interpretação:** a lista em `side_effect` simula uma dependência cujo estado muda; a exceção simula a falha. `Biblioteca` não esconde o erro, o que é o comportamento desejado: quem chamou precisa saber que a operação não foi concluída.

---

## Questão 9 – Primeiro teste de integração

**Teste:** `test_integracao_cadastro_pesquisa_e_emprestimo` (sem mocks). Componentes reais: `Biblioteca`, `validators`, `Livro`, `RepositorioMemoria`.

```text
cadastrar ─▶ consultar ─▶ disponível? ─▶ emprestar ─▶ consultar ─▶ quantidade −1
```

**Saída de êxito esperada:**
```text
tests/test_integracao.py::test_integracao_cadastro_pesquisa_e_emprestimo PASSED
```

**Interpretação:** passar significa que a saída de cada componente é aceita pelo seguinte e que o estoque reduzido pelo empréstimo chega ao repositório e é visto na consulta seguinte.

---

## Questão 10 – Integração do fluxo completo

**Teste:** `test_integracao_fluxo_completo`: cadastrar → consultar → emprestar → consultar → devolver → consultar, com SQLite em memória.

Verificações: livro cadastrado corretamente; encontrado; estoque cai após o empréstimo (`1 → 0`) e a disponibilidade vira `False`; sobe após a devolução (`0 → 1`); estado final igual ao inicial.

**Componentes integrados:** `Biblioteca` → `validators` → `Livro` → `LivroRepository` → `database.py` → SQLite.

**Saída de êxito esperada:**
```text
tests/test_integracao.py::test_integracao_fluxo_completo PASSED
```

---

## Questão 11 – Integração com persistência (SQLite)

**Testes:** `test_persistencia_*` em `test_integracao.py` e `test_repository.py`. Fluxo: inicializar banco `:memory:` → cadastrar → persistir → nova consulta → recuperar → comparar.

- Consulta SQL direta confirma que a linha existe no banco.
- `recuperado is not cadastrado` e `recuperado == cadastrado`: veio do banco e os dados são idênticos.
- Nova instância da `Biblioteca` sobre o mesmo banco vê o estoque após o empréstimo.
- Teste com arquivo temporário: fecha a conexão, reabre e recupera o livro.
- Cadastro duplicado não cria segunda linha.

O banco da aplicação (`biblioteca.db`) não é tocado: os testes usam `:memory:` e `tmp_path`.

**Saída de êxito esperada:**
```text
tests/test_integracao.py::test_persistencia_cadastro_grava_linha_no_banco PASSED
tests/test_integracao.py::test_persistencia_recupera_dados_iguais_aos_cadastrados PASSED
tests/test_integracao.py::test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca PASSED
tests/test_integracao.py::test_persistencia_cadastro_duplicado_nao_cria_segunda_linha PASSED
tests/test_integracao.py::test_persistencia_em_arquivo_sobrevive_ao_fechamento_da_conexao PASSED
```

**Interpretação:** um mock de `salvar()` não detectaria esquema errado, falta de `commit` ou ordem de colunas incorreta; aqui qualquer um desses reprovaria o teste.

---

## Questão 12 – Fixture para integração

**Fixture:** `ambiente_integracao` (em `conftest.py`). Usada em `test_integracao_fluxo_completo`, nos quatro `test_persistencia_*` que dependem dela e em todos os testes de `test_repository.py`.

**Saída de êxito esperada** (`pytest --setup-show`):
```text
SETUP    F ambiente_integracao
tests/test_integracao.py::test_integracao_fluxo_completo (fixtures used: ambiente_integracao) .
TEARDOWN F ambiente_integracao
```

- **Setup (antes do `yield`):** abre SQLite em memória, cria a tabela, monta repositório e biblioteca. Cada teste começa com banco vazio.
- **Execução do teste:** acontece no `yield`; o pytest pausa a fixture, roda o teste e a retoma.
- **Teardown (depois do `yield`):** fecha a conexão, descartando o banco. Roda mesmo se o teste falhar, evitando vazamento de recursos.

---

## Questão 13 – Investigação de falhas

- **Erro introduzido:** em `Livro.emprestar()`, a linha `self.quantidade -= 1` foi substituída por `pass`.
- **Teste que detectou:** `test_livro.py::test_emprestar_reduz_um_exemplar` (e outros 14: unitários, mock, repositório e integração).
- **Mensagem do framework:**
```text
tests/test_livro.py:56: in test_emprestar_reduz_um_exemplar
    assert livro.quantidade == 2
E   AssertionError: assert 3 == 2
15 failed, 87 passed
```
- **Interpretação:** o valor obtido (3) difere do esperado (2); o estoque não diminuiu após o empréstimo, então o defeito está em `Livro.emprestar()`.
- **Correção:** restaurar `self.quantidade -= 1`. Resultado após corrigir: todos os testes passam.

Outras mutações também detectadas: `devolver` somando 2 (4 falhas), permitir empréstimo com estoque zero (5 falhas), consultar ISBN incorreto (23 falhas).

---

## Questão 14 – Cobertura

Comando: `python -m pytest --cov=biblioteca --cov-report=term-missing`

| | Antes | Depois |
|---|---|---|
| Testes | 102 | 111 |
| Cobertura total | **93%** | **100%** |
| `repository.py` | 82% | 100% |

**Módulo com menor cobertura:** `repository.py` (linhas 21, 26, 51-52, 57-58, 71-72, 98-103).

**Comportamentos não testados:** duplicado e atualização de inexistente no repositório em memória; **falha do banco** (conversão de `sqlite3.Error` em `ErroPersistenciaError`); `listar()` do SQLite.

**Novos testes** (`test_cobertura_extra.py`): exceções do repositório em memória, `listar` ordenado e vazio, e um teste parametrizado que fecha a conexão e confirma que as 5 operações lançam `ErroPersistenciaError`.

**Saída de êxito esperada (final):**
```text
biblioteca/repository.py      57      0   100%
TOTAL                        148      0   100%
111 passed
```

**Por que cobertura alta, isoladamente, não garante qualidade:** a cobertura mede quais linhas foram *executadas*, não se o resultado foi *verificado*. Um teste sem `assert` cobre a linha e não detecta defeito. Ela também não mede combinações de dados (o erro `<` vs `<=` exige valores-limite), não revela regras nunca implementadas (como limitar a devolução ao total de exemplares) e não distingue testes bons de frágeis. Serve melhor para achar lacunas do que para certificar qualidade; a Questão 13 é o que mostra que esta suíte detecta defeitos.

---

## Questão final – Teste unitário × teste de integração

| | Teste unitário | Teste de integração |
|---|---|---|
| **Exemplo** | `test_livro.py::test_emprestar_reduz_um_exemplar`; `test_mocks.py::test_emprestar_persiste_o_livro_atualizado` | `test_integracao_fluxo_completo`; `test_persistencia_*` |
| **Componente testado isoladamente** | `Livro` (regra de estoque) e `Biblioteca` (regras de serviço) | Nenhum isolado: o alvo é o conjunto |
| **Dependências substituídas ou controladas** | Repositório trocado por `create_autospec(LivroRepository)`; `validar_isbn` por `@patch`; respostas e falhas via `return_value` e `side_effect` | Nenhuma substituída; o banco é real, mas descartável (`:memory:` / `tmp_path`) |
| **Componentes reais** | Só a unidade sob teste | `Biblioteca` → `validators` → `Livro` → `LivroRepository` → `database.py` → SQLite |
| **Defeitos que detecta** | Erros de lógica interna: estoque errado, validação com `<` no lugar de `<=`, exceção ausente ou errada, chamada indevida ao repositório (ex.: `salvar` num duplicado), falha não propagada | Erros de encaixe e contrato: SQL com colunas em ordem diferente, esquema incompatível, falta de `commit`, normalização de ISBN inconsistente entre camadas, estado que não se mantém entre operações |

**Exemplo de complementaridade:** se `LivroRepository.atualizar` esquecesse de gravar a quantidade, os testes unitários de `Biblioteca` continuariam passando (o mock aceita a chamada), mas `test_persistencia_emprestimo_sobrevive_a_nova_instancia_da_biblioteca` falharia, pois leria do banco o estoque antigo. Inversamente, um erro em `Livro.emprestar()` seria apontado com precisão pelo teste unitário, enquanto o de integração só indicaria que algo no fluxo está errado.

---

## Observações

- A devolução não tem limite superior (o enunciado só pede a quantidade *disponível*); a cobertura de 100% não revela isso.
- Nenhum teste depende da ordem de execução nem altera o `biblioteca.db` da aplicação.
