/**
 * Serviço de domínio do checkout (RP-05): orquestra curso → gateway →
 * usuário → transação atômica (user → enrollment → payment → audit, RP-07)
 * → notificação. Testável sem HTTP; dependências injetadas pelo composition
 * root.
 */
const { NotFoundError, PaymentDeniedError } = require('../errors');

class CheckoutService {
    constructor({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        paymentGateway,
        passwordService,
        notificationService,
    }) {
        this.db = db;
        this.userModel = userModel;
        this.courseModel = courseModel;
        this.enrollmentModel = enrollmentModel;
        this.paymentModel = paymentModel;
        this.auditLogModel = auditLogModel;
        this.paymentGateway = paymentGateway;
        this.passwordService = passwordService;
        this.notificationService = notificationService;
    }

    async checkout({ name, email, password, courseId, cardNumber }) {
        const course = await this.courseModel.findActiveById(courseId);
        if (!course) throw new NotFoundError('Curso não encontrado');

        const charge = await this.paymentGateway.charge({ cardNumber, amount: course.price });
        if (!charge.approved) throw new PaymentDeniedError();

        const existingUser = await this.userModel.findByEmail(email);
        const passwordHash = existingUser ? null : await this.passwordService.hash(password);

        const { userId, enrollmentId } = await this.db.withTransaction(async () => {
            const user = existingUser || (await this.userModel.create({ name, email, passwordHash }));
            const newEnrollmentId = await this.enrollmentModel.create(user.id, courseId);
            await this.paymentModel.create(newEnrollmentId, course.price, charge.status);
            await this.auditLogModel.record(`Checkout curso ${courseId} por ${user.id}`);
            return { userId: user.id, enrollmentId: newEnrollmentId };
        });

        await this.notificationService.sendCheckoutConfirmation({ userId, courseTitle: course.title });
        return { enrollmentId };
    }
}

module.exports = { CheckoutService };
