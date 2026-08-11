/**
 * Validação de entrada (RP-11): presença + tipo antes de qualquer uso.
 * Payload inválido → 400 via ValidationError (nunca 500, nunca crash).
 * Os nomes dos campos JSON (usr/eml/pwd/c_id/card) são contrato externo e
 * foram preservados; internamente viram nomes completos (RP-15).
 */
const { ValidationError } = require('../errors');

const EMAIL_PATTERN = /^\S+@\S+\.\S+$/;
const CARD_NUMBER_PATTERN = /^\d+$/;

function isNonEmptyString(value) {
    return typeof value === 'string' && value.trim() !== '';
}

function parsePositiveInteger(value) {
    if (Number.isInteger(value) && value > 0) return value;
    if (typeof value === 'string' && /^\d+$/.test(value)) {
        const parsed = Number.parseInt(value, 10);
        return parsed > 0 ? parsed : null;
    }
    return null;
}

function validateCheckout(req, res, next) {
    const body = req.body || {};
    const { usr, eml, pwd, c_id: rawCourseId, card } = body;

    if (!isNonEmptyString(usr)) {
        return next(new ValidationError("campo 'usr' é obrigatório e deve ser texto"));
    }
    if (!isNonEmptyString(eml) || !EMAIL_PATTERN.test(eml.trim())) {
        return next(new ValidationError("campo 'eml' é obrigatório e deve ser um email válido"));
    }
    if (!isNonEmptyString(pwd)) {
        return next(new ValidationError("campo 'pwd' é obrigatório e deve ser texto"));
    }
    const courseId = parsePositiveInteger(rawCourseId);
    if (courseId === null) {
        return next(new ValidationError("campo 'c_id' é obrigatório e deve ser um inteiro positivo"));
    }
    // Cartão DEVE ser string de dígitos: um número JSON aqui derrubava o
    // processo no legado (cc.startsWith is not a function) — agora é 400.
    if (typeof card !== 'string' || !CARD_NUMBER_PATTERN.test(card)) {
        return next(new ValidationError("campo 'card' é obrigatório e deve ser uma string de dígitos"));
    }

    req.checkoutInput = {
        name: usr.trim(),
        email: eml.trim(),
        password: pwd,
        courseId,
        cardNumber: card,
    };
    return next();
}

function validateUserIdParam(req, res, next) {
    const userId = parsePositiveInteger(req.params.id);
    if (userId === null) {
        return next(new ValidationError("parâmetro 'id' deve ser um inteiro positivo"));
    }
    req.userId = userId;
    return next();
}

module.exports = { validateCheckout, validateUserIdParam };
