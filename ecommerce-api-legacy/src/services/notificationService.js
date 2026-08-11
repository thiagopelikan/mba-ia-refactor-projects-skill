/**
 * Notificação como colaborador injetável (RP-05/RP-06): substitui o antigo
 * logAndCache/globalCache. Sem SMTP configurado, registra o evento no logger
 * estruturado (sem dados sensíveis).
 */
class NotificationService {
    constructor({ smtp, logger }) {
        this.smtp = smtp;
        this.logger = logger;
    }

    async sendCheckoutConfirmation({ userId, courseTitle }) {
        // Um transporte SMTP real entraria aqui usando this.smtp (host/port/user/pass).
        this.logger.info('notification.checkout-confirmation', {
            userId,
            courseTitle,
            transport: this.smtp.host ? 'smtp' : 'log-only',
        });
    }
}

module.exports = { NotificationService };
