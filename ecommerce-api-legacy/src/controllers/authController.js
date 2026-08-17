/**
 * Controller de autenticação: entrada já validada (middleware) → AuthService
 * → resposta 200 { token }. O token nunca é logado.
 */
function createAuthController({ authService }) {
    async function login(req, res) {
        const { token } = await authService.login(req.loginInput);
        res.status(200).json({ token });
    }

    return { login };
}

module.exports = { createAuthController };
