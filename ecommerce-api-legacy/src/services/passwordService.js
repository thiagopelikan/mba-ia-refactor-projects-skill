/**
 * Hash de senha real com bcrypt (RP-04): salt embutido, custo configurável.
 * Substitui o antigo badCrypto (reversível e sem salt).
 */
const bcrypt = require('bcrypt');

class PasswordService {
    constructor(saltRounds) {
        this.saltRounds = saltRounds;
    }

    hash(plainTextPassword) {
        return bcrypt.hash(plainTextPassword, this.saltRounds);
    }

    compare(plainTextPassword, passwordHash) {
        return bcrypt.compare(plainTextPassword, passwordHash);
    }
}

module.exports = { PasswordService };
