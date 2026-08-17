/**
 * Rotas de autenticação: POST /api/login emite o Bearer token usado pelas
 * rotas protegidas (/api/admin/* e DELETE /api/users/:id).
 */
const { Router } = require('express');
const { validateLogin } = require('../middlewares/validation');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createAuthRoutes({ authController }) {
    const router = Router();
    router.post('/login', validateLogin, asyncHandler(authController.login));
    return router;
}

module.exports = { createAuthRoutes };
