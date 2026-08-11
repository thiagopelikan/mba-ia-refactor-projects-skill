/**
 * Controller de checkout: entrada já validada (middleware) → serviço de
 * domínio → resposta. Contrato preservado: 200 {msg, enrollment_id}.
 */
function createCheckoutController({ checkoutService }) {
    async function checkout(req, res) {
        const { enrollmentId } = await checkoutService.checkout(req.checkoutInput);
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }

    return { checkout };
}

module.exports = { createCheckoutController };
