/**
 * Rotas de usuários. authMiddleware opcional (ver adminRoutes.js).
 */
const { Router } = require('express');
const { validateUserIdParam } = require('../middlewares/validation');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createUserRoutes({ userController, authMiddleware }) {
    const router = Router();
    if (authMiddleware) router.use(authMiddleware);
    router.delete('/:id', validateUserIdParam, asyncHandler(userController.remove));
    return router;
}

module.exports = { createUserRoutes };
