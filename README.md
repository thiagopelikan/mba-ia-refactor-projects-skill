# Criação de Skills — Refatoração Arquitetural Automatizada

Ao longo do curso você aprendeu o que são Skills e como elas permitem que um agente de IA atue como um especialista em tarefas específicas. Agora imagine o seguinte cenário: você herdou 3 projetos legados com problemas de arquitetura, segurança e qualidade de código. Revisar e corrigir tudo manualmente levaria dias.

Neste desafio, você vai criar uma Skill que automatiza esse processo — analisando, auditando e refatorando qualquer projeto para o padrão MVC, independente da tecnologia.

## Objetivo

Você deve entregar uma Skill capaz de:

- Analisar uma codebase detectando linguagem, framework e arquitetura atual
- Identificar anti-patterns e code smells, classificando por severidade com arquivo e linha exatos
- Gerar um relatório de auditoria estruturado com todos os achados
- Refatorar o projeto para o padrão MVC (Model-View-Controller), eliminando os problemas encontrados
- Validar o resultado garantindo que a aplicação continua funcionando após as mudanças

A skill deve ser agnóstica de tecnologia, funcionando com diferentes linguagens e frameworks.

## Contexto

### Definição de Severidades

Para padronizar a sua auditoria e os relatórios gerados pela IA, utilize a seguinte escala de classificação baseada em problemas de MVC e SOLID:

- **CRITICAL:** Falhas graves de arquitetura ou segurança que impedem o funcionamento correto, expõem dados sensíveis (ex: credenciais hardcoded, SQL Injection) ou violam completamente a separação de responsabilidades (ex: "God Class" contendo banco de dados, lógicas complexas e roteamento no mesmo arquivo).
- **HIGH:** Fortes violações do padrão MVC ou princípios SOLID que dificultam muito a manutenção e testes (ex: lógicas de negócio pesadas presas dentro de Controllers, forte acoplamento sem Injeção de Dependência, ou uso de estado global mutável em toda a aplicação).
- **MEDIUM:** Problemas de padronização, duplicação de código ou gargalos de performance moderada (ex: Queries N+1 no banco de dados, uso inadequado de middlewares, validações ausentes nas rotas).
- **LOW:** Melhorias de legibilidade, nomenclatura de variáveis ruins, ou "magic numbers" soltos pelo código.

### Exemplo de Uso no CLI

```bash
# Executar a skill no projeto com problemas
cd code-smells-project
claude "/refactor-arch"
```

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python
Framework:      Flask 3.1.1
Dependencies:  flask-cors
Domain:        E-commerce API (produtos, pedidos, usuários)
Architecture:  Monolítica — tudo em 4 arquivos, sem separação de camadas
Source files:  4 files analyzed
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 4 | HIGH: 5 | MEDIUM: 2 | LOW: 3

## Findings

### [CRITICAL] God Class / God Method
File: models.py:1-350
Description: Arquivo único contém toda lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes.
Impact: Impossível testar em isolamento, qualquer mudança afeta tudo.
Recommendation: Separar em models e controllers por domínio.

### [CRITICAL] Hardcoded Credentials
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123'
...

================================
Total: 14 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

```
[... refatoração executada ...]

================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
src/
├── config/settings.py
├── models/
│   ├── produto_model.py
│   └── usuario_model.py
├── views/
│   └── routes.py
├── controllers/
│   ├── produto_controller.py
│   └── pedido_controller.py
├── middlewares/error_handler.py
└── app.py (composition root)

## Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly
  ✓ Zero anti-patterns remaining
================================
```

## Tecnologias obrigatórias

- **Ferramenta:** uma das três opções abaixo (não são aceitas outras ferramentas):
  - Claude Code
  - Gemini CLI
  - OpenAI Codex
- **Recurso:** Custom Skills (ou o equivalente na ferramenta escolhida)
- **Formato dos arquivos de referência:** Markdown
- **Projetos-alvo:** Python/Flask (2 projetos) e Node.js/Express (1 projeto) (fornecidos no repositório base)

> **Nota sobre a ferramenta:** Os exemplos deste documento usam o Claude Code (`.claude/skills/`) como referência, pois é a ferramenta utilizada no curso. Se você optar por Gemini CLI ou Codex, adapte o nome da pasta e o comando de invocação conforme a convenção dela — o conceito de skill e a estrutura interna (SKILL.md + arquivos de referência) permanecem os mesmos.

## Requisitos

### 1. Análise Manual dos Projetos

Antes de criar a skill, você deve entender os problemas que ela vai resolver.

**Tarefas:**

- Analisar o projeto `code-smells-project/` (Python/Flask — API de E-commerce)
- Analisar o projeto `ecommerce-api-legacy/` (Node.js/Express — LMS API com fluxo de checkout)
- Analisar o projeto `task-manager-api/` (Python/Flask — API de Task Manager)

Para cada projeto, identificar e documentar no mínimo 5 problemas, incluindo pelo menos:

- 1 de severidade CRITICAL ou HIGH
- 2 de severidade MEDIUM
- 2 de severidade LOW

Documentar os achados na seção "Análise Manual" do seu `README.md`

> **Dica:** Não precisa encontrar todos os problemas — foque nos que têm maior impacto arquitetural. Use os projetos como insumo para entender quais padrões sua skill precisa detectar.

> **Por que 3 projetos?** Dois são Python/Flask (com níveis de organização diferentes) e um é Node.js/Express. Sua skill precisa funcionar nos 3 para provar que é verdadeiramente agnóstica de tecnologia — lidando tanto com código completamente desestruturado quanto com projetos que já possuem alguma separação de camadas.

### 2. Criação da Skill

Agora que você conhece os problemas, crie uma skill que os detecte, gere um relatório de auditoria e corrija automaticamente.

**Tarefas:**

Criar a skill dentro do projeto `code-smells-project/` e implementar o SKILL.md com 3 fases sequenciais:

- **Fase 1 — Análise:** Detectar stack, mapear arquitetura atual, imprimir resumo
- **Fase 2 — Auditoria:** Cruzar código contra catálogo de anti-patterns, gerar relatório, pedir confirmação
- **Fase 3 — Refatoração:** Reestruturar para o padrão MVC, validar que funciona

Criar arquivos de referência em Markdown que forneçam à skill o conhecimento necessário para executar as 3 fases. Os arquivos devem cobrir **obrigatoriamente** as seguintes áreas de conhecimento:

