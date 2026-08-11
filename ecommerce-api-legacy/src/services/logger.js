/**
 * Logger estruturado (RP-15): substitui console.log; uma linha JSON por evento.
 * Dados sensíveis (cartão, senha, secrets) NUNCA passam por aqui — os chamadores
 * mascaram/omitem antes de logar.
 */
const LOG_LEVELS = { debug: 10, info: 20, warn: 30, error: 40 };

function createLogger({ level = 'info' } = {}) {
    const threshold = LOG_LEVELS[level] ?? LOG_LEVELS.info;

    function write(entryLevel, message, meta = {}) {
        if ((LOG_LEVELS[entryLevel] ?? LOG_LEVELS.info) < threshold) return;
        const entry = { time: new Date().toISOString(), level: entryLevel, message, ...meta };
        const line = `${JSON.stringify(entry)}\n`;
        if (entryLevel === 'warn' || entryLevel === 'error') {
            process.stderr.write(line);
        } else {
            process.stdout.write(line);
        }
    }

    return {
        debug: (message, meta) => write('debug', message, meta),
        info: (message, meta) => write('info', message, meta),
        warn: (message, meta) => write('warn', message, meta),
        error: (message, meta) => write('error', message, meta),
    };
}

module.exports = { createLogger };
