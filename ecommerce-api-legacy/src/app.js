/**
 * Composition root (RP-03): monta a aplicação — config → infra (db/logger)
 * → models → services → controllers → rotas → middlewares de erro.
 * Zero lógica de negócio, zero SQL, zero rota inline.
 * Entry point: `node src/app.js` (inalterado).
 */
const express = require('express');

const config = require('./config');
const { createLogger } = require('./services/logger');
const { createDatabase } = require('./db/connection');
const { initDatabase } = require('./db/init');

const { UserModel } = require('./models/userModel');
const { CourseModel } = require('./models/courseModel');
const { EnrollmentModel } = require('./models/enrollmentModel');
const { PaymentModel } = require('./models/paymentModel');
const { AuditLogModel } = require('./models/auditLogModel');

const { PasswordService } = require('./services/passwordService');
const { PaymentGatewayService } = require('./services/paymentGatewayService');
const { NotificationService } = require('./services/notificationService');
const { TokenService } = require('./services/tokenService');
const { AuthService } = require('./services/authService');
const { CheckoutService } = require('./services/checkoutService');

const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createAuthController } = require('./controllers/authController');

const { createCheckoutRoutes } = require('./routes/checkoutRoutes');
const { createAdminRoutes } = require('./routes/adminRoutes');
const { createUserRoutes } = require('./routes/userRoutes');
const { createAuthRoutes } = require('./routes/authRoutes');

const { createAuthMiddleware } = require('./middlewares/auth');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { notFoundHandler } = require('./middlewares/notFoundHandler');

async function createApp() {
    const logger = createLogger({ level: config.logLevel });

    if (!config.paymentGateway.apiKey) {
        logger.warn('config.payment-gateway-key-ausente', {
            hint: 'defina PAYMENT_GATEWAY_KEY no ambiente (.env) para um gateway real',
        });
    }

    const db = createDatabase(config.database.storage);
    const passwordService = new PasswordService(config.bcryptCost);
    await initDatabase(db, {
        passwordService,
        seedUserPassword: config.seed.userPassword,
        logger,
    });

    const userModel = new UserModel(db);
    const courseModel = new CourseModel(db);
    const enrollmentModel = new EnrollmentModel(db);
    const paymentModel = new PaymentModel(db);
    const auditLogModel = new AuditLogModel(db);

    const paymentGateway = new PaymentGatewayService({ apiKey: config.paymentGateway.apiKey, logger });
    const notificationService = new NotificationService({ smtp: config.smtp, logger });
    const tokenService = new TokenService({
        secret: config.auth.tokenSecret,
        ttlSeconds: config.auth.tokenTtlSeconds,
    });
    const checkoutService = new CheckoutService({
        db,
        userModel,
        courseModel,
        enrollmentModel,
        paymentModel,
        auditLogModel,
        paymentGateway,
        passwordService,
        notificationService,
    });

    const authService = new AuthService({ userModel, passwordService, tokenService });

    const checkoutController = createCheckoutController({ checkoutService });
    const reportController = createReportController({ courseModel });
    const userController = createUserController({ userModel });
    const authController = createAuthController({ authService });

    // Auth SEMPRE ligada (RP-12): rotas sensíveis/destrutivas exigem Bearer token.
    const authMiddleware = createAuthMiddleware(tokenService);

    const app = express();
    app.use(express.json({ limit: config.jsonBodyLimit }));

    app.use('/api', createAuthRoutes({ authController }));
    app.use('/api', createCheckoutRoutes({ checkoutController }));
    app.use('/api/admin', createAdminRoutes({ reportController, authMiddleware }));
    app.use('/api/users', createUserRoutes({ userController, authMiddleware }));

    app.use(notFoundHandler);
    app.use(createErrorHandler(logger));

    return { app, logger, db };
}

async function start() {
    const { app, logger } = await createApp();
    app.listen(config.port, () => {
        logger.info('server.started', { port: config.port, authEnforced: true });
    });
}

if (require.main === module) {
    start().catch((err) => {
        process.stderr.write(
            `${JSON.stringify({ level: 'error', message: 'boot.failed', error: err.message })}\n`,
        );
        process.exit(1);
    });
}

module.exports = { createApp, start };