| Área de conhecimento | O que deve conter |
|---|---|
| Análise de projeto | Heurísticas para detecção de linguagem, framework, banco de dados e mapeamento de arquitetura |
| Catálogo de anti-patterns | Anti-patterns com sinais de detecção e classificação de severidade |
| Template de relatório | Formato padronizado do relatório de auditoria (Fase 2) |
| Guidelines de arquitetura | Regras do padrão MVC alvo (camadas Models, Views/Routes e Controllers, responsabilidades de cada uma) |
| Playbook de refatoração | Padrões concretos de transformação para cada anti-pattern (com exemplos de código) |

> **Nota:** Você tem liberdade para organizar os arquivos de referência como preferir — pode usar os nomes e a quantidade de arquivos que fizer sentido para sua skill. O importante é que todas as 5 áreas de conhecimento estejam cobertas. O nome da skill (`refactor-arch`) e o arquivo `SKILL.md` são obrigatórios e não devem ser alterados. O path da skill segue a convenção da ferramenta escolhida (no Claude Code, por exemplo, é `.claude/skills/refactor-arch/`).

**Requisitos da skill:**

- Deve ser agnóstica de tecnologia — deve funcionar corretamente nos 3 projetos fornecidos, independente da stack ou nível de organização
- O catálogo de anti-patterns deve conter no mínimo 8 anti-patterns com severidade distribuída (CRITICAL, HIGH, MEDIUM, LOW)
- O catálogo deve incluir detecção de APIs deprecated — identificar uso de APIs obsoletas e recomendar o equivalente moderno
- O playbook deve ter no mínimo 8 padrões de transformação com exemplos de código antes/depois
- A Fase 2 deve pausar e pedir confirmação antes de modificar qualquer arquivo
- A Fase 3 deve validar o resultado (boot da aplicação + endpoints funcionando)

### 3. Execução da Skill

Execute sua skill nos 3 projetos e valide que ela funciona em todas as stacks.

#### Projeto 1 — code-smells-project (Python/Flask)

Invocar a skill no Claude Code:

```bash
claude "/refactor-arch"
```

> **Nota:** O comando acima é o exemplo com Claude Code. Se você estiver usando Gemini CLI ou Codex, utilize o comando equivalente para invocar uma skill na sua ferramenta.

- Verificar que a Fase 1 detecta corretamente a stack e imprime o resumo
- Verificar que a Fase 2 encontra no mínimo 5 dos problemas documentados na sua análise manual
- Confirmar a execução da Fase 3
- Verificar que a Fase 3:
  - Cria a estrutura de diretórios baseada em MVC
  - A aplicação inicia sem erros
  - Os endpoints originais continuam respondendo
- Salvar o relatório de auditoria (output da Fase 2) em `reports/audit-project-1.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 2 — ecommerce-api-legacy (Node.js/Express)

Prove que sua skill é reutilizável em outro projeto de backend, mas com stack diferente.

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `ecommerce-api-legacy/`
- Invocar a skill:

```bash
cd ../ecommerce-api-legacy
claude "/refactor-arch"
```

- Verificar que as 3 fases executam corretamente neste projeto
- Salvar o relatório em `reports/audit-project-2.md`
- Commitar o código refatorado do projeto no repositório

#### Projeto 3 — task-manager-api (Python/Flask)

Agora o teste com um projeto Python/Flask que já possui alguma organização de camadas (models, routes, services, utils).

- Copiar a pasta `.claude/skills/refactor-arch/` para dentro de `task-manager-api/`
- Invocar a skill:

```bash
cd ../task-manager-api
claude "/refactor-arch"
```

- Verificar que:
  - A Fase 1 detecta corretamente Python/Flask como stack e identifica o domínio de Task Manager
  - A Fase 2 identifica problemas mesmo em um projeto parcialmente organizado
  - A Fase 3 melhora a estrutura sem quebrar a aplicação (todos os endpoints devem continuar respondendo)
- Salvar o relatório em `reports/audit-project-3.md`
- Commitar o código refatorado do projeto no repositório

> **Nota:** Este projeto já possui alguma separação de camadas, mas isso não significa que a arquitetura está adequada. A skill deve identificar tanto problemas de código (segurança, performance, qualidade) quanto oportunidades de melhoria arquitetural. Se houver mudanças estruturais necessárias, a skill deve propô-las e executá-las.

#### Validação

Para cada projeto refatorado, valide o seguinte checklist:

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [ ] Linguagem detectada corretamente
- [ ] Framework detectado corretamente
- [ ] Domínio da aplicação descrito corretamente
- [ ] Número de arquivos analisados condiz com a realidade

### Fase 2 — Auditoria
- [ ] Relatório segue o template definido nos arquivos de referência
- [ ] Cada finding tem arquivo e linhas exatos
- [ ] Findings ordenados por severidade (CRITICAL → LOW)
- [ ] Mínimo de 5 findings identificados
- [ ] Detecção de APIs deprecated incluída (se aplicável)
- [ ] Skill pausa e pede confirmação antes da Fase 3

### Fase 3 — Refatoração
- [ ] Estrutura de diretórios segue padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models criados para abstrair dados
- [ ] Views/Routes separadas para visualização ou roteamento
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
```

> **Dica:** Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Entregável

Repositório público no GitHub (fork do repositório base) contendo:

- Skill completa em `.claude/skills/refactor-arch/` (dentro dos 3 projetos)
- Código refatorado dos 3 projetos (resultado da execução da Fase 3, commitado no repositório)
- Relatórios de auditoria em `reports/` (3 arquivos)
- `README.md` atualizado

### Estrutura do repositório

Faça um fork do repositório base contendo os três projetos com code smells.

> **Nota:** A estrutura abaixo usa Claude Code como exemplo (`.claude/skills/`). Se estiver usando outra ferramenta, adapte os caminhos conforme a convenção dela.

