/**
 * Middleware de autenticação (AP-06 — infra pronta): verifica Bearer token
 * via TokenService. NÃO é aplicado às rotas do baseline por padrão
 * (ENFORCE_AUTH=0) — exigi-lo mudaria os status de contrato (200 → 401).
 * Limitação aceita e documentada; ligar com ENFORCE_AUTH=1.
 */
const { AuthError } = require('../errors');

const BEARER_PREFIX = 'Bearer ';

function createAuthMiddleware(tokenService) {
    return (req, res, next) => {
        const header = req.headers.authorization || '';
        if (!header.startsWith(BEARER_PREFIX)) {
            return next(new AuthError('Não autenticado'));
        }
        const payload = tokenService.verify(header.slice(BEARER_PREFIX.length));
        if (!payload) {
            return next(new AuthError('Token inválido'));
        }
        req.auth = payload;
        return next();
    };
}

module.exports = { createAuthMiddleware };
