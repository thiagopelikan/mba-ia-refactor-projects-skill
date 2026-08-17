/**
 * Serviço de autenticação (RP-12): valida credenciais (bcrypt via
 * PasswordService) e emite o Bearer token exigido pelas rotas protegidas.
 * Nunca loga senha nem token. Email inexistente e senha errada produzem o
 * MESMO erro 401; uma comparação bcrypt "chamariz" iguala o tempo de
 * resposta para não vazar a existência do usuário por timing.
 */
const crypto = require('crypto');
const { AuthError } = require('../errors');

const DECOY_PASSWORD_BYTES = 24;

class AuthService {
    constructor({ userModel, passwordService, tokenService }) {
        this.userModel = userModel;
        this.passwordService = passwordService;
        this.tokenService = tokenService;
        // Hash de uma senha aleatória, usado quando o email não existe.
        this.decoyHashPromise = passwordService.hash(
            crypto.randomBytes(DECOY_PASSWORD_BYTES).toString('base64url'),
        );
    }

    async login({ email, password }) {
        const credentials = await this.userModel.findCredentialsByEmail(email);
        const passwordHash = credentials ? credentials.passwordHash : await this.decoyHashPromise;
        const passwordMatches = await this.passwordService.compare(password, passwordHash);
        if (!credentials || !passwordMatches) {
            throw new AuthError('Credenciais inválidas');
        }
        return { token: this.tokenService.issue(credentials.id) };
    }
}

module.exports = { AuthService };
