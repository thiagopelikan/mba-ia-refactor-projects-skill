# Skill `refactor-arch` — Plano de Implementação

> **Para workers agênticos:** SUB-SKILL OBRIGATÓRIA: use superpowers:subagent-driven-development (recomendado) ou superpowers:executing-plans para implementar este plano tarefa a tarefa. Os passos usam checkbox (`- [ ]`) para rastreamento.

**Goal:** Entregar uma Skill do Claude Code (`refactor-arch`) que analisa, audita e refatora qualquer projeto backend para o padrão MVC, agnóstica de tecnologia, validada nos 3 projetos legados do repositório.

**Architecture:** Uma skill de 3 fases sequenciais (Análise → Auditoria → Refatoração) onde o `SKILL.md` é o orquestrador (prompt) e 5 arquivos de referência em Markdown carregam o conhecimento de domínio (heurísticas de detecção, catálogo de anti-patterns, template de relatório, guidelines de MVC e playbook de refatoração). A skill é criada em `code-smells-project/.claude/skills/refactor-arch/` e copiada para os outros 2 projetos. A prova de agnosticismo é rodar as 3 fases nos 3 stacks (Flask sem camadas, Express God Class, Flask com camadas de fachada).

**Tech Stack:** Claude Code Custom Skills (Markdown). Projetos-alvo: Python/Flask + SQLite (`code-smells-project`), Node.js/Express + SQLite (`ecommerce-api-legacy`), Python/Flask + SQLAlchemy (`task-manager-api`).

## Global Constraints

- **Nome da skill:** `refactor-arch` (fixo, não alterar). Arquivo `SKILL.md` obrigatório.
- **Path (Claude Code):** `.claude/skills/refactor-arch/` dentro de cada projeto.
- **Formato dos arquivos de referência:** Markdown.
- **Escala de severidade (usar literalmente):** CRITICAL, HIGH, MEDIUM, LOW — conforme definições do README (§ Contexto).
- **Catálogo de anti-patterns:** mínimo 8 anti-patterns, com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW), **incluindo detecção de APIs deprecated**.
- **Playbook de refatoração:** mínimo 8 padrões de transformação, cada um com exemplo de código antes/depois.
- **Fase 2 deve pausar e pedir confirmação** (`[y/n]`) antes de modificar qualquer arquivo.
- **Fase 3 deve validar:** boot da aplicação sem erros + endpoints originais respondendo.
- **5 áreas de conhecimento obrigatórias** (README § Requisitos.2): Análise de projeto, Catálogo de anti-patterns, Template de relatório, Guidelines de arquitetura, Playbook de refatoração.
- **Relatórios de auditoria:** salvar em `reports/audit-project-{1,2,3}.md` (na raiz do repositório).
- **Critérios de aceite (nos 3 projetos):** Fase 1 detecta stack corretamente; Fase 2 ≥ 5 findings incluindo ≥ 1 CRITICAL/HIGH; Fase 3 aplicação funciona após refatoração.
- **Idioma:** relatórios e output da skill em português (alinhado ao README e exemplos).
- **Não quebrar contratos:** os endpoints originais (método + path) devem continuar respondendo após a refatoração.

---

## Contexto dos Projetos (insumo da análise manual)

Resumo consolidado da análise (usado nas Tasks 1, 8–10). Detalhes completos com arquivo/linha ficam no README (Task 1).

| | code-smells-project | ecommerce-api-legacy | task-manager-api |
|---|---|---|---|
| Stack | Python / Flask 3.1.1 | Node / Express 4.18.2 | Python / Flask 3.0.0 + SQLAlchemy 3.1.1 |
| Arquivos-fonte | 4 (~780 LoC) | 3 (~180 LoC) | 14 (~1155 LoC) |
| Endpoints | 19 | 3 | 22 |
| Banco | SQLite `loja.db`, SQL cru concatenado | SQLite `:memory:`, SQL parametrizado | SQLite `tasks.db`, ORM |
| Domínio | E-commerce (produtos, usuários, pedidos, relatório) | LMS/checkout (cursos, matrículas, pagamentos) | Task Manager (tasks, usuários, categorias, relatórios) |
| Pior problema | SQL injection total + `/admin/query` executando SQL arbitrário sem auth | `pk_live` hardcoded + nº de cartão logado + hash caseiro reversível | MD5 sem salt + hash devolvido no login |
| Padrão dominante | God Module procedural | God Class + callback hell + estado global | Camadas de fachada (models/routes/services vazios ou mortos) |

**Achados-chave por projeto** (mínimo a garantir na auditoria):

- **Projeto 1 (code-smells-project):** `/admin/query` executa SQL arbitrário sem auth (`app.py:59-78`, CRITICAL); SQL injection por concatenação (`models.py`, CRITICAL); senha em texto plano + vazada em `GET /usuarios` (`models.py:83,99`, CRITICAL); SECRET_KEY hardcoded (`app.py:7`, CRITICAL) e vazada em `/health` (`controllers.py:285-289`, CRITICAL); `/admin/reset-db` destrutivo sem auth (`app.py:47-57`, CRITICAL); God Module (`models.py:1-315`, CRITICAL); estado global de conexão thread-unsafe (`database.py:4-10`, HIGH); `debug=True` + `0.0.0.0` (`app.py:88`, HIGH); CORS aberto (`app.py:9`, HIGH); lógica/side-effects no controller (`controllers.py:208-210,247-250`, HIGH); N+1 query tripla (`models.py:171-233`, MEDIUM); validação ausente (MEDIUM); magic numbers/strings (LOW); `print()` como logging (LOW); imports mortos (`models.py:2`,`database.py:2`, LOW).

