/**
 * Rotas de usuários (destrutivas — RP-12): authMiddleware é OBRIGATÓRIO
 * e aplicado a todas as rotas deste router. Sem Bearer token válido → 401.
 */
const { Router } = require('express');
const { validateUserIdParam } = require('../middlewares/validation');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createUserRoutes({ userController, authMiddleware }) {
    if (typeof authMiddleware !== 'function') {
        throw new Error('createUserRoutes exige um authMiddleware — rota destrutiva não sobe sem auth');
    }
    const router = Router();
    router.use(authMiddleware);
    router.delete('/:id', validateUserIdParam, asyncHandler(userController.remove));
    return router;
}

module.exports = { createUserRoutes };
