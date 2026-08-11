# task-manager-api

API de Task Manager em Python/Flask usada como entrada do desafio `refactor-arch`. Após a Fase 3, o projeto segue MVC adaptado: `config/` (env vars), `models/` (dados + regras de domínio), `controllers/` (orquestração), `routes/` (blueprints finos), `middlewares/` (error handler central + infra de auth) e `app.py` como composition root (App Factory).

## Como rodar

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Configuração via ambiente (obrigatório: SECRET_KEY)
cp .env.example .env
python -c "import secrets; print(secrets.token_hex(32))"   # cole o valor em SECRET_KEY no .env

python seed.py   # popula o SQLite (instance/tasks.db) em transação única
python app.py    # sobe em http://HOST:PORT (default 127.0.0.1:5000)
```

As senhas dos usuários de seed vêm de `SEED_DEFAULT_PASSWORD` no `.env`; se vazia, o seed gera senhas aleatórias e as imprime uma única vez no console.

## Estrutura

```
config/settings.py           # toda configuração via env vars (.env.example documenta)
app.py                       # App Factory create_app() — só composição
database.py                  # objeto db (Flask-SQLAlchemy)
models/                      # schema + regras de domínio + queries (SQLAlchemy 2.x)
controllers/                 # validação → model → resposta, por domínio
routes/                      # blueprints finos (task, user, auth, category, report, main)
middlewares/error_handler.py # error handling central (exceções tipadas → JSON)
middlewares/auth.py          # token assinado + @auth_required/@admin_required (infra)
utils/helpers.py             # constantes e validadores canônicos do domínio
seed.py                      # dados de exemplo (transação única, senhas via env/aleatórias)
```

Nota: os decorators de auth existem mas não estão aplicados às rotas do contrato original — limitação aceita para preservar o baseline (ver relatório da Fase 3).
