"""Emissão e verificação de tokens de autenticação (RP-12).

Substitui a ausência de material de autenticação do legado: o login passa a
emitir um token ASSINADO com a SECRET_KEY (itsdangerous, já incluído no
Flask — nenhuma dependência nova), verificável server-side via `validar`.
"""
from itsdangerous import BadSignature, URLSafeTimedSerializer

TOKEN_SALT = "auth-token"
TOKEN_MAX_AGE_SEGUNDOS = 3600


class TokenService:
    def __init__(self, secret_key, max_age=TOKEN_MAX_AGE_SEGUNDOS):
        self._serializer = URLSafeTimedSerializer(secret_key, salt=TOKEN_SALT)
        self._max_age = max_age

    def gerar(self, usuario_id, tipo):
        return self._serializer.dumps({"usuario_id": usuario_id, "tipo": tipo})

    def validar(self, token):
        """Retorna o payload do token, ou None se inválido/expirado."""
        try:
            return self._serializer.loads(token, max_age=self._max_age)
        except BadSignature:
            return None