```
desafio-skills/
├── README.md                              # Sua documentação
│
├── code-smells-project/                   # Projeto 1 — Python/Flask (API de E-commerce)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← SUA SKILL AQUI
│   │           ├── SKILL.md
│   │           └── (arquivos de referência)
│   ├── app.py
│   ├── controllers.py
│   ├── models.py
│   ├── database.py
│   └── requirements.txt
│
├── ecommerce-api-legacy/                  # Projeto 2 — Node.js/Express (LMS API com checkout)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── src/
│   │   ├── app.js
│   │   ├── AppManager.js
│   │   └── utils.js
│   ├── api.http
│   └── package.json
│
├── task-manager-api/                      # Projeto 3 — Python/Flask (API de Task Manager)
│   ├── .claude/
│   │   └── skills/
│   │       └── refactor-arch/             # ← CÓPIA DA SKILL
│   │           └── ...
│   ├── app.py
│   ├── database.py
│   ├── seed.py
│   ├── requirements.txt
│   ├── models/
│   ├── routes/
│   ├── services/
│   └── utils/
│
└── reports/                               # Relatórios gerados
    ├── audit-project-1.md                 # Saída da Fase 2 no projeto 1
    ├── audit-project-2.md                 # Saída da Fase 2 no projeto 2
    └── audit-project-3.md                 # Saída da Fase 2 no projeto 3
```

**O que você vai criar:**

- `.claude/skills/refactor-arch/` — A skill completa (SKILL.md + arquivos de referência)
- Código refatorado dos 3 projetos — resultado da execução da Fase 3, commitado no repositório
- `reports/audit-project-{1,2,3}.md` — Relatório de auditoria de cada projeto
- `README.md` — Documentação do seu processo

**O que já vem pronto:**

- `code-smells-project/` — API de E-commerce Python/Flask com code smells intencionais
- `ecommerce-api-legacy/` — LMS API Node.js/Express (com fluxo de checkout) e problemas de implementação
- `task-manager-api/` — API de Task Manager Python/Flask com organização parcial e problemas de segurança/qualidade

> **Dica:** Cada projeto contém problemas intencionais de diferentes severidades (CRITICAL, HIGH, MEDIUM, LOW), incluindo falhas de segurança, violações arquiteturais e problemas de qualidade de código. Parte do desafio é identificá-los por conta própria através da análise manual do código.

### README.md deve conter

**A) Seção "Análise Manual":**

- Lista dos problemas identificados manualmente em cada projeto
- Classificação por severidade
- Justificativa de por que cada problema é relevante

**B) Seção "Construção da Skill":**

- Decisões de design: como estruturou o SKILL.md e os arquivos de referência
- Quais anti-patterns incluiu no catálogo e por quê
- Como garantiu que a skill é agnóstica de tecnologia
- Desafios encontrados e como resolveu

**C) Seção "Resultados":**

- Resumo dos relatórios de auditoria dos 3 projetos (quantos findings por severidade em cada)
- Comparação antes/depois da estrutura de cada projeto
- Checklist de validação preenchido para cada projeto
- Screenshots ou logs mostrando as aplicações rodando após refatoração
- Observações sobre como a skill se comportou em stacks diferentes

**D) Seção "Como Executar":**

- Pré-requisitos (a ferramenta escolhida — Claude Code, Gemini CLI ou Codex — instalada e configurada)
- Comandos para executar a skill em cada projeto
- Como validar que a refatoração funcionou

### Ordem de execução sugerida

**1. Analisar os projetos manualmente**

Leia o código dos três projetos e documente os problemas encontrados.

**2. Criar a skill**

Escreva o SKILL.md e os arquivos de referência.

**3. Executar nos 3 projetos**

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

Salve a saída da Fase 2 de cada projeto em `reports/audit-project-{1,2,3}.md`.

**4. Iterar**

Se a skill não detectou problemas suficientes ou a refatoração falhou, ajuste os arquivos de referência e execute novamente. É normal precisar de 2-4 iterações.

## Critérios de Aceite

A skill deve atingir os seguintes mínimos em **todos os 3 projetos**:

| Critério | Requisito |
|---|---|
| Fase 1 detecta stack corretamente | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 encontra >= 5 findings | OBRIGATÓRIO (3/3 projetos) |
| Fase 2 inclui pelo menos 1 CRITICAL ou HIGH | OBRIGATÓRIO (3/3 projetos) |
| Fase 3 aplicação funciona após refatoração | OBRIGATÓRIO (3/3 projetos) |

**IMPORTANTE:** Todos os critérios devem ser atingidos nos 3 projetos, não apenas em um!

> **Sobre o projeto 3 (task-manager-api):** Este projeto já possui alguma organização. "aplicação funciona" significa que a API inicia sem erros e todos os endpoints continuam respondendo corretamente.

## Referências

