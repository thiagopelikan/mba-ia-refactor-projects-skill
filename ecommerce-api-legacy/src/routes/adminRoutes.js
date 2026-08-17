/**
 * Rotas administrativas (sensíveis — RP-12): authMiddleware é OBRIGATÓRIO
 * e aplicado a todas as rotas deste router. Sem Bearer token válido → 401.
 */
const { Router } = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createAdminRoutes({ reportController, authMiddleware }) {
    if (typeof authMiddleware !== 'function') {
        throw new Error('createAdminRoutes exige um authMiddleware — rotas administrativas não sobem sem auth');
    }
    const router = Router();
    router.use(authMiddleware);
    router.get('/financial-report', asyncHandler(reportController.getFinancialReport));
    return router;
}

module.exports = { createAdminRoutes };
