/**
 * Infra de banco (RP-13): promisifica o driver sqlite3 na borda, uma única vez.
 * O wrapper run() usa function regular no callback para preservar this.lastID e
 * this.changes (promisify perderia esses valores).
 * withTransaction (RP-07) serializa transações e garante BEGIN/COMMIT/ROLLBACK.
 */
const sqlite3 = require('sqlite3');

function createDatabase(storage) {
    const driver = new sqlite3.Database(storage);

    function run(sql, params = []) {
        return new Promise((resolve, reject) => {
            driver.run(sql, params, function onRun(err) {
                if (err) reject(err);
                else resolve({ lastID: this.lastID, changes: this.changes });
            });
        });
    }

    function get(sql, params = []) {
        return new Promise((resolve, reject) => {
            driver.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        });
    }

    function all(sql, params = []) {
        return new Promise((resolve, reject) => {
            driver.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        });
    }

    function close() {
        return new Promise((resolve, reject) => {
            driver.close((err) => (err ? reject(err) : resolve()));
        });
    }

    // Fila de transações: garante que duas transações concorrentes não intercalem
    // BEGIN/COMMIT na mesma conexão.
    let transactionQueue = Promise.resolve();

    function withTransaction(work) {
        const execute = async () => {
            await run('BEGIN');
            try {
                const result = await work();
                await run('COMMIT');
                return result;
            } catch (err) {
                try {
                    await run('ROLLBACK');
                } catch (rollbackErr) {
                    err.rollbackError = rollbackErr;
                }
                throw err;
            }
        };
        const result = transactionQueue.then(execute);
        transactionQueue = result.catch(() => {});
        return result;
    }

    return { driver, run, get, all, close, withTransaction };
}

module.exports = { createDatabase };
