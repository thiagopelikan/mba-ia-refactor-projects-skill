/**
 * Model de usuários: único ponto de acesso à tabela users.
 * Serialização segura (RP-04): o hash de senha só sai via
 * findCredentialsByEmail (consumido exclusivamente pelo AuthService no
 * login) — nunca em findByEmail nem em qualquer resposta HTTP.
 */
class UserModel {
    constructor(db) {
        this.db = db;
    }

    findByEmail(email) {
        return this.db.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
    }

    /**
     * Uso restrito ao fluxo de login (AuthService): inclui o hash bcrypt
     * para comparação de senha. Não usar para serializar usuário.
     */
    findCredentialsByEmail(email) {
        return this.db.get('SELECT id, email, pass AS passwordHash FROM users WHERE email = ?', [email]);
    }

    async create({ name, email, passwordHash }) {
        const { lastID } = await this.db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
            name,
            email,
            passwordHash,
        ]);
        return { id: lastID, name, email };
    }

    /**
     * Remove o usuário e TODOS os registros relacionados na mesma transação
     * (RP-07): payments → enrollments → user. Nenhum órfão sobra.
     */
    deleteWithRelations(userId) {
        return this.db.withTransaction(async () => {
            await this.db.run(
                'DELETE FROM payments WHERE enrollment_id IN (SELECT id FROM enrollments WHERE user_id = ?)',
                [userId],
            );
            await this.db.run('DELETE FROM enrollments WHERE user_id = ?', [userId]);
            const { changes } = await this.db.run('DELETE FROM users WHERE id = ?', [userId]);
            return { deleted: changes > 0 };
        });
    }
}

module.exports = { UserModel };
