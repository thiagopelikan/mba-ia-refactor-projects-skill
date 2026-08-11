/**
 * Envolve handlers async para que rejeições cheguem ao error handler
 * central via next(err) (RP-08/RP-13) — Express 4 não faz isso sozinho.
 */
function asyncHandler(handler) {
    return (req, res, next) => {
        Promise.resolve(handler(req, res, next)).catch(next);
    };
}

module.exports = { asyncHandler };
