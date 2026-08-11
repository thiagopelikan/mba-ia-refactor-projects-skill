/**
 * Controller de usuários: remoção transacional em cascata (RP-07) — sem
 * órfãos em enrollments/payments. Usuário inexistente → 404 (o legado
 * respondia 200 incondicional e ignorava o erro).
 */
const { NotFoundError } = require('../errors');

function createUserController({ userModel }) {
    async function remove(req, res) {
        const { deleted } = await userModel.deleteWithRelations(req.userId);
        if (!deleted) {
            throw new NotFoundError('Usuário não encontrado');
        }
        res.status(200).json({ msg: 'Usuário removido junto com matrículas e pagamentos' });
    }

    return { remove };
}

module.exports = { createUserController };
