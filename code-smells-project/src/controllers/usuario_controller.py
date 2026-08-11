"""Controller do domínio Usuário (RP-03, RP-04, RP-11, RP-12).

O login emite token verificável assinado com a SECRET_KEY (TokenService).
Nenhuma resposta contém senha/hash.
"""
import logging

from src.exceptions import AuthError, NotFoundError, ValidationError

logger = logging.getLogger(__name__)


def _validar_novo_usuario(dados):
    if not dados:
        raise ValidationError("Dados inválidos")

    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not isinstance(nome, str) or not isinstance(email, str) or not isinstance(senha, str):
        raise ValidationError("Nome, email e senha devem ser texto")
    if not nome.strip() or not email.strip() or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    return {"nome": nome, "email": email, "senha": senha}


def _validar_credenciais(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")
    return email, senha


class UsuarioController:
    def __init__(self, usuario_model, token_service):
        self._usuarios = usuario_model
        self._tokens = token_service

    def listar(self):
        return {"dados": self._usuarios.listar(), "sucesso": True}, 200

    def buscar(self, usuario_id):
        usuario = self._usuarios.buscar_por_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return {"dados": usuario, "sucesso": True}, 200

    def criar(self, dados):
        campos = _validar_novo_usuario(dados)
        novo_id = self._usuarios.criar(**campos)
        logger.info("Usuário criado: id=%s", novo_id)
        return {"dados": {"id": novo_id}, "sucesso": True}, 201

    def login(self, dados):
        email, senha = _validar_credenciais(dados)
        usuario = self._usuarios.autenticar(email, senha)
        if usuario is None:
            logger.info("Tentativa de login inválida")
            raise AuthError("Email ou senha inválidos", extra={"sucesso": False})

        usuario["token"] = self._tokens.gerar(usuario["id"], usuario["tipo"])
        logger.info("Login bem-sucedido: usuario_id=%s", usuario["id"])
        return {"dados": usuario, "sucesso": True, "mensagem": "Login OK"}, 200