- [Claude Code: Skills](https://docs.anthropic.com/en/docs/claude-code/skills) — Documentação oficial sobre como criar e estruturar Skills
- [Claude Code: Overview](https://docs.anthropic.com/en/docs/claude-code/overview) — Visão geral do Claude Code e suas capacidades
- [The Complete Guide to Building Skills for Claude (PDF)](https://resources.anthropic.com/hubfs/The-Complete-Guide-to-Building-Skill-for-Claude.pdf) — Guia completo da Anthropic sobre construção de Skills
- [Equipping Agents for the Real World with Agent Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills) — Blog oficial da Anthropic sobre Agent Skills

---

## Análise Manual

Antes de construir a skill `refactor-arch`, os três projetos legados foram lidos manualmente, arquivo por arquivo, para levantar os anti-patterns de arquitetura, segurança e qualidade que a skill precisaria detectar e corrigir. A seguir estão os achados por projeto (arquivo:linha reais), classificados conforme a escala de severidade definida na seção [Definição de Severidades](#definição-de-severidades).

### Projeto 1 — code-smells-project (Python/Flask 3.1.1, SQLite, E-commerce)

| # | Anti-pattern | Local (arquivo:linha) | Severidade | Por que é relevante |
|---|---|---|---|---|
| 1 | Arbitrary SQL Execution | `app.py:59-78` | CRITICAL | `POST /admin/query` executa qualquer SQL vindo do body sem autenticação — equivale a um shell direto no banco (DROP de tabelas, SELECT de senhas, etc.). |
| 2 | SQL Injection por concatenação | `models.py:105-120` | CRITICAL | Queries montadas com `+` (ex.: `"... WHERE email='"+email+"'"` no login) permitem bypass de autenticação com payloads como `' OR '1'='1`. |
| 3 | Senha em texto plano + exposta | `database.py:31,75-83`, `models.py:83,99` | CRITICAL | Coluna `senha` armazenada sem hash e `GET /usuarios` devolve a senha de todos os usuários na resposta JSON. |
| 4 | Endpoint destrutivo sem autenticação | `app.py:47-57` | CRITICAL | `POST /admin/reset-db` apaga todas as tabelas do banco sem exigir nenhuma credencial. |
| 5 | God Module | `models.py:1-315` | CRITICAL | Um único arquivo concentra acesso a dados, regra de negócio e serialização de 4 domínios (produtos, usuários, pedidos, itens), tornando testes isolados inviáveis. |
| 6 | Estado global thread-unsafe | `database.py:4-10` | HIGH | Conexão singleton com `check_same_thread=False` é compartilhada entre requisições concorrentes, gerando corrupção de dados em produção. |
| 7 | `debug=True` + bind público + CORS aberto | `app.py:88`, `app.py:9` | HIGH | Debug mode exposto em `0.0.0.0` habilita o Werkzeug debugger (RCE conhecido) e `CORS(app)` sem restrição libera qualquer origem. |
| 8 | N+1 Query tripla | `models.py:171-233` (`192`, `224`) | MEDIUM | Busca de pedidos dispara uma query por pedido e outra por item/produto dentro de loops, degradando performance conforme o volume cresce. |
| 9 | Validação de tipo ausente | `controllers.py:39-46` | MEDIUM | `preco` recebido como string sem validação derruba o endpoint com erro 500 em vez de retornar 400. |
| 10 | Magic numbers/strings | `models.py:257-262`, `app.py:88` | LOW | Faixas de desconto (`10000`/`5000`/`1000`) e porta hardcoded sem constantes nomeadas dificultam manutenção. |
| 11 | `print()` como logging (com PII) | `controllers.py:179` | LOW | Dados de login são impressos no console em vez de usar um logger estruturado, vazando PII em qualquer ambiente. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express 4.18.2, SQLite in-memory, LMS com checkout)

| # | Anti-pattern | Local (arquivo:linha) | Severidade | Por que é relevante |
|---|---|---|---|---|
| 1 | Credenciais de produção hardcoded | `src/utils.js:1-7` | CRITICAL | Senha de banco, chave de gateway de pagamento (`pk_live_...`) e usuário SMTP ficam expostos em texto plano no código-fonte versionado. |
| 2 | Log de PAN de cartão + chave de gateway | `AppManager.js:45` | CRITICAL | `console.log` imprime o número completo do cartão junto com a chave secreta do gateway a cada checkout — violação direta de PCI-DSS. |
| 3 | Hash caseiro reversível | `src/utils.js:17-23` | CRITICAL | `badCrypto` usa Base64 repetido sem salt, dando falsa sensação de segurança para senhas que na prática são trivialmente reversíveis. |
| 4 | God Class `AppManager` | `AppManager.js:4-141` | CRITICAL | Uma única classe mistura conexão de banco, DDL, seed de dados, definição de rotas, regra de pagamento e serialização — nenhuma camada isolada. |
| 5 | Endpoints admin/destrutivos sem autenticação | `AppManager.js:80,131` | CRITICAL | `GET /api/admin/financial-report` e `DELETE /api/users/:id` não verificam identidade nem papel do requisitante. |
| 6 | Estado global mutável / memory leak | `src/utils.js:9-10`, `utils.js:10,25` | HIGH | `globalCache` e `totalRevenue` são compartilhados entre requisições e crescem sem limite; além disso `totalRevenue` é exportado por valor e nunca reflete atualizações (bug funcional). |
| 7 | Callback hell (5 níveis) | `AppManager.js:37-77` | HIGH | Checkout aninha 5 callbacks de banco, tornando o fluxo de erro incompleto e o código difícil de testar e manter. |
| 8 | Checkout sem transação | `AppManager.js:50-62` | HIGH | Falha após a matrícula mas antes do pagamento deixa o aluno inscrito sem cobrança — sem `BEGIN/COMMIT/ROLLBACK` para garantir atomicidade. |
| 9 | N+1 Query no relatório financeiro | `AppManager.js:83-126` | MEDIUM | Relatório itera resultados e dispara uma query adicional por linha em vez de usar JOIN, penalizando performance conforme os dados crescem. |
| 10 | Sem hardening HTTP básico | `src/app.js:6`, `AppManager.js:7` | MEDIUM | `express.json()` sem limite de tamanho, ausência de `helmet`/rate-limit, e banco `:memory:` hardcoded no construtor da classe. |
| 11 | Nomenclatura ruim | `AppManager.js:29-33` | LOW | Variáveis como `u, e, p, cid, cc` no handler de checkout escondem o significado dos dados e dificultam a leitura do fluxo de pagamento. |
| 12 | `console.log` como logging + magic number | `utils.js:19`, `AppManager.js:45` | LOW | `console.log` substitui um logger estruturado em toda a aplicação e `10000` aparece como magic number no cálculo de cache sem constante nomeada. |

### Projeto 3 — task-manager-api (Python/Flask 3.0.0 + SQLAlchemy, SQLite, Task Manager)

| # | Anti-pattern | Local (arquivo:linha) | Severidade | Por que é relevante |
|---|---|---|---|---|
| 1 | MD5 sem salt para senha | `models/user.py:29,32` | CRITICAL | `set_password`/`check_password` usam `hashlib.md5`, um algoritmo quebrado e sem salt — senhas viram alvo fácil de rainbow tables. |
| 2 | Hash de senha devolvido pela API | `models/user.py:21`, `routes/user_routes.py:209` | CRITICAL | `to_dict()` inclui o campo `password` e essa serialização é usada até na resposta de `POST /login`, vazando o hash da senha ao cliente. |
| 3 | Credenciais SMTP hardcoded | `services/notification_service.py:7-10` | CRITICAL | Usuário e senha de e-mail ficam fixos no código-fonte, expostos a qualquer pessoa com acesso ao repositório. |
| 4 | Token de autenticação falso e previsível | `routes/user_routes.py:210` | CRITICAL | O "token" é literalmente `'fake-jwt-token-' + id`, sem assinatura nem verificação — qualquer rota autenticada pode ser forjada trivialmente. |
| 5 | `debug=True` + bind público + CORS aberto | `app.py:34`, `app.py:15` | HIGH | Mesma exposição de RCE via debugger do Werkzeug e CORS sem restrição de origem em ambiente que já roda com SQLAlchemy em produção. |
| 6 | Lógica de negócio no controller (God Method) | `routes/report_routes.py:12-101` | HIGH | Endpoint de relatório concentra ~90 linhas de agregação e regra de negócio dentro da rota, sem nenhuma camada de serviço. |
| 7 | Código morto significativo | `services/notification_service.py:1-48`, `utils/helpers.py` | HIGH | `NotificationService` nunca é importado/usado e `utils/helpers.py` duplica validação que também nunca é chamada — sinal de camadas que existem só no nome. |
| 8 | `db.create_all()` no import do módulo | `app.py:30-31` | HIGH | Efeito colateral de criação de schema disparado só por importar `app.py`, dificultando testes e controle de migrations. |
| 9 | API deprecated `datetime.utcnow()` | `models/task.py:15`, `routes/report_routes.py:35` (22 ocorrências) | MEDIUM | `utcnow()` está deprecado desde Python 3.12 e retorna datetime naive; o substituto é `datetime.now(timezone.utc)`. |
| 10 | API deprecated `Model.query.get()` | `routes/task_routes.py:42,67` (16 ocorrências) | MEDIUM | Padrão legado do SQLAlchemy 1.x; a API atual recomenda `db.session.get(Model, id)`. |
| 11 | N+1 Query em `GET /tasks` | `routes/task_routes.py:41-57` | MEDIUM | Para cada task busca `User.query.get()` e `Category.query.get()` individualmente em vez de usar `join`/`joinedload`. |
| 12 | `except:` nu engolindo erros | `routes/task_routes.py:62-63` (8 ocorrências no projeto) | MEDIUM | Captura genérica sem logar nem re-lançar mascara falhas reais (ex.: erro de banco vira resposta silenciosa incorreta). |
| 13 | Dependências declaradas e não usadas | `requirements.txt:4-6` | LOW | `marshmallow`, `requests` e `python-dotenv` estão no requirements mas nunca são importados, inflando a superfície de dependências. |
| 14 | Validação fraca e duplicada | `routes/user_routes.py:61-65` | LOW | Senha aceita com menos de 4 caracteres e regex de e-mail simplista repetida em múltiplos pontos em vez de centralizada. |

---

## Construção da Skill

A skill `refactor-arch` foi construída em `.claude/skills/refactor-arch/` (Claude Code) como um **prompt orquestrador** (`SKILL.md`) mais **5 arquivos de referência em Markdown**, e depois copiada **sem nenhuma alteração** para dentro dos outros 2 projetos — provando que o mesmo artefato funciona em stacks diferentes.

### Decisões de design

- **`SKILL.md` enxuto + conhecimento em `references/`.** O `SKILL.md` só descreve o fluxo das 3 fases (o que fazer, em que ordem, quando parar). Todo o conhecimento de domínio — heurísticas, catálogo, template, arquitetura-alvo, transformações — vive em arquivos de referência separados, carregados sob demanda em cada fase. Isso mantém o orquestrador curto e legível, e torna o conhecimento reutilizável e versionável independente do prompt.
- **Separação por fase, não por assunto.** Cada uma das 3 fases do `SKILL.md` aponta explicitamente quais referências ler antes de agir (Fase 1 → `project-analysis.md`; Fase 2 → `anti-patterns-catalog.md` + `audit-report-template.md`; Fase 3 → `mvc-guidelines.md` + `refactoring-playbook.md`), evitando que o agente carregue contexto irrelevante para a etapa atual.
- **Gate de confirmação explícito.** A Fase 2 termina sempre com a pergunta literal `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` e a instrução "não modifique nenhum arquivo do projeto antes de receber `y`" — a Fase 3 só é lida/executada depois da resposta afirmativa.
- **Rastreabilidade finding → correção.** Cada finding da Fase 2 referencia o ID do anti-pattern do catálogo (AP-NN) e a recomendação aponta o padrão do playbook que o resolve (RP-NN), fechando o ciclo auditoria → refatoração.

### Anti-patterns no catálogo (`references/anti-patterns-catalog.md`)

16 anti-patterns (AP-01 a AP-16), com distribuição de severidade **5 CRITICAL / 5 HIGH / 4 MEDIUM / 2 LOW** — acima do mínimo de 8 exigido pelo desafio:

| ID | Anti-pattern | Severidade |
|---|---|---|
| AP-01 | Hardcoded Credentials / Secrets | CRITICAL |
| AP-02 | SQL Injection | CRITICAL |
| AP-03 | God Class / God Module / God Method | CRITICAL |
| AP-04 | Weak/Broken Password Hashing & Exposição de Senha | CRITICAL |
| AP-05 | Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth | CRITICAL |
| AP-06 | Missing Authentication / Authorization | HIGH |
| AP-07 | Business Logic in Controller/Route | HIGH |
| AP-08 | Global Mutable State | HIGH |
| AP-09 | Missing Transaction / Non-atomic Writes | HIGH |
| AP-10 | Insecure Config em Produção | HIGH |
| AP-11 | N+1 Query | MEDIUM |
| AP-12 | Deprecated API Usage *(seção obrigatória)* | MEDIUM |
| AP-13 | Missing Input Validation | MEDIUM |
| AP-14 | Code Duplication & Dead Layers (camadas de fachada) | MEDIUM |
| AP-15 | Poor Naming / Magic Numbers | LOW |
| AP-16 | Dead Code / Bad Hygiene | LOW |

Os anti-patterns foram escolhidos por **impacto arquitetural** e por serem detectáveis a partir de **sinais acionáveis** — nunca "código ruim" genérico, sempre algo como "query concatenada com input do usuário" ou "arquivo com mais de uma responsabilidade de domínio". O catálogo cobre 4 famílias: segurança (credenciais, SQL Injection, hash fraco), violações de MVC/SOLID (God Class, lógica no controller, estado global, ausência de transação), performance (N+1) e qualidade (validação ausente, duplicação, nomenclatura, APIs deprecated).

AP-12 (Deprecated API Usage) tem uma seção própria obrigatória com tabelas separadas por stack:

- **Python:** `datetime.utcnow()` → `datetime.now(timezone.utc)`, `datetime.utcfromtimestamp()` → `datetime.fromtimestamp(tz=...)`, `Model.query.get(id)` → `db.session.get(Model, id)`, `Model.query.filter(...)` (estilo legacy) → `select(...)` (SQLAlchemy 2.0), `@app.before_first_request` → inicialização no factory.
- **Node:** `body-parser` → `express.json()`/`express.urlencoded()`, `crypto.createCipher` → `crypto.createCipheriv`, `new Buffer(...)` → `Buffer.from(...)`, callbacks aninhados → `async/await`, `url.parse(...)` → `new URL(...)`.

Para a Fase 3, o `references/refactoring-playbook.md` traz **15 padrões de transformação** (RP-01 a RP-15, acima do mínimo de 8), cada um com código ANTES/DEPOIS, cobrindo desde extração de config e parametrização de queries até conversão de callbacks para `async/await` e absorção de camadas de fachada mortas — com uma tabela de rastreabilidade explícita ligando cada AP-NN ao(s) RP-NN que o resolve(m).

### Como garantimos o agnosticismo de tecnologia

- **Detecção por manifesto + heurísticas por stack.** `references/project-analysis.md` detecta linguagem/framework/versão a partir de `requirements.txt`/`package.json` (e imports/rotas quando o manifesto não basta), com "worked examples" cobrindo explicitamente os 3 stacks-alvo do desafio.
- **Playbook com exemplos em Python E Node lado a lado** para os padrões que se aplicam a ambos, mais um padrão específico (RP-13) só para conversão de callbacks no Node.
- **Regra de ADAPTAÇÃO** em `references/mvc-guidelines.md`: quando o projeto já possui alguma separação em camadas (caso do Projeto 3), a skill deve reorganizar/absorver o que já existe em vez de reescrever do zero.
- **Prova empírica:** a mesma skill, copiada byte a byte (`diff -rq` entre as 3 cópias não acusa nenhuma diferença), rodou com sucesso em um monolito procedural Flask, uma God Class Express e um Flask+SQLAlchemy com camadas de fachada.

### Desafios encontrados e como foram resolvidos

| # | Desafio | Solução |
|---|---|---|
| 1 | A porta padrão 5000 no macOS é ocupada pelo AirPlay Receiver, quebrando a validação de boot da Fase 3. | A skill e a validação passaram a ler a porta de uma variável de ambiente (`PORT`), com fallback para 5000 — documentado nos `.env.example` de cada projeto. |
| 2 | Tensão entre exigir autenticação (correto do ponto de vista de segurança) e o critério de aceite "endpoints continuam respondendo" — exigir auth faria os endpoints do baseline (sem token) retornarem 401. | A infraestrutura de autenticação (token assinado, `middlewares/auth.py`/`auth.js`) foi construída, mas deixada **não-obrigatória** por padrão nos endpoints herdados do baseline. Documentada como limitação aceita, priorizando não quebrar o contrato HTTP existente. |
| 3 | O banco `:memory:` do projeto 2 (Node) perde todo o estado a cada boot, e o baseline depende de dados de seed já existirem. | `db/init.js` roda o seed de forma transacional no boot da aplicação, antes de aceitar requisições. |
| 4 | O projeto 3 já tinha uma pasta `services/` e `utils/helpers.py`, mas eram **camadas de fachada mortas** (nunca importadas, ou duplicando lógica que já existia nos models) — uma reescrita ingênua manteria o lixo ou apagaria trabalho útil. | A Fase 3 aplicou a regra de adaptação: absorveu os métodos de domínio já existentes nos models (ex.: `Task.is_overdue()`, `to_dict()`), removeu `services/` (código morto) e tornou `utils/helpers.py` a implementação canônica única. |

## Resultados

### Resumo da auditoria (Fase 2) nos 3 projetos

| Projeto | Stack | Findings | Distribuição |
|---|---|---|---|
| 1 — code-smells-project | Python/Flask 3.1.1 (SQLite, SQL cru) | 30 | 11 CRITICAL / 8 HIGH / 7 MEDIUM / 4 LOW |
| 2 — ecommerce-api-legacy | Node/Express 4.18.2 (SQLite `:memory:`) | 21 | 6 CRITICAL / 7 HIGH / 5 MEDIUM / 3 LOW |
| 3 — task-manager-api | Python/Flask 3.0.0 + SQLAlchemy | 26 | 6 CRITICAL / 5 HIGH / 9 MEDIUM / 6 LOW |

Todos os 3 projetos superam com folga o mínimo de 5 findings e incluem múltiplos CRITICAL/HIGH exigidos pelos Critérios de Aceite. Relatórios completos em [`reports/audit-project-1.md`](reports/audit-project-1.md), [`reports/audit-project-2.md`](reports/audit-project-2.md) e [`reports/audit-project-3.md`](reports/audit-project-3.md).

### Antes / depois da estrutura

#### Projeto 1 — code-smells-project

```
# ANTES                          # DEPOIS
code-smells-project/             code-smells-project/
├── app.py                       ├── app.py                 # composition root
├── controllers.py                ├── requirements.txt
├── models.py    (God Module,    └── src/
│                 ~314 linhas)       ├── config/settings.py
├── database.py  (conexão            ├── models/
│                 singleton          │   ├── produto_model.py
│                 global)            │   ├── usuario_model.py
└── requirements.txt                 │   └── pedido_model.py
                                      ├── controllers/
                                      │   ├── produto_controller.py
                                      │   ├── usuario_controller.py
                                      │   └── pedido_controller.py
                                      ├── views/routes.py
                                      ├── middlewares/error_handler.py
                                      ├── services/
                                      └── database.py
```

Principais correções: queries parametrizadas (fim do SQL Injection), hash de senha com `werkzeug.security`, configuração via `.env`/`config/settings.py` (fim dos hardcoded), rotas `/admin/query` e `/admin/reset-db` removidas, error handling centralizado em middleware, conexão de banco por request em vez de singleton global.

#### Projeto 2 — ecommerce-api-legacy

```
# ANTES                          # DEPOIS
ecommerce-api-legacy/            ecommerce-api-legacy/
└── src/                         └── src/
    ├── app.js                       ├── app.js
    ├── AppManager.js (God               ├── config/
    │   Class, ~141 linhas)             ├── db/
    └── utils.js (credenciais            ├── models/            (5 models)
        + estado global)                 ├── services/          (gateway, bcrypt/password,
                                          │                       notificação, token, checkout, logger)
                                          ├── controllers/       (3)
                                          ├── routes/            (3)
                                          ├── middlewares/       (5)
                                          └── errors.js
```

Principais correções: credenciais movidas para `.env`, hash de senha com bcrypt, checkout transacional (`BEGIN`/`COMMIT`/`ROLLBACK`), cascade correto no delete de usuário, callback hell (5 níveis) convertido para `async/await`, validação de payload (antes derrubava o processo Node com `TypeError` não tratado, agora responde 400), relatório financeiro de N+1 para JOIN, e nenhum PAN de cartão ou chave de gateway em log.

#### Projeto 3 — task-manager-api

```
# ANTES                          # DEPOIS
task-manager-api/                task-manager-api/
├── app.py (db.create_all()      ├── app.py            # App Factory (create_app)
│   disparado no import)         ├── config/settings.py
├── models/                      ├── controllers/
├── routes/ (lógica inline)      ├── routes/            # finas + category_routes.py (novo)
├── services/ (MORTO,            ├── middlewares/
│   SMTP hardcoded, nunca        │   ├── error_handler.py
│   importado)                   │   └── auth.py
└── utils/helpers.py             ├── models/            # SQLAlchemy 2.0 + métodos de domínio
    (duplicado, não usado)       ├── utils/helpers.py   # canônico (única implementação)
                                  └── seed.py
                                  # services/ REMOVIDO (código morto)
```

Principais correções: MD5 → hash `werkzeug.security`, senha removida das respostas da API (`to_dict()`/login não vazam mais o hash), token de login trocado pelo literal `'fake-jwt-token-' + id` por um token assinado, **0 usos de `datetime.utcnow()` e 0 usos de `Model.query.get()` restantes** (as 22 + 16 ocorrências deprecated foram eliminadas — RP-10), N+1 em `GET /tasks` resolvido com eager loading/JOIN, e absorção das camadas de fachada mortas (`services/` removido, `Task.is_overdue()`/`to_dict()` do model passam a ser a única implementação em vez de 6 cópias inline nas rotas).

### Checklist de validação preenchido

#### Projeto 1 — code-smells-project

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — Python
- [x] Framework detectado corretamente — Flask 3.1.1
- [x] Domínio da aplicação descrito corretamente — E-commerce (produtos, usuários, pedidos)
- [x] Número de arquivos analisados condiz com a realidade — 4 arquivos (app.py, controllers.py, models.py, database.py)

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados — 30 findings
- [x] Detecção de APIs deprecated incluída (se aplicável) — verificado; stack sem ORM/datetime não acusou ocorrências de AP-12 relevantes
- [x] Skill pausa e pede confirmação antes da Fase 3 — prompt `[y/n]` exibido e respeitado

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — `src/{config,models,controllers,views,middlewares}`
- [x] Configuração extraída para módulo de config (sem hardcoded) — `src/config/settings.py` + `.env.example`
- [x] Models criados para abstrair dados — `produto_model.py`, `usuario_model.py`, `pedido_model.py`
- [x] Views/Routes separadas — `src/views/routes.py`
- [x] Controllers concentram o fluxo da aplicação — `src/controllers/*`
- [x] Error handling centralizado — `src/middlewares/error_handler.py`
- [x] Entry point claro — `app.py` (composition root)
- [x] Aplicação inicia sem erros — boot confirmado (`SECRET_KEY=... PORT=5055 python app.py`)
- [x] Endpoints originais respondem corretamente — `GET /produtos` retornou 200 com o catálogo completo
```

#### Projeto 2 — ecommerce-api-legacy

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — JavaScript (Node.js)
- [x] Framework detectado corretamente — Express 4.18.2
- [x] Domínio da aplicação descrito corretamente — LMS com fluxo de checkout (cursos, matrículas, pagamentos)
- [x] Número de arquivos analisados condiz com a realidade — `src/app.js`, `src/AppManager.js`, `src/utils.js`

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados — 21 findings
- [x] Detecção de APIs deprecated incluída (se aplicável) — callback hell (11 chamadas) e Express 4 sinalizados sob AP-12
- [x] Skill pausa e pede confirmação antes da Fase 3 — prompt `[y/n]` exibido e respeitado

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — `src/{config,db,models,services,controllers,routes,middlewares}`
- [x] Configuração extraída para módulo de config (sem hardcoded) — `src/config/index.js` + `.env`
- [x] Models criados para abstrair dados — 5 models (`userModel`, `courseModel`, `enrollmentModel`, `paymentModel`, `auditLogModel`)
- [x] Views/Routes separadas — `src/routes/{checkoutRoutes,adminRoutes,userRoutes}.js`
- [x] Controllers concentram o fluxo da aplicação — `src/controllers/{checkoutController,reportController,userController}.js`
- [x] Error handling centralizado — `src/errors.js` + `middlewares/errorHandler.js`
- [x] Entry point claro — `src/app.js`
- [x] Aplicação inicia sem erros — boot confirmado (`PORT=3010 node src/app.js`, seed automático no init)
- [x] Endpoints originais respondem corretamente — `POST /api/checkout` (200, matrícula criada) e `GET /api/admin/financial-report` (200) testados
```

#### Projeto 3 — task-manager-api

```markdown
## Checklist de Validação

### Fase 1 — Análise
- [x] Linguagem detectada corretamente — Python
- [x] Framework detectado corretamente — Flask 3.0.0 + SQLAlchemy
- [x] Domínio da aplicação descrito corretamente — Task Manager (tarefas, categorias, usuários, relatórios)
- [x] Número de arquivos analisados condiz com a realidade — `app.py`, `database.py`, `models/`, `routes/`, `services/`, `utils/`

### Fase 2 — Auditoria
- [x] Relatório segue o template definido nos arquivos de referência
- [x] Cada finding tem arquivo e linhas exatos
- [x] Findings ordenados por severidade (CRITICAL → LOW)
- [x] Mínimo de 5 findings identificados — 26 findings
- [x] Detecção de APIs deprecated incluída (se aplicável) — 22 usos de `datetime.utcnow()` + 16 usos de `Model.query.get()` catalogados
- [x] Skill pausa e pede confirmação antes da Fase 3 — prompt `[y/n]` exibido e respeitado

### Fase 3 — Refatoração
- [x] Estrutura de diretórios segue padrão MVC — `{config,controllers,routes,middlewares,models,utils}/`
- [x] Configuração extraída para módulo de config (sem hardcoded) — `config/settings.py` + `.env`
- [x] Models criados para abstrair dados — `models/{user,task,category}.py` com métodos de domínio (`is_overdue()`, `to_dict()`)
- [x] Views/Routes separadas — `routes/*` finas (inclui `category_routes.py`, novo)
- [x] Controllers concentram o fluxo da aplicação — `controllers/*`
- [x] Error handling centralizado — `middlewares/error_handler.py`
- [x] Entry point claro — `app.py` (App Factory `create_app`)
- [x] Aplicação inicia sem erros — `python seed.py` (sem `DeprecationWarning`) + boot confirmado (`PORT=5056 python app.py`)
- [x] Endpoints originais respondem corretamente — `GET /tasks` (200) e `POST /login` (200, hash da senha não vaza mais na resposta)
```

### Logs de execução (evidência)

Boot e chamadas reais capturados após a refatoração dos 3 projetos, para validar o critério "aplicação funciona":

```
# Projeto 1 — boot
2026-08-11 14:36:55 INFO src.database: Banco loja.db inicializado com seed (10 produtos, 3 usuários)
2026-08-11 14:36:55 INFO src.app: Servidor iniciado em http://127.0.0.1:5055
 * Running on http://127.0.0.1:5055
$ curl localhost:5055/produtos
{"dados":[{"id":1,"nome":"Notebook Gamer","preco":5999.99,...}]}   # HTTP 200

# Projeto 2 — boot
{"level":"info","message":"db.init","seeded":true,"users":1,"courses":2}
{"level":"info","message":"server.started","port":3010,"authEnforced":false}
$ curl -X POST localhost:3010/api/checkout -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
{"msg":"Sucesso","enrollment_id":2}                                 # HTTP 200 — sem PAN/segredo no log
$ curl localhost:3010/api/admin/financial-report
[{"course":"Clean Architecture","revenue":997,...}]                 # HTTP 200

# Projeto 3 — seed + boot
INFO __main__: Seed concluído com sucesso! (3 usuários, 4 categorias, 10 tasks)   # sem DeprecationWarning
 * Running on http://127.0.0.1:5056
$ curl -X POST localhost:5056/login -d '{"email":"joao@email.com","password":"..."}'
{"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxLCJyb2xlIjoiYWRtaW4ifQ...","user":{...}}  # HTTP 200 — sem campo "password"
$ curl localhost:5056/tasks
[{"id":1,"title":"Implementar autenticação JWT","user_name":"João Silva",...}]     # HTTP 200
```

### Observações sobre comportamento em stacks diferentes

A **mesma skill**, copiada sem nenhuma alteração (`SKILL.md` + 5 referências idênticos byte a byte nos 3 projetos), funcionou nos 3 stacks-alvo do desafio: um monolito procedural em Flask com SQL cru (Projeto 1), uma God Class em Express com callback hell e banco `:memory:` (Projeto 2), e um Flask+SQLAlchemy que já tinha camadas de fachada mortas (Projeto 3) — o que comprova o agnosticismo de tecnologia exigido.

A Fase 3 se adaptou ao contexto de cada projeto, como previsto na regra de adaptação: nos dois monolitos (Projetos 1 e 2) a skill fez uma reescrita completa em camadas MVC; no Projeto 3 ela fez uma reorganização adaptada, absorvendo os métodos de domínio que já existiam nos models em vez de recriá-los do zero, e removendo apenas o que era código morto (`services/`).

## Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e configurado
- Python 3 + `venv` (para `code-smells-project` e `task-manager-api`, ambos Flask)
- Node.js + npm (para `ecommerce-api-legacy`, Express)

### Comandos para executar a skill em cada projeto

```bash
# Projeto 1 — Python/Flask
cd code-smells-project && claude "/refactor-arch"

# Projeto 2 — Node/Express
cd ../ecommerce-api-legacy && claude "/refactor-arch"

# Projeto 3 — Python/Flask + SQLAlchemy
cd ../task-manager-api && claude "/refactor-arch"
```

Em cada execução, revise o relatório impresso na Fase 2 e responda `y` no prompt `Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]` para a skill prosseguir com a refatoração.

### Como validar que a refatoração funcionou

Suba cada aplicação já refatorada e exercite os endpoints originais.

> **Nota:** no macOS a porta 5000 costuma estar ocupada pelo AirPlay Receiver — use uma porta livre via variável de ambiente (ex.: `PORT=5055`).

```bash
# Projeto 1
cd code-smells-project
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
SECRET_KEY=dev PORT=5055 python app.py
# em outro terminal:
curl localhost:5055/produtos

# Projeto 2
cd ecommerce-api-legacy
npm install
PORT=3010 node src/app.js
# em outro terminal (ver payloads completos em api.http):
curl -X POST localhost:3010/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'

# Projeto 3
cd task-manager-api
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python seed.py
SECRET_KEY=dev PORT=5056 python app.py
# em outro terminal:
curl localhost:5056/tasks
```

Se a aplicação subir sem erros e os endpoints acima responderem com HTTP 200, a refatoração preservou o contrato original — que é exatamente o que a Fase 3 da skill valida automaticamente ao final de cada execução.

---

## Dicas Finais

- **Comece pela análise manual** — entender os problemas profundamente é essencial para criar uma skill que os detecte.
- **O SKILL.md é um prompt** — ele instrui o agente sobre o que fazer, enquanto os arquivos de referência fornecem o conhecimento de domínio.
- **Seja específico nos sinais de detecção** — "código ruim" não ajuda; "query SQL dentro de loop for" é acionável.
- **Teste incrementalmente** — não tente criar a skill perfeita de primeira.
- **A skill deve ser copiável** — se ela só funciona em um projeto específico, está acoplada demais. Teste nos 3 projetos para validar.
- **Projetos diferentes exigem adaptação** — a Fase 3 de um projeto já parcialmente organizado não vai ter as mesmas transformações de um monolito. Sua skill deve se adaptar ao contexto.
- **Pedir confirmação na Fase 2 é obrigatório** — o humano deve revisar o relatório antes de qualquer modificação.
- **Consulte as referências do curso** — revise a documentação oficial da ferramenta escolhida e os materiais das aulas para relembrar a estrutura e anatomia de uma skill.