- **Projeto 2 (ecommerce-api-legacy):** credenciais de produção hardcoded incl. `pk_live` e SMTP (`utils.js:1-7`, CRITICAL); nº de cartão + chave logados (`AppManager.js:45`, CRITICAL); hash caseiro reversível `badCrypto` (`utils.js:17-23`, CRITICAL); God Class `AppManager` (`AppManager.js:4-141`, CRITICAL); endpoints admin/destrutivos sem auth (`AppManager.js:80,131`, CRITICAL); estado global mutável + memory leak (`utils.js:9-10`, HIGH); callback hell 5 níveis (`AppManager.js:37-77`, HIGH); sem transação no checkout → escrita parcial (`AppManager.js:50-62`, HIGH); regra de pagamento no handler (`AppManager.js:46`, HIGH); erros ignorados/crash sem response (`AppManager.js:92,104,133`, HIGH); N+1 no relatório (`AppManager.js:83-126`, MEDIUM); `express.json()` sem limite/helmet (`app.js:6`, MEDIUM); DB `:memory:` hardcoded (`AppManager.js:7`, MEDIUM); nomes ruins (`u,e,p,cid,cc`, LOW); `console.log` como logging (LOW).

- **Projeto 3 (task-manager-api):** MD5 sem salt (`models/user.py:29,32`, CRITICAL); hash devolvido na API incl. no login (`models/user.py:21`, CRITICAL); SMTP hardcoded (`services/notification_service.py:7-10`, CRITICAL); SECRET_KEY hardcoded (`app.py:13`, CRITICAL); token falso previsível + sem verificação de auth (`user_routes.py:210`, CRITICAL); `debug=True` + `0.0.0.0` (`app.py:34`, HIGH); CORS aberto (`app.py:15`, HIGH); lógica de negócio nos controllers/God Method (`report_routes.py:12-101`, HIGH); `services/` código morto (HIGH); `utils/helpers.py` duplicado e não usado (HIGH); `db.create_all()` no import (`app.py:30-31`, HIGH); **API deprecated `datetime.utcnow()` (22x)** e **`Query.get()` (16x)** (MEDIUM); N+1 queries múltiplas (MEDIUM); `except:` nu (8x) (MEDIUM); validação ausente/crashes por tipo (MEDIUM); sem paginação (MEDIUM); deps não usadas (`marshmallow`,`requests`,`python-dotenv`, LOW); imports mortos (LOW); magic numbers (LOW).

---

## Estrutura de Arquivos (o que será criado)

```
mba-ia-refactor-projects-skill/
├── README.md                                       # ATUALIZAR (Tasks 1, 11)
├── reports/
│   ├── audit-project-1.md                          # Criar (Task 8)
│   ├── audit-project-2.md                          # Criar (Task 9)
│   └── audit-project-3.md                          # Criar (Task 10)
├── code-smells-project/
│   ├── .claude/skills/refactor-arch/               # A SKILL (Tasks 2-7)
│   │   ├── SKILL.md                                # Orquestrador 3 fases
│   │   └── references/
│   │       ├── project-analysis.md                # Área 1: heurísticas de detecção
│   │       ├── anti-patterns-catalog.md           # Área 2: catálogo (≥8, incl. deprecated)
│   │       ├── audit-report-template.md           # Área 3: template do relatório
│   │       ├── mvc-guidelines.md                  # Área 4: regras do MVC alvo
│   │       └── refactoring-playbook.md            # Área 5: playbook (≥8 antes/depois)
│   └── src/ ...                                     # Código refatorado (Task 8)
├── ecommerce-api-legacy/
│   ├── .claude/skills/refactor-arch/               # CÓPIA da skill (Task 9)
│   └── src/ ...                                     # Código refatorado (Task 9)
└── task-manager-api/
    ├── .claude/skills/refactor-arch/               # CÓPIA da skill (Task 10)
    └── src/ ...                                     # Código refatorado (Task 10)
```

**Responsabilidade de cada arquivo da skill:**

- **`SKILL.md`** — frontmatter (`name`, `description`) + prompt orquestrador. Define as 3 fases, quando ler cada referência, o gate de confirmação da Fase 2 e o passo de validação da Fase 3. É o único ponto de entrada; deve ser genérico (sem citar nome de projeto específico).
- **`references/project-analysis.md`** — como detectar linguagem/framework/versão/DB/domínio e mapear arquitetura, por evidência de arquivos (`requirements.txt`, `package.json`, imports, DDL).
- **`references/anti-patterns-catalog.md`** — catálogo de anti-patterns com sinais de detecção acionáveis e severidade; inclui seção de APIs deprecated por stack.
- **`references/audit-report-template.md`** — formato exato do relatório da Fase 2 (cabeçalho, summary, findings ordenados por severidade com arquivo/linha).
- **`references/mvc-guidelines.md`** — a arquitetura-alvo: camadas Models, Views/Routes, Controllers + config, middlewares, entry point; responsabilidades e regras de dependência.
- **`references/refactoring-playbook.md`** — ≥8 transformações concretas antes/depois, mapeadas aos anti-patterns.

---

### Task 1: Documentar Análise Manual no README

**Files:**
- Modify: `README.md` (adicionar seção "## Análise Manual" após a seção "## Referências" ou antes de "## Dicas Finais")

**Interfaces:**
- Consumes: dados consolidados na seção "Contexto dos Projetos" deste plano.
- Produces: seção "Análise Manual" que será referenciada pelo README final (Task 11).

- [ ] **Step 1: Escrever a seção "Análise Manual"**

