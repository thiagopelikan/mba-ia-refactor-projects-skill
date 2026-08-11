/**
 * Model de auditoria. O erro de INSERT NUNCA é engolido (RP-08): dentro da
 * transação de checkout, falha de auditoria reverte o fluxo inteiro.
 */
class AuditLogModel {
    constructor(db) {
        this.db = db;
    }

    async record(action) {
        const { lastID } = await this.db.run(
            "INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))",
            [action],
        );
        return lastID;
    }
}

module.exports = { AuditLogModel };
