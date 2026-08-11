/**
 * Rotas de checkout: finas — validação (middleware) + delegação ao controller.
 */
const { Router } = require('express');
const { validateCheckout } = require('../middlewares/validation');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createCheckoutRoutes({ checkoutController }) {
    const router = Router();
    router.post('/checkout', validateCheckout, asyncHandler(checkoutController.checkout));
    return router;
}

module.exports = { createCheckoutRoutes };
