# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.
Refatorada para arquitetura MVC (Fase 3): config por env vars, models por domínio,
rotas finas, controllers, error handling centralizado e composition root.

## Estrutura

```
├── app.py                  # entry point (delega para src/app.py)
├── .env.example            # variáveis de ambiente esperadas
└── src/
    ├── app.py              # composition root: monta app, injeta deps, registra rotas
    ├── config/settings.py  # configuração via env vars (zero hardcoded)
    ├── database.py         # conexão por request (flask.g) + schema/seed
    ├── exceptions.py       # exceções tipadas (400/401/404)
    ├── models/             # produto_model, usuario_model, pedido_model (SQL parametrizado)
    ├── controllers/        # produto, usuario, pedido, health (validação → model → resposta)
    ├── views/routes.py     # blueprints por domínio, handlers finos
    ├── middlewares/        # error_handler centralizado
    └── services/           # notificador (logging) e token_service (token assinado no login)
```

## Como rodar

```bash
pip install -r requirements.txt

# SECRET_KEY é obrigatória (a app não sobe sem ela):
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(32))')"

# macOS: a porta 5000 costuma estar ocupada pelo AirPlay Receiver — use outra:
PORT=5055 python app.py
```

A aplicação sobe em `http://127.0.0.1:$PORT` (host/porta configuráveis via `HOST`/`PORT`).
O banco SQLite (`loja.db`, configurável via `DATABASE_PATH`) é criado e seedado
automaticamente no boot — senhas do seed já são gravadas com hash.

Todas as variáveis de ambiente estão documentadas em [.env.example](.env.example).

## Mudanças de contrato (intencionais, por segurança)

- `POST /admin/query` e `POST /admin/reset-db` foram **removidos** (executavam SQL
  arbitrário/apagavam o banco, sem autenticação). Respondem 404.
- `GET /usuarios` e `GET /usuarios/<id>` **não devolvem mais o campo `senha`**;
  senhas agora são armazenadas com hash (werkzeug).
- `GET /health` devolve apenas status/contadores — **sem** `secret_key`, `db_path`
  ou `debug`.
- `POST /login` passou a devolver também `dados.token` (token assinado, verificável
  server-side).
