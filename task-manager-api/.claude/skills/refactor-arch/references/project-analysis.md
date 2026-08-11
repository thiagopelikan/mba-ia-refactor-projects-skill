# Análise de Projeto (Fase 1)

Heurísticas para detectar linguagem, framework, banco de dados, domínio e arquitetura de **qualquer** projeto backend. Aplique-as na ordem abaixo e sempre cite a evidência (arquivo/linha) que sustentou cada detecção.

## 1. Detecção de linguagem

Combine **extensão dos arquivos-fonte** + **arquivo de manifesto**. O manifesto é a evidência mais forte.

| Linguagem | Extensões | Manifesto(s) | Sinais adicionais |
|---|---|---|---|
| Python | `.py` | `requirements.txt`, `pyproject.toml`, `Pipfile` | shebang `#!/usr/bin/env python`, `__init__.py` |
| Node.js (JS/TS) | `.js`, `.mjs`, `.ts` | `package.json` (+ `package-lock.json`/`yarn.lock`) | `node_modules/`, `"scripts"` no package.json |
| Ruby | `.rb` | `Gemfile` | `config.ru`, `Rakefile` |
| PHP | `.php` | `composer.json` | `index.php`, `artisan` (Laravel) |
| Java/Kotlin | `.java`, `.kt` | `pom.xml`, `build.gradle` | `src/main/java` |
| Go | `.go` | `go.mod` | `main.go`, `func main()` |
| C#/.NET | `.cs` | `*.csproj`, `*.sln` | `Program.cs`, `Startup.cs` |

Regra: liste os arquivos do projeto (ignorando `node_modules/`, `.venv/`, `venv/`, `.git/`, `.claude/`, `dist/`, `build/`), conte por extensão e confirme com o manifesto. Se houver conflito (ex.: `.py` e `.js`), a linguagem do backend é a do manifesto que declara o framework web.

## 2. Detecção de framework + versão

Leia o manifesto e **extraia a versão pinada**; depois confirme por imports no código.

**Python** — em `requirements.txt` / `pyproject.toml`:

| Dependência | Framework | Confirmação no código |
|---|---|---|
| `flask==X.Y.Z` | Flask X.Y.Z | `from flask import Flask`, `app = Flask(__name__)` |
| `django==X.Y.Z` | Django | `manage.py`, `from django...` |
| `fastapi==X.Y.Z` | FastAPI | `from fastapi import FastAPI` |
| `flask-sqlalchemy` | Flask + ORM SQLAlchemy | `from flask_sqlalchemy import SQLAlchemy`, `db.Model` |

**Node** — em `package.json` → `dependencies`:

| Dependência | Framework | Confirmação no código |
|---|---|---|
| `"express": "^X.Y.Z"` | Express X.Y.Z | `require('express')` / `import express` |
| `"koa"` | Koa | `require('koa')` |
| `"fastify"` | Fastify | `require('fastify')` |
| `"@nestjs/core"` | NestJS | decorators `@Controller` |

Versão: use a pinada (`flask==3.1.1` → "Flask 3.1.1"; `"express": "^4.18.2"` → "Express 4.18.2"). Se não houver pin, reporte o range e diga que não está pinada.

Anote também **dependências declaradas e nunca importadas** (compare o manifesto com os imports reais) — isso vira finding LOW na Fase 2 (dead dependency).

## 3. Detecção de banco de dados

Procure, nesta ordem:

1. **Drivers/ORMs no manifesto e imports:** `sqlite3` (builtin Python), `psycopg2`, `pymysql`, `sqlalchemy`/`flask_sqlalchemy`, e em Node: `sqlite3`, `pg`, `mysql2`, `mongoose`, `sequelize`, `prisma`.
2. **Strings de conexão:** `sqlite:///arquivo.db`, `:memory:`, `postgres://`, `mysql://`, `mongodb://`, `SQLALCHEMY_DATABASE_URI`.
3. **DDL cru:** `grep` por `CREATE TABLE` — cada `CREATE TABLE nome (...)` dá o nome de uma tabela.
4. **Models de ORM:** classes com `db.Model`/`Base` (SQLAlchemy) → `__tablename__` ou nome da classe em minúsculo/plural; schemas do Mongoose/Sequelize em Node.

Liste **todas as tabelas** encontradas (via DDL ou models) — elas entram no campo `DB tables:` do resumo. Registre também peculiaridades: SQLite em `:memory:` (dados perdidos a cada restart), `db.create_all()` executado no import, seeds com dados sensíveis.

