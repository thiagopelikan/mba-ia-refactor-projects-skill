/**
 * Rotas administrativas. authMiddleware é opcional (ENFORCE_AUTH=1):
 * por padrão desligado para preservar o contrato do baseline (AP-06 —
 * limitação aceita, documentada no README).
 */
const { Router } = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createAdminRoutes({ reportController, authMiddleware }) {
    const router = Router();
    if (authMiddleware) router.use(authMiddleware);
    router.get('/financial-report', asyncHandler(reportController.getFinancialReport));
    return router;
}

module.exports = { createAdminRoutes };
