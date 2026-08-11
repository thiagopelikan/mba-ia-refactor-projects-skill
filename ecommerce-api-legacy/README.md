# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express — refatorada para arquitetura MVC na Fase 3 do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start          # ou: node src/app.js (entry point inalterado)
```

A aplicação sobe em `http://localhost:3000` (configurável via `PORT`). O banco SQLite é em memória e carrega o seed automaticamente no boot. Exemplos de requisições em `api.http`.

Configuração via variáveis de ambiente (opcionalmente em um arquivo `.env` — veja `.env.example`). Nenhuma variável é obrigatória para o boot em desenvolvimento.

## Estrutura (MVC)

```
src/
├── config/          # toda configuração via process.env (dotenv); zero hardcoded
├── db/              # conexão sqlite promisificada + transações; DDL/seed
├── models/          # 1 por domínio (user, course, enrollment, payment, auditLog); SQL parametrizado
├── services/        # gateway de pagamento, hash (bcrypt), notificação, token, checkout; logger
├── controllers/     # orquestram fluxo (checkout, report, user)
├── routes/          # Routers finos → controllers
├── middlewares/     # error handler central, 404, validação (400), auth (opcional)
├── errors.js        # erros tipados (400/401/404) consumidos pelo error handler
└── app.js           # composition root + entry point
```

## Endpoints (contrato preservado)

- `POST /api/checkout` — corpo `{usr, eml, pwd, c_id, card}`; cartão iniciando em `4` → 200 `{msg, enrollment_id}`; caso contrário 400 `{"error":"Pagamento recusado"}`. Payload inválido (ex.: `card` numérico) → **400** (antes derrubava o processo).
- `GET /api/admin/financial-report` — 200, array `{course, revenue, students:[{student, paid}]}` (agora com JOIN único).
- `DELETE /api/users/:id` — 200; remove usuário **e** matrículas/pagamentos na mesma transação (sem órfãos). Usuário inexistente → 404.

Erros agora são JSON padronizado `{"error": "..."}` (antes text/plain).

## Segurança / limitações registradas

- Credenciais/chaves saíram do código (env vars); número de cartão nunca é logado (apenas `****4444`); senhas com hash bcrypt.
- **Auth (AP-06 — limitação aceita):** a infraestrutura de autenticação (TokenService + middleware Bearer) está pronta, mas **desligada por padrão** para preservar o contrato do baseline (report e delete respondem 200 sem credencial). Ative com `ENFORCE_AUTH=1` para exigir token em `/api/admin/*` e `DELETE /api/users/:id`.
- Checkout com email de usuário existente não exige a senha desse usuário (comportamento herdado do legado, coberto pela mesma limitação AP-06).
