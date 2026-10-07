# Mini Sistema de Biblioteca – Testes de Software I (Unidade I)

```bash
pip install -r requirements.txt
python -m pytest -v                                      # pytest + unittest
python -m pytest --cov=biblioteca --cov-report=term-missing
python -m unittest discover -s tests -p "test_*.py" -v   # apenas os testes unittest
```

- `biblioteca/` – código da aplicação (Livro, Biblioteca, validadores, repositórios, SQLite)
- `tests/` – testes (unitários, parametrizados, exceções, fixtures, mocks, integração, persistência)
- `relatorio_cobertura.txt` – cobertura antes e depois da Questão 14
- O relatório com as respostas de todas as questões está em `Relatorio_Atividade_Unidade_I.md`
