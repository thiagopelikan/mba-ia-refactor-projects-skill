/**
 * Config central (RP-01): toda configuração vem de variáveis de ambiente.
 * Nenhum valor sensível hardcoded; chaves documentadas em .env.example.
 */
const path = require('path');

require('dotenv').config({ path: path.resolve(__dirname, '..', '..', '.env') });

function integerFromEnv(name, defaultValue) {
    const raw = process.env[name];
    if (raw === undefined || raw === '') return defaultValue;
    const parsed = Number.parseInt(raw, 10);
    if (Number.isNaN(parsed)) {
        throw new Error(`Config inválida: ${name} deve ser um número inteiro (recebido: "${raw}")`);
    }
    return parsed;
}

module.exports = {
    port: integerFromEnv('PORT', 3000),
    jsonBodyLimit: process.env.JSON_BODY_LIMIT || '100kb',
    logLevel: process.env.LOG_LEVEL || 'info',

    database: {
        // ':memory:' recria o banco (com seed) a cada boot — comportamento original preservado.
        storage: process.env.DATABASE_STORAGE || ':memory:',
        // Reservados para um banco com autenticação (não usados pelo sqlite em memória).
        user: process.env.DB_USER || '',
        pass: process.env.DB_PASS || '',
    },

    paymentGateway: {
        apiKey: process.env.PAYMENT_GATEWAY_KEY || '',
    },

    smtp: {
        host: process.env.SMTP_HOST || '',
        port: integerFromEnv('SMTP_PORT', 587),
        user: process.env.SMTP_USER || '',
        pass: process.env.SMTP_PASS || '',
    },

    auth: {
        // Se vazio, o TokenService gera um secret efêmero por boot (tokens não sobrevivem a restart).
        tokenSecret: process.env.AUTH_TOKEN_SECRET || '',
        tokenTtlSeconds: integerFromEnv('AUTH_TOKEN_TTL_SECONDS', 3600),
        // Auth SEMPRE ligada (RP-12): /api/admin/* e DELETE /api/users/:id exigem
        // Bearer token obtido em POST /api/login. Não há flag para desligar.
    },

    seed: {
        // Se vazio, o seed gera uma senha aleatória por boot (nunca senha em claro no código).
        userPassword: process.env.SEED_USER_PASSWORD || '',
    },

    bcryptCost: integerFromEnv('BCRYPT_COST', 10),
};
