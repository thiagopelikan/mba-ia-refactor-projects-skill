/**
 * Infra de auth (RP-12): emissão/verificação de token assinado (HMAC-SHA256)
 * com expiração. Emitido por POST /api/login e verificado pelo middleware de
 * auth, aplicado por padrão às rotas sensíveis/destrutivas.
 */
const crypto = require('crypto');

const EPHEMERAL_SECRET_BYTES = 32;

class TokenService {
    constructor({ secret, ttlSeconds }) {
        // Sem AUTH_TOKEN_SECRET configurado, gera um secret efêmero por boot:
        // tokens não sobrevivem a restart, mas nada roda com secret vazio.
        this.secret = secret || crypto.randomBytes(EPHEMERAL_SECRET_BYTES).toString('hex');
        this.ttlSeconds = ttlSeconds;
    }

    sign(payload) {
        return crypto.createHmac('sha256', this.secret).update(payload).digest('base64url');
    }

    issue(subject) {
        const payload = Buffer.from(
            JSON.stringify({ sub: subject, exp: Date.now() + this.ttlSeconds * 1000 }),
        ).toString('base64url');
        return `${payload}.${this.sign(payload)}`;
    }

    verify(token) {
        if (typeof token !== 'string' || !token.includes('.')) return null;
        const [payload, signature] = token.split('.');
        const expected = this.sign(payload);
        const received = Buffer.from(signature);
        const wanted = Buffer.from(expected);
        if (received.length !== wanted.length || !crypto.timingSafeEqual(received, wanted)) return null;
        try {
            const data = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'));
            if (typeof data.exp !== 'number' || data.exp < Date.now()) return null;
            return data;
        } catch {
            return null;
        }
    }
}

module.exports = { TokenService };