Adicionar ao `README.md` uma seção com um subtópico por projeto. Para cada projeto documentar **no mínimo 5 problemas** com: nome do anti-pattern, arquivo:linha, severidade e justificativa (1-2 frases de por que é relevante). Garantir a distribuição mínima exigida pelo README (§ Requisitos.1): pelo menos 1 CRITICAL/HIGH, 2 MEDIUM e 2 LOW por projeto. Usar a tabela comparativa e os "achados-chave por projeto" da seção "Contexto dos Projetos" deste plano como fonte.

Formato sugerido por projeto:

```markdown
### Projeto 1 — code-smells-project (Python/Flask)

| # | Anti-pattern | Local | Severidade | Por que é relevante |
|---|---|---|---|---|
| 1 | Arbitrary SQL Execution endpoint | app.py:59-78 | CRITICAL | `/admin/query` executa SQL do body sem auth — equivale a shell no banco. |
| ... | ... | ... | ... | ... |
```

- [ ] **Step 2: Validar a distribuição de severidades**

Run: `grep -c "CRITICAL\|HIGH\|MEDIUM\|LOW" README.md`
Expected: contagem consistente com ≥5 problemas por projeto e a distribuição mínima (≥1 CRITICAL/HIGH, ≥2 MEDIUM, ≥2 LOW por projeto).

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: adiciona secao Analise Manual dos 3 projetos legados"
```

---

### Task 2: Criar o SKILL.md (orquestrador das 3 fases)

**Files:**
- Create: `code-smells-project/.claude/skills/refactor-arch/SKILL.md`

**Interfaces:**
- Produces: contrato de invocação da skill e a ordem de leitura dos 5 arquivos de referência (`references/*.md`). As Tasks 3-7 preenchem esses arquivos; o SKILL.md os referencia por path relativo.

- [ ] **Step 1: Escrever o frontmatter + corpo do SKILL.md**

Criar o arquivo com:

1. **Frontmatter YAML:**
```yaml
---
name: refactor-arch
description: Analisa, audita e refatora um projeto backend para o padrão MVC. Detecta stack (linguagem/framework/DB), cruza o código contra um catálogo de anti-patterns e code smells classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW), gera um relatório de auditoria, pede confirmação e então reestrutura o projeto para MVC validando que a aplicação continua funcionando. Agnóstica de tecnologia (Python/Flask, Node/Express e outros).
---
```

2. **Corpo (prompt orquestrador)** com estas seções:
   - **Visão geral:** a skill executa 3 fases sequenciais; nunca pular fases; sempre agnóstica de stack.
   - **Fase 1 — Análise:** ler `references/project-analysis.md`; detectar linguagem, framework+versão, dependências, banco de dados, domínio e arquitetura atual; imprimir o bloco-resumo no formato do README (§ exemplo "PHASE 1: PROJECT ANALYSIS": Language / Framework / Dependencies / Domain / Architecture / Source files / DB tables).
   - **Fase 2 — Auditoria:** ler `references/anti-patterns-catalog.md` e `references/audit-report-template.md`; cruzar cada arquivo-fonte contra o catálogo; produzir findings com **arquivo:linha exatos**, ordenados por severidade (CRITICAL → LOW); renderizar o relatório no formato do template; imprimir o `## Summary` com contagem por severidade; **PAUSAR e pedir confirmação** `Proceed with refactoring (Phase 3)? [y/n]` — **não modificar nenhum arquivo antes do `y`**. Salvar o relatório em `reports/audit-project-N.md` quando indicado.
   - **Fase 3 — Refatoração:** só após confirmação; ler `references/mvc-guidelines.md` e `references/refactoring-playbook.md`; criar a estrutura de diretórios MVC; aplicar as transformações do playbook para eliminar os findings; extrair config (sem hardcoded), criar models, separar views/routes, concentrar fluxo em controllers, centralizar error handling, definir entry point/composition root; **preservar todos os endpoints originais**; ao final imprimir a nova estrutura e rodar a **validação** (boot da app + checagem dos endpoints), reportando ✓/✗.
   - **Regras gerais:** adaptar as transformações ao nível de organização do projeto (um monolito procedural exige mais que um projeto já parcialmente em camadas); nunca inventar arquivo/linha — sempre citar evidência real; se um projeto já usa ORM, refatorar sobre o ORM em vez de reintroduzir SQL cru.

- [ ] **Step 2: Verificar o frontmatter e a estrutura**

Run: `head -5 code-smells-project/.claude/skills/refactor-arch/SKILL.md && grep -n "Fase 1\|Fase 2\|Fase 3\|\[y/n\]\|references/" code-smells-project/.claude/skills/refactor-arch/SKILL.md`
Expected: frontmatter com `name: refactor-arch`; as 3 fases presentes; o gate `[y/n]` presente na Fase 2; referências aos 5 arquivos `references/*.md`.

- [ ] **Step 3: Commit**

```bash
git add code-smells-project/.claude/skills/refactor-arch/SKILL.md
git commit -m "feat(skill): adiciona SKILL.md orquestrador das 3 fases"
```

---

### Task 3: Reference — Análise de Projeto (`project-analysis.md`)

**Files:**
- Create: `code-smells-project/.claude/skills/refactor-arch/references/project-analysis.md`

**Interfaces:**
- Consumes: referenciado pela Fase 1 do `SKILL.md`.
- Produces: heurísticas que a Fase 1 usa para preencher o bloco-resumo (Language, Framework, Dependencies, DB, Domain, Architecture).

- [ ] **Step 1: Escrever as heurísticas de detecção**

Conteúdo obrigatório (Área de conhecimento 1 do README):
   - **Detecção de linguagem:** por extensão de arquivos-fonte e manifesto (`.py`+`requirements.txt`/`pyproject.toml` → Python; `.js`/`.ts`+`package.json` → Node; `.rb`+`Gemfile`; `.php`+`composer.json`; etc.). Tabela linguagem → sinais.
   - **Detecção de framework + versão:** ler o manifesto. Python: `flask`, `django`, `fastapi` no `requirements.txt` (extrair versão pinada); Node: `express`, `koa`, `nestjs`, `fastify` em `package.json` `dependencies`. Também confirmar por imports (`from flask import`, `require('express')`).
   - **Detecção de banco de dados:** procurar `sqlite3`, `psycopg2`, `mysql`, `mongoose`, `sqlalchemy`, DDL (`CREATE TABLE`), strings de conexão (`sqlite:///`, `:memory:`, `postgres://`). Listar as tabelas encontradas via `CREATE TABLE` ou models de ORM.
   - **Detecção de domínio:** inferir dos nomes de tabelas/rotas/entidades (ex.: `produtos/pedidos` → e-commerce; `courses/enrollments/payments` → LMS/checkout; `tasks/categories` → task manager).
   - **Mapeamento de arquitetura atual:** contar arquivos-fonte e LoC; classificar em "monolito procedural / God Class" vs "parcialmente em camadas" vs "MVC"; identificar entry point, porta, como a app inicia; detectar padrões (blueprints, factory, roteamento manual).
   - **Como imprimir o resumo:** template do bloco `PHASE 1: PROJECT ANALYSIS` idêntico ao exemplo do README (linhas alinhadas: `Language:`, `Framework:`, `Dependencies:`, `Domain:`, `Architecture:`, `Source files:`, `DB tables:`).
   - Incluir uma tabela worked-example com os 3 stacks-alvo (Flask cru, Express, Flask+SQLAlchemy) mostrando o resultado esperado da detecção — para provar agnosticismo.

- [ ] **Step 2: Verificar cobertura**

Run: `grep -in "flask\|express\|sqlite\|sqlalchemy\|PHASE 1\|framework\|dom[ií]nio" code-smells-project/.claude/skills/refactor-arch/references/project-analysis.md | head`
Expected: cobre detecção de Python/Flask e Node/Express, DB SQLite/SQLAlchemy, e o template do bloco de resumo.

- [ ] **Step 3: Commit**

```bash
git add code-smells-project/.claude/skills/refactor-arch/references/project-analysis.md
git commit -m "feat(skill): adiciona referencia de analise de projeto (Fase 1)"
```

---

### Task 4: Reference — Catálogo de Anti-patterns (`anti-patterns-catalog.md`)

**Files:**
- Create: `code-smells-project/.claude/skills/refactor-arch/references/anti-patterns-catalog.md`

**Interfaces:**
- Consumes: referenciado pela Fase 2 do `SKILL.md`.
- Produces: catálogo com IDs de anti-pattern citáveis nos findings; sinais de detecção que a Fase 2 aplica.

- [ ] **Step 1: Escrever o catálogo (≥ 12 anti-patterns, incluindo deprecated)**

Cada entrada com: **ID/Nome**, **Severidade**, **Sinais de detecção** (acionáveis, não vagos), **Por que é problema**, **Stacks aplicáveis**. Cobrir no mínimo (garante ≥8 e distribuição CRITICAL→LOW):

   1. **Hardcoded Credentials/Secrets** — CRITICAL — sinal: `SECRET_KEY=`, `password=`, `pk_live`, `smtp...=` literais no código; strings de senha em seed.
   2. **SQL Injection** — CRITICAL — sinal: query montada por concatenação/f-string com input do usuário (`"... WHERE x = " + v`, `f"...{v}..."`); ausência de placeholders `?`/`:param`.
   3. **God Class / God Module / God Method** — CRITICAL — sinal: um arquivo/classe/função que concentra DB + regra de negócio + roteamento + serialização; arquivo > ~250 linhas com múltiplos domínios; método > ~50 linhas.
   4. **Weak/Broken Password Hashing** — CRITICAL — sinal: `md5`/`sha1` sem salt, hash caseiro, senha em texto plano; senha devolvida em resposta/`to_dict`.
   5. **Arbitrary Code/SQL Execution & endpoints destrutivos sem auth** — CRITICAL — sinal: endpoint que executa SQL/`eval` do body; `reset-db`/`DELETE` sem verificação de auth.
   6. **Missing Authentication/Authorization** — HIGH — sinal: rotas sensíveis sem middleware/decorator de auth; token previsível/sem assinatura (`fake-jwt-token-`).
   7. **Business Logic in Controller/Route** — HIGH — sinal: cálculo/regra/efeito colateral (envio de email, cobrança) dentro do handler HTTP; handler > ~40 linhas.
   8. **Global Mutable State** — HIGH — sinal: variável de módulo mutável compartilhada entre requisições (`globalCache`, `totalRevenue`, conexão singleton global).
   9. **Missing Transaction / Non-atomic writes** — HIGH — sinal: múltiplos INSERT/UPDATE relacionados sem `BEGIN/commit/rollback`.
   10. **Insecure config em produção** — HIGH — sinal: `debug=True`, bind `0.0.0.0`, CORS aberto (`CORS(app)` sem origins), `express.json()` sem limite/helmet.
   11. **N+1 Query** — MEDIUM — sinal: query dentro de loop; `Model.query.get()` por item; ausência de JOIN/eager-load.
   12. **Deprecated API usage** — MEDIUM — **seção obrigatória** — tabela por stack:
       - Python: `datetime.utcnow()` → `datetime.now(timezone.utc)`; SQLAlchemy `Model.query.get()`/`Query.get()` → `db.session.get(Model, id)`; `Model.query` legacy → `db.session.execute(select(...))`.
       - Node: `body-parser` → `express.json()`; `crypto.createCipher` → `createCipheriv`; `new Buffer()` → `Buffer.from()`; callbacks → `async/await`/promises; Express 4 → 5 quando aplicável.
       - Regra: identificar o uso obsoleto E recomendar o equivalente moderno.
   13. **Missing Input Validation** — MEDIUM — sinal: uso de campos do body sem checagem de presença/tipo; `int(x)`/comparação numérica sobre input não validado → 500.
   14. **Code Duplication** — MEDIUM — sinal: blocos de validação/serialização repetidos; helper existente ignorado.
   15. **Poor Naming / Magic Numbers / Dead Code** — LOW — sinal: `u,e,p,cc`; literais soltos (`10000`, `5000`); imports não usados; `except:` nu; `print()` como logging; deps declaradas e não importadas.

- [ ] **Step 2: Verificar contagem e distribuição**

Run: `grep -c "Severidade:\|Severity:\|CRITICAL\|HIGH\|MEDIUM\|LOW" code-smells-project/.claude/skills/refactor-arch/references/anti-patterns-catalog.md && grep -in "deprecated\|utcnow\|body-parser\|createCipher" code-smells-project/.claude/skills/refactor-arch/references/anti-patterns-catalog.md | head`
Expected: ≥ 8 anti-patterns com as 4 severidades presentes; a seção de APIs deprecated existe e cita exemplos por stack.

- [ ] **Step 3: Commit**

```bash
git add code-smells-project/.claude/skills/refactor-arch/references/anti-patterns-catalog.md
git commit -m "feat(skill): adiciona catalogo de anti-patterns com deteccao de APIs deprecated"
```

---

### Task 5: Reference — Template de Relatório (`audit-report-template.md`)

**Files:**
- Create: `code-smells-project/.claude/skills/refactor-arch/references/audit-report-template.md`

**Interfaces:**
- Consumes: referenciado pela Fase 2 do `SKILL.md`.
- Produces: o formato exato do relatório que a Fase 2 renderiza e que é salvo em `reports/audit-project-N.md`.

- [ ] **Step 1: Escrever o template**

Baseado no exemplo "ARCHITECTURE AUDIT REPORT" do README. Deve conter:
   - **Cabeçalho:** `ARCHITECTURE AUDIT REPORT`, `Project:`, `Stack:`, `Files:` (N analisados | ~X linhas).
   - **`## Summary`:** contagem por severidade (`CRITICAL: n | HIGH: n | MEDIUM: n | LOW: n`).
   - **`## Findings`:** um bloco por finding, **ordenados por severidade (CRITICAL → LOW)**, cada um com:
     ```
     ### [SEVERITY] <Nome do anti-pattern>
     File: <arquivo>:<linha(s)>
     Description: <o que é, com evidência concreta>
     Impact: <por que importa>
     Recommendation: <transformação sugerida — apontar para o playbook>
     ```
   - **Rodapé:** `Total: <n> findings`.
   - Instrução explícita: cada finding **deve** ter arquivo e linha exatos; nunca omitir a linha.
   - Um exemplo preenchido (1-2 findings de amostra) para o agente calibrar o tom.

- [ ] **Step 2: Verificar o template**

Run: `grep -n "AUDIT REPORT\|## Summary\|## Findings\|File:\|Recommendation:\|Total:" code-smells-project/.claude/skills/refactor-arch/references/audit-report-template.md`
Expected: todas as seções presentes na ordem correta.

- [ ] **Step 3: Commit**

```bash
git add code-smells-project/.claude/skills/refactor-arch/references/audit-report-template.md
git commit -m "feat(skill): adiciona template do relatorio de auditoria (Fase 2)"
```

---

### Task 6: Reference — Guidelines de Arquitetura MVC (`mvc-guidelines.md`)

**Files:**
- Create: `code-smells-project/.claude/skills/refactor-arch/references/mvc-guidelines.md`

**Interfaces:**
- Consumes: referenciado pela Fase 3 do `SKILL.md`.
- Produces: a definição da estrutura-alvo que a Fase 3 cria; nomes de camadas/pastas usados pelo playbook (Task 7).

- [ ] **Step 1: Escrever as guidelines**

Conteúdo obrigatório (Área de conhecimento 4). Definir as camadas e a estrutura-alvo (alinhada ao exemplo "New Project Structure" do README):
   - **Config** (`config/settings.py` ou `config/index.js`): carrega env vars, zero hardcoded.
   - **Models** (`models/`): abstração de dados por domínio; acesso ao DB/ORM; sem regra de apresentação nem roteamento.
   - **Views/Routes** (`views/routes.py` ou `routes/`): definição de rotas HTTP; parsing de request/response; delega ao controller; sem SQL nem regra de negócio.
   - **Controllers** (`controllers/`): orquestra o fluxo (validação → model → resposta); concentra a lógica de aplicação; um controller por domínio.
   - **Middlewares** (`middlewares/error_handler.py`): error handling centralizado, auth, etc.
   - **Entry point / Composition root** (`app.py`/`app.js`): monta a aplicação, injeta dependências, registra rotas/middlewares; nada de lógica.
   - **Regras de dependência:** Routes → Controllers → Models; nunca o inverso; sem estado global mutável; config injetada, não importada de módulo global.
   - **Regra de adaptação:** se o projeto já tem camadas (ex.: task-manager-api com `models/`, `routes/`, `services/`), reorganizar mover a lógica das rotas para controllers/services e usar os métodos de domínio existentes em vez de recriar a estrutura do zero. Para Node/Express, mapear os nomes equivalentes (`controllers/`, `routes/`, `models/`, `config/`, `middlewares/`).
   - Diagrama textual da estrutura-alvo por stack (Python e Node).

- [ ] **Step 2: Verificar cobertura das camadas**

Run: `grep -in "config\|model\|view\|route\|controller\|middleware\|entry point\|composition root\|depend" code-smells-project/.claude/skills/refactor-arch/references/mvc-guidelines.md | head`
Expected: todas as camadas (Config, Models, Views/Routes, Controllers, Middlewares, Entry point) e as regras de dependência presentes.

- [ ] **Step 3: Commit**

```bash
git add code-smells-project/.claude/skills/refactor-arch/references/mvc-guidelines.md
git commit -m "feat(skill): adiciona guidelines da arquitetura MVC alvo (Fase 3)"
```

---

### Task 7: Reference — Playbook de Refatoração (`refactoring-playbook.md`)

**Files:**
- Create: `code-smells-project/.claude/skills/refactor-arch/references/refactoring-playbook.md`

**Interfaces:**
- Consumes: referenciado pela Fase 3 do `SKILL.md`; usa os nomes de camadas de `mvc-guidelines.md` e mapeia contra os IDs de `anti-patterns-catalog.md`.
- Produces: transformações concretas antes/depois que a Fase 3 aplica.

- [ ] **Step 1: Escrever o playbook (≥ 8 padrões antes/depois)**

Cada padrão com: **anti-pattern alvo**, **objetivo**, **código ANTES**, **código DEPOIS**, **notas**. Cobrir no mínimo:

   1. **Extrair config para módulo (remover hardcoded)** — antes: `SECRET_KEY = "..."`; depois: `SECRET_KEY = os.environ["SECRET_KEY"]` em `config/settings.py` + `.env.example`.
   2. **Parametrizar queries (eliminar SQL injection)** — antes: `"... WHERE id = " + str(id)`; depois: `cursor.execute("... WHERE id = ?", (id,))`. Versão Node: placeholders `?` no `sqlite3`.
   3. **Quebrar God Class/Module em camadas** — antes: `models.py` com tudo; depois: `models/produto_model.py` + `controllers/produto_controller.py` + `views/routes.py`.
   4. **Hash de senha seguro** — antes: `md5(pwd)` / `badCrypto` / texto plano; depois: `bcrypt`/`werkzeug.security.generate_password_hash` / `bcrypt` (Node). Nunca devolver senha/hash no `to_dict`/response.
   5. **Mover lógica de negócio do controller para service/model** — antes: cálculo de desconto/regra de pagamento no handler; depois: função no model/service dedicado, controller só orquestra.
   6. **Substituir estado global mutável por injeção/escopo** — antes: `db_connection` global / `globalCache`; depois: conexão por request/DI, cache com TTL ou removido.
   7. **Envolver escritas relacionadas em transação** — antes: INSERTs soltos; depois: `try: ... conn.commit() except: conn.rollback()` / transação do driver.
   8. **Centralizar error handling** — antes: `try/except` repetido em cada handler retornando `str(e)`; depois: `@app.errorhandler`/middleware `(err, req, res, next)` único.
   9. **Corrigir N+1 com JOIN/eager-load** — antes: query em loop; depois: 1 JOIN / `joinedload`/`selectinload`.
   10. **Substituir APIs deprecated** — antes: `datetime.utcnow()` / `Model.query.get()` / `body-parser`; depois: `datetime.now(timezone.utc)` / `db.session.get(Model, id)` / `express.json()`.
   11. **Adicionar validação de entrada** — antes: uso direto do body; depois: função de validação/schema retornando 400 com mensagem clara.
   12. **Proteger endpoints e remover rotas perigosas** — antes: `/admin/query`, `/admin/reset-db`, `DELETE` sem auth; depois: remover/segregar atrás de auth middleware; token real (JWT assinado) quando aplicável.

   Incluir uma **tabela de rastreabilidade** anti-pattern → padrão de refatoração.

- [ ] **Step 2: Verificar contagem de padrões e exemplos antes/depois**

Run: `grep -c "ANTES\|Before\|DEPOIS\|After\|^###" code-smells-project/.claude/skills/refactor-arch/references/refactoring-playbook.md`
Expected: ≥ 8 padrões, cada um com blocos de código antes e depois.

- [ ] **Step 3: Commit**

```bash
git add code-smells-project/.claude/skills/refactor-arch/references/refactoring-playbook.md
git commit -m "feat(skill): adiciona playbook de refatoracao com 12 padroes antes/depois"
```

---

### Task 8: Executar a skill no Projeto 1 (code-smells-project)

**Files:**
- Create: `reports/audit-project-1.md`
- Modify/Create: estrutura MVC em `code-smells-project/` (resultado da Fase 3)

**Interfaces:**
- Consumes: a skill completa (Tasks 2-7).
- Produces: relatório de auditoria + código refatorado que serve de baseline de qualidade para os projetos 2 e 3.

- [ ] **Step 1: Baseline — capturar comportamento atual dos endpoints**

Rodar a app original e registrar as respostas dos endpoints-chave (contrato a preservar).
Run: `cd code-smells-project && pip install -r requirements.txt && python app.py &` depois `curl -s localhost:5000/health`, `curl -s localhost:5000/produtos`, `curl -s -X POST localhost:5000/login -H 'Content-Type: application/json' -d '{"email":"admin@loja.com","senha":"admin123"}'`.
Expected: capturar status/shape de cada endpoint para comparar após a refatoração. Encerrar o processo.

- [ ] **Step 2: Executar Fase 1 + Fase 2 (auditoria) e salvar o relatório**

Invocar a skill (via subagente especialista com o SKILL.md como guia) para produzir a análise (Fase 1) e o relatório (Fase 2). Salvar a saída da Fase 2 em `reports/audit-project-1.md`.
Expected (critérios de aceite): Fase 1 detecta Python/Flask 3.1.1, SQLite, domínio e-commerce, 4 arquivos; Fase 2 gera ≥ 5 findings (deve incluir SQL injection, hardcoded secret, God Module, senha em texto plano — ver "achados-chave Projeto 1"), com ≥ 1 CRITICAL/HIGH, ordenados por severidade, cada um com arquivo:linha; relatório segue o template.

- [ ] **Step 3: Gate de confirmação + Fase 3 (refatoração)**

Confirmar (`y`) e executar a Fase 3: criar estrutura MVC (`src/config/`, `src/models/`, `src/views/`, `src/controllers/`, `src/middlewares/`, `src/app.py`), aplicar o playbook para eliminar os findings (parametrizar queries, extrair config, hash de senha, remover rotas `/admin/*` perigosas, centralizar error handling, corrigir N+1, remover imports mortos). Preservar os endpoints originais.

- [ ] **Step 4: Validar (boot + endpoints)**

Run: subir a app refatorada e repetir os `curl` do Step 1.
Expected: aplicação inicia sem erros; endpoints originais respondem com o mesmo contrato (produtos lista, login funciona, health OK); zero anti-patterns CRITICAL remanescentes. Registrar o log/saída para o README (Task 11).

- [ ] **Step 5: Commit**

```bash
git add reports/audit-project-1.md code-smells-project/
git commit -m "refactor(project-1): refatora code-smells-project para MVC + relatorio de auditoria"
```

---

### Task 9: Copiar a skill e executar no Projeto 2 (ecommerce-api-legacy)

**Files:**
- Create: `ecommerce-api-legacy/.claude/skills/refactor-arch/` (cópia da skill)
- Create: `reports/audit-project-2.md`
- Modify/Create: estrutura MVC em `ecommerce-api-legacy/`

**Interfaces:**
- Consumes: a skill validada no Projeto 1 (prova de agnosticismo em outro stack).
- Produces: relatório + código refatorado Node/Express.

- [ ] **Step 1: Copiar a skill (sem alterações — prova de reutilização)**

Run: `cp -r code-smells-project/.claude ecommerce-api-legacy/.claude`
Expected: `ecommerce-api-legacy/.claude/skills/refactor-arch/SKILL.md` existe e é idêntico ao original (`diff` vazio).

- [ ] **Step 2: Baseline — capturar comportamento atual**

Run: `cd ecommerce-api-legacy && npm install && node src/app.js &` depois exercitar `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id` conforme `api.http`.
Expected: registrar status/shape das 3 rotas. Encerrar o processo.

- [ ] **Step 3: Executar Fase 1 + Fase 2 e salvar relatório**

Expected: Fase 1 detecta Node/Express 4.18.2, SQLite `:memory:`, domínio LMS/checkout, 3 arquivos; Fase 2 gera ≥ 5 findings (incluir hardcoded `pk_live`/SMTP, cartão logado, `badCrypto`, God Class, sem transação — ver "achados-chave Projeto 2"), ≥ 1 CRITICAL/HIGH, ordenados, com arquivo:linha. Salvar em `reports/audit-project-2.md`.

- [ ] **Step 4: Confirmar + Fase 3 (refatoração)**

Criar estrutura MVC em Node (`src/config/`, `src/models/`, `src/controllers/`, `src/routes/`, `src/middlewares/`, `src/app.js`): quebrar `AppManager` em camadas; mover credenciais para `.env`/`config`; parar de logar cartão; hash real (`bcrypt`); envolver checkout em transação; substituir callback hell por `async/await`; centralizar error handling + 404; validar entrada. Preservar as 3 rotas originais.

- [ ] **Step 5: Validar (boot + endpoints)**

Expected: `node src/app.js` sobe sem erro; `POST /api/checkout`, `GET /api/admin/financial-report`, `DELETE /api/users/:id` respondem preservando o contrato; nenhuma credencial hardcoded remanescente.

- [ ] **Step 6: Commit**

```bash
git add ecommerce-api-legacy/ reports/audit-project-2.md
git commit -m "refactor(project-2): refatora ecommerce-api-legacy (Node/Express) para MVC + relatorio"
```

---

### Task 10: Copiar a skill e executar no Projeto 3 (task-manager-api)

**Files:**
- Create: `task-manager-api/.claude/skills/refactor-arch/` (cópia da skill)
- Create: `reports/audit-project-3.md`
- Modify/Create: estrutura MVC melhorada em `task-manager-api/`

**Interfaces:**
- Consumes: a skill validada nos Projetos 1 e 2 (prova de adaptação a projeto já parcialmente organizado).
- Produces: relatório + código refatorado; encerra a suíte de execução.

- [ ] **Step 1: Copiar a skill**

Run: `cp -r code-smells-project/.claude task-manager-api/.claude`
Expected: `task-manager-api/.claude/skills/refactor-arch/SKILL.md` idêntico ao original.

- [ ] **Step 2: Baseline — capturar comportamento atual**

Run: `cd task-manager-api && pip install -r requirements.txt && python seed.py && python app.py &` depois exercitar `GET /tasks`, `POST /login`, `GET /reports/summary`, `GET /categories`.
Expected: registrar status/shape dos endpoints (18+ rotas). Encerrar o processo.

- [ ] **Step 3: Executar Fase 1 + Fase 2 e salvar relatório**

Expected: Fase 1 detecta Python/Flask 3.0.0 + SQLAlchemy, SQLite `tasks.db`, domínio Task Manager, ~14 arquivos; Fase 2 identifica problemas **mesmo com camadas já presentes** — ≥ 5 findings incluindo MD5 sem salt, hash no login, SMTP hardcoded, token falso, **APIs deprecated (`datetime.utcnow`, `Query.get`)**, `services/` morto, N+1 — ≥ 1 CRITICAL/HIGH, ordenados, com arquivo:linha. Salvar em `reports/audit-project-3.md`.

- [ ] **Step 4: Confirmar + Fase 3 (refatoração adaptada)**

Adaptar (não recriar do zero): mover lógica das rotas para `controllers/`/`services/`; usar os métodos de domínio já existentes (`Task.is_overdue()`, `validate_status`) em vez de duplicar; trocar MD5 por hash seguro e parar de vazar o hash no `to_dict`; extrair config para `config/` com `python-dotenv` (já declarado); substituir `datetime.utcnow()` → `datetime.now(timezone.utc)` e `Model.query.get()` → `db.session.get()`; App Factory (`create_app()`); mover `db.create_all()` para fora do import; corrigir N+1 com eager-load; centralizar error handling; separar `category_routes.py`. Preservar todos os endpoints.

- [ ] **Step 5: Validar (boot + endpoints)**

Expected: `python app.py` sobe sem erro; todos os endpoints originais continuam respondendo; sem MD5/credenciais hardcoded; sem `datetime.utcnow()`/`Query.get()` remanescentes.

- [ ] **Step 6: Commit**

```bash
git add task-manager-api/ reports/audit-project-3.md
git commit -m "refactor(project-3): refatora task-manager-api para MVC (adaptado) + relatorio"
```

---

### Task 11: Finalizar README (seções B, C, D) e entrega

**Files:**
- Modify: `README.md` (adicionar seções "Construção da Skill", "Resultados", "Como Executar")

**Interfaces:**
- Consumes: os relatórios (Tasks 8-10), os logs de validação e as decisões de design (Tasks 2-7).
- Produces: o README de entrega completo.

- [ ] **Step 1: Escrever seção "Construção da Skill" (B)**

Documentar: decisões de design (por que SKILL.md orquestrador + 5 referências); quais anti-patterns entraram no catálogo e por quê; como garantiu agnosticismo (detecção por manifesto + heurísticas por stack + teste nos 3 projetos); desafios e soluções.

- [ ] **Step 2: Escrever seção "Resultados" (C)**

Incluir: resumo dos 3 relatórios (findings por severidade em cada); comparação antes/depois da estrutura de cada projeto (árvore de diretórios); o checklist de validação do README preenchido (Fase 1/2/3) para cada projeto; logs/saída mostrando as apps rodando após a refatoração; observações sobre o comportamento em stacks diferentes (Flask cru vs Express vs Flask+SQLAlchemy).

- [ ] **Step 3: Escrever seção "Como Executar" (D)**

Pré-requisitos (Claude Code instalado); comandos por projeto (`cd <proj> && claude "/refactor-arch"`); como validar (boot + curl nos endpoints).

- [ ] **Step 4: Self-review do README contra o checklist do desafio**

Run: `grep -n "Análise Manual\|Construção da Skill\|Resultados\|Como Executar" README.md`
Expected: as 4 seções (A, B, C, D) presentes.

- [ ] **Step 5: Verificar entregáveis completos**

Run: `ls reports/ && ls code-smells-project/.claude/skills/refactor-arch/references/ && ls */. claude/skills/refactor-arch/SKILL.md 2>/dev/null; find . -name SKILL.md -not -path '*/node_modules/*'`
Expected: 3 relatórios; 5 arquivos de referência + SKILL.md; skill presente nos 3 projetos.

- [ ] **Step 6: Commit final**

```bash
git add README.md
git commit -m "docs: finaliza README com Construcao da Skill, Resultados e Como Executar"
```

---

## Self-Review (checklist do plano contra o desafio)

**Cobertura do spec:**
- ✅ Análise Manual dos 3 projetos (≥5 problemas, distribuição de severidade) → Task 1.
- ✅ Skill em `.claude/skills/refactor-arch/` com SKILL.md + 5 referências cobrindo as 5 áreas de conhecimento → Tasks 2-7.
- ✅ SKILL.md com 3 fases sequenciais + gate de confirmação na Fase 2 + validação na Fase 3 → Task 2.
- ✅ Catálogo ≥8 anti-patterns com severidade distribuída + detecção de APIs deprecated → Task 4.
- ✅ Playbook ≥8 transformações antes/depois → Task 7.
- ✅ Execução nos 3 projetos + relatórios em `reports/` + commits → Tasks 8-10.
- ✅ Skill copiada (não reescrita) para projetos 2 e 3 → Tasks 9-10, Step 1.
- ✅ Critérios de aceite (stack detectada, ≥5 findings com ≥1 CRITICAL/HIGH, app funciona) validados nos 3 → Tasks 8-10, Steps de validação.
- ✅ README com seções A/B/C/D → Tasks 1 e 11.

**Consistência de nomes:** camadas MVC (`config/`, `models/`, `views`|`routes/`, `controllers/`, `middlewares/`, entry point) usadas de forma idêntica entre `mvc-guidelines.md` (Task 6), `refactoring-playbook.md` (Task 7) e as Fases 3 das Tasks 8-10.

**Riscos / notas:**
- A invocação real da skill (`claude "/refactor-arch"`) é interativa; na execução via subagentes, o SKILL.md é usado como guia de processo pelo agente especialista, preservando o gate de confirmação como checkpoint humano (revisão do relatório antes da Fase 3).
- Projeto 2 usa SQLite `:memory:`: o baseline e a validação precisam popular dados na mesma execução (seed inline) antes de exercitar os endpoints.
- Manter os endpoints originais é contrato inegociável — cada Task de execução tem Step de baseline + Step de validação comparando antes/depois.
