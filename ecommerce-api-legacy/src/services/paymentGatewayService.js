/**
 * Gateway de pagamento como serviço injetável (RP-05). A regra herdada do
 * gateway simulado (cartão iniciando em "4" → aprovado) fica encapsulada
 * aqui, atrás de uma constante nomeada — preserva o contrato do baseline.
 * NUNCA loga o número completo do cartão nem a chave da API (RP-04):
 * apenas os 4 últimos dígitos, mascarados.
 */
const { PAYMENT_STATUS } = require('../models/paymentModel');

const APPROVED_CARD_PREFIX = '4';
const MASK_VISIBLE_DIGITS = 4;

function maskCardNumber(cardNumber) {
    return `****${String(cardNumber).slice(-MASK_VISIBLE_DIGITS)}`;
}

class PaymentGatewayService {
    constructor({ apiKey, logger }) {
        this.apiKey = apiKey; // usada por um gateway real; jamais logada
        this.logger = logger;
    }

    async charge({ cardNumber, amount }) {
        const approved = cardNumber.startsWith(APPROVED_CARD_PREFIX);
        this.logger.info('payment.gateway.charge', {
            card: maskCardNumber(cardNumber),
            amount,
            approved,
        });
        return { approved, status: approved ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED };
    }
}

module.exports = { PaymentGatewayService, maskCardNumber };
