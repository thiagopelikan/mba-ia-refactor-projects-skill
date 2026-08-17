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
├── services/        # gateway de pagamento, hash (bcrypt), notificação, token, auth (login), checkout; logger
├── controllers/     # orquestram fluxo (checkout, report, user, auth)
├── routes/          # Routers finos → controllers
├── middlewares/     # error handler central, 404, validação (400), auth (obrigatória nas rotas sensíveis)
├── errors.js        # erros tipados (400/401/404) consumidos pelo error handler
└── app.js           # composition root + entry point
```

## Endpoints (contrato preservado — segurança vence contrato)

- `POST /api/checkout` — **público** (fluxo principal); corpo `{usr, eml, pwd, c_id, card}`; cartão iniciando em `4` → 200 `{msg, enrollment_id}`; caso contrário 400 `{"error":"Pagamento recusado"}`. Payload inválido (ex.: `card` numérico) → **400** (antes derrubava o processo).
- `POST /api/login` — **público**; corpo `{email, password}`; credenciais válidas → 200 `{token}`; inválidas → 401.
- `GET /api/admin/financial-report` — **exige `Authorization: Bearer <token>`** (sem/inválido → 401); com token → 200, array `{course, revenue, students:[{student, paid}]}` (JOIN único).
- `DELETE /api/users/:id` — **exige `Authorization: Bearer <token>`** (sem/inválido → 401); com token → 200; remove usuário **e** matrículas/pagamentos na mesma transação (sem órfãos). Usuário inexistente → 404.

Erros agora são JSON padronizado `{"error": "..."}` (antes text/plain).

## Autenticação (RP-12 — sempre ligada)

As rotas sensíveis/destrutivas (`/api/admin/*` e `DELETE /api/users/:id`) **exigem** Bearer token por padrão — não existe flag para desligar (a antiga `ENFORCE_AUTH` foi removida). Os status 401 sem token nessas rotas são a *correção* do finding AP-05/AP-06, não uma quebra de contrato.

Como obter um token:

1. Defina `SEED_USER_PASSWORD` no ambiente (ou `.env`) antes de subir a app — é a senha do usuário seed `leonan@fullcycle.com.br` (apenas o hash bcrypt é gravado).
2. `POST /api/login` com `{"email": "leonan@fullcycle.com.br", "password": "<SEED_USER_PASSWORD>"}` → `{"token": "..."}`.
3. Envie `Authorization: Bearer <token>` nas rotas protegidas.

Se `SEED_USER_PASSWORD` ficar vazio, o seed usa uma senha aleatória por boot (nunca logada) e o login do usuário seed fica indisponível — usuários criados via checkout continuam podendo logar com a senha usada no checkout.

## Segurança / limitações registradas

- Credenciais/chaves saíram do código (env vars); número de cartão nunca é logado (apenas `****4444`); senhas com hash bcrypt; senha e token nunca aparecem em logs.
- Checkout com email de usuário existente não exige a senha desse usuário (comportamento herdado do legado; o checkout permanece público por ser o fluxo principal).
- Sem `AUTH_TOKEN_SECRET` configurado, o secret do token é efêmero por boot: tokens não sobrevivem a restart.
