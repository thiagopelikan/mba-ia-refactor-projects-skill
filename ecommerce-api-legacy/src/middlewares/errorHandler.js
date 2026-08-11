/**
 * Error handler central (RP-08): único ponto que converte erros em resposta
 * HTTP JSON padronizada. Erros inesperados viram 500 genérico (sem vazar
 * stack) com log completo no servidor. Nunca loga o corpo da requisição
 * (pode conter cartão/senha).
 */
const { ApiError } = require('../errors');

function resolveStatus(err) {
    if (err instanceof ApiError) return err.status;
    // Erros do body parser (JSON malformado → 400, payload grande → 413).
    if (typeof err.status === 'number' && err.status >= 400 && err.status < 500) return err.status;
    return 500;
}

function createErrorHandler(logger) {
    // Assinatura (err, req, res, next) obrigatória para o Express reconhecer.
    // eslint-disable-next-line no-unused-vars
    return (err, req, res, next) => {
        const status = resolveStatus(err);
        let message;
        if (err instanceof ApiError) {
            message = err.message;
        } else if (status === 500) {
            message = 'Erro interno';
        } else {
            message = 'Requisição inválida';
        }

        if (status >= 500) {
            logger.error('http.unhandled-error', {
                method: req.method,
                path: req.originalUrl,
                error: err.message,
                stack: err.stack,
            });
        } else {
            logger.warn('http.request-error', {
                method: req.method,
                path: req.originalUrl,
                status,
                error: err.message,
            });
        }

        res.status(status).json({ error: message });
    };
}

module.exports = { createErrorHandler };
