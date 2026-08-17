/**
 * Middleware de autenticação (RP-12, corrige AP-05/AP-06): verifica Bearer
 * token via TokenService. Aplicado SEMPRE (sem flag de desligar) às rotas
 * sensíveis/destrutivas: /api/admin/* e DELETE /api/users/:id.
 * Sem token ou token inválido → 401. Token obtido em POST /api/login.
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
