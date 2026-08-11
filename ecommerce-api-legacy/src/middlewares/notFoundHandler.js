/**
 * Handler 404 central (RP-08): registrado depois de todas as rotas.
 */
function notFoundHandler(req, res) {
    res.status(404).json({ error: 'Rota não encontrada' });
}

module.exports = { notFoundHandler };
