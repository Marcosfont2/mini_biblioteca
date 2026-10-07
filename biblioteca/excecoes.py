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
