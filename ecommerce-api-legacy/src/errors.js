/**
 * Erros tipados da aplicação (RP-08): controllers/services lançam;
 * o middleware central converte em resposta HTTP JSON padronizada.
 */
class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.name = this.constructor.name;
        this.status = status;
    }
}

class ValidationError extends ApiError {
    constructor(message) {
        super(message, 400);
    }
}

class PaymentDeniedError extends ApiError {
    constructor(message = 'Pagamento recusado') {
        super(message, 400);
    }
}

class NotFoundError extends ApiError {
    constructor(message = 'Recurso não encontrado') {
        super(message, 404);
    }
}

class AuthError extends ApiError {
    constructor(message = 'Não autenticado') {
        super(message, 401);
    }
}

module.exports = { ApiError, ValidationError, PaymentDeniedError, NotFoundError, AuthError };