## 4. Detecção de domínio

Infira o domínio de negócio dos **nomes de tabelas, rotas e entidades** — nunca chute sem evidência:

| Sinais (tabelas/rotas) | Domínio provável |
|---|---|
| `produtos`, `pedidos`, `usuarios`, `itens_pedido`, `/carrinho` | E-commerce API |
| `courses`, `enrollments`, `payments`, `students`, `/checkout` | LMS / plataforma de cursos com checkout |
| `tasks`, `categories`, `users`, `/tasks`, `/login` | Task Manager API |
| `posts`, `comments`, `likes` | Rede social / blog |
| `appointments`, `patients`, `doctors` | Saúde / agendamento |

Descreva o domínio em uma linha citando as entidades: ex. `E-commerce API (produtos, pedidos, usuários)`.

## 5. Mapeamento da arquitetura atual

1. **Conte arquivos-fonte e LoC** (só código da aplicação; exclua lockfiles, `node_modules/`, `.venv/`, `.claude/`, testes gerados).
2. **Identifique o entry point:** arquivo com `app.run(...)` / `app.listen(...)` / `if __name__ == "__main__"` / `"main"`+`"scripts".start` no package.json. Anote a **porta** e como a app inicia (`python app.py`, `npm start`).
3. **Classifique a arquitetura** em uma das três categorias:

| Classificação | Sinais |
|---|---|
| **Monolito procedural / God Class** | Tudo em 1-4 arquivos; um arquivo/classe concentra DB + regra de negócio + rotas + serialização; funções gigantes; nenhum diretório de camada |
| **Parcialmente em camadas** | Existem diretórios `models/`, `routes/`, `services/`, `utils/`, mas com violações: lógica de negócio dentro das rotas, camadas de fachada nunca importadas (código morto), utils duplicando services |
| **MVC** | Camadas Config, Models, Views/Routes, Controllers, Middlewares presentes e respeitando Routes → Controllers → Models |

4. **Detecte padrões existentes:** blueprints Flask (`Blueprint(...)`, `register_blueprint`), application factory (`create_app()`), roteamento manual (`@app.route` direto no entry point), classe única gerenciando tudo (ex.: `AppManager`), middlewares registrados.
5. **Cuidado com camadas de fachada:** a existência de `services/` ou `utils/` NÃO prova que são usados. Verifique os **imports reais**: se nenhuma rota importa `services/`, a camada é código morto — registre isso na descrição da arquitetura (vira finding na Fase 2).
6. **Mapeie todos os endpoints (método + path)** — `@app.route`/`@bp.route` em Flask, `app.get/post/put/delete` ou `router.*` em Express. Essa lista é o contrato que a Fase 3 preserva.

## 6. Como imprimir o resumo

Template do bloco (linhas alinhadas, rótulos em inglês, valores em português quando descritivos):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:     Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

Preencha cada campo com o que foi detectado nas seções 1-5. `Dependencies:` lista as dependências diretas relevantes além do framework. `Architecture:` traz a classificação + uma descrição curta com evidência.

## 7. Worked examples — os 3 stacks-alvo (prova de agnosticismo)

Resultado esperado da detecção em três projetos reais de perfis diferentes:

| Campo | Projeto A (Flask cru) | Projeto B (Express) | Projeto C (Flask + ORM) |
|---|---|---|---|
| Language | Python | JavaScript (Node.js) | Python |
| Framework | Flask 3.1.1 (`requirements.txt`) | Express 4.18.2 (`package.json`) | Flask 3.0.0 + Flask-SQLAlchemy (`requirements.txt`) |
| DB | SQLite via `sqlite3` + SQL cru concatenado | SQLite via `sqlite3` em `:memory:` (dados voláteis) | SQLite via SQLAlchemy ORM (`db.Model`) |
| Domain | E-commerce (produtos, pedidos, usuários) | LMS com checkout (courses, enrollments, payments) | Task Manager (tasks, categories, users) |
| Architecture | Monolito procedural — God Module, 4 arquivos na raiz | God Class (ex.: `AppManager`) concentrando DB + regras + email + rotas | Parcialmente em camadas — `models/`, `routes/` usados; `services/` e `utils/` são fachada/código morto |
| Tabelas | via `CREATE TABLE` em `database.py` | via `CREATE TABLE` no boot | via models `db.Model` |

Se o projeto analisado não bater com nenhum perfil, aplique as heurísticas genéricas das seções 1-5 — elas não dependem de stack.
