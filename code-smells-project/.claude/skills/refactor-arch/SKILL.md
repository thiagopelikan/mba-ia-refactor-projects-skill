---
name: refactor-arch
description: Analisa, audita e refatora um projeto backend para o padrão MVC. Detecta stack (linguagem/framework/DB), cruza o código contra um catálogo de anti-patterns e code smells classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW), gera um relatório de auditoria, pede confirmação e então reestrutura o projeto para MVC validando que a aplicação continua funcionando. Agnóstica de tecnologia (Python/Flask, Node/Express e outros).
---

# refactor-arch — Auditoria e Refatoração Arquitetural para MVC

## Visão geral

Você vai executar **3 fases sequenciais** sobre o projeto do diretório atual:

1. **Fase 1 — Análise:** detectar a stack e mapear a arquitetura atual.
2. **Fase 2 — Auditoria:** cruzar o código contra o catálogo de anti-patterns e gerar o relatório. **PAUSAR e pedir confirmação antes de qualquer modificação.**
3. **Fase 3 — Refatoração:** reestruturar para o padrão MVC e validar que a aplicação continua funcionando.

Regras invioláveis:

- **Nunca pule fases** e nunca execute a Fase 3 sem a confirmação explícita do usuário na Fase 2.
- **Seja agnóstico de stack:** esta skill deve funcionar igualmente em Python/Flask (com ou sem ORM), Node.js/Express e outros backends. Nunca assuma a linguagem — detecte-a na Fase 1 e adapte tudo o que vier depois.
- **Nunca modifique arquivos nas Fases 1 e 2.** Elas são somente leitura (exceto salvar o relatório em `reports/`, que não altera código).

Arquivos de referência desta skill (leia cada um na fase indicada):

| Fase | Arquivo | Conteúdo |
|---|---|---|
| 1 | `references/project-analysis.md` | Heurísticas de detecção de linguagem, framework, DB, domínio e arquitetura |
| 2 | `references/anti-patterns-catalog.md` | Catálogo de anti-patterns com IDs, severidades e sinais de detecção |
| 2 | `references/audit-report-template.md` | Formato exato do relatório de auditoria |
| 3 | `references/mvc-guidelines.md` | Estrutura-alvo MVC: camadas, responsabilidades e regras de dependência |
| 3 | `references/refactoring-playbook.md` | Transformações concretas antes/depois para cada anti-pattern |

---

## Fase 1 — Análise

1. Leia `references/project-analysis.md` e siga as heurísticas de lá.
2. Detecte, com evidência concreta (arquivo de manifesto, imports, DDL):
   - **Linguagem** (extensões dos arquivos-fonte + manifesto);
   - **Framework e versão** (manifesto: `requirements.txt`/`pyproject.toml`/`package.json`; confirmar por imports/`require`);
   - **Dependências** relevantes (incluindo as declaradas mas não usadas — anote, vira finding na Fase 2);
   - **Banco de dados** (driver, ORM, strings de conexão, `CREATE TABLE`, models) e a **lista de tabelas**;
   - **Domínio** da aplicação (inferido de tabelas, rotas e entidades);
   - **Arquitetura atual** (monolito procedural / God Class / parcialmente em camadas / MVC), entry point, porta e como a app inicia;
   - **Contagem de arquivos-fonte e LoC** (exclua `node_modules/`, `.venv/`, `.claude/`, lockfiles).
3. Imprima o bloco-resumo EXATAMENTE neste formato (modelo completo no arquivo de referência):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem>
Framework:     <framework + versão>
Dependencies:  <deps relevantes>
Domain:        <domínio inferido>
Architecture:  <classificação + descrição curta>
Source files:  <N> files analyzed
DB tables:     <tabelas>
================================
```

4. Mapeie e guarde a **lista de todos os endpoints originais (método HTTP + path)** — ela é o contrato que a Fase 3 deve preservar e validar.

---

## Fase 2 — Auditoria

1. Leia `references/anti-patterns-catalog.md` e `references/audit-report-template.md`.
2. Leia **cada arquivo-fonte por inteiro** e cruze contra **todos** os anti-patterns do catálogo (IDs AP-01 a AP-16), usando os sinais de detecção de cada entrada.
3. Para cada ocorrência, produza um finding com:
   - severidade e nome/ID do anti-pattern (exatamente como no catálogo);
   - **arquivo e linha(s) exatos** — abra o arquivo e cite a linha real; **nunca invente arquivo/linha, nunca omita a linha**;
   - descrição com evidência concreta (trecho ou valor encontrado);
   - impacto;
   - recomendação apontando o padrão do playbook (RP-NN) que o corrige.
4. Renderize o relatório **no formato exato do template**, com os findings **ordenados por severidade (CRITICAL → HIGH → MEDIUM → LOW)**.
5. Imprima o `## Summary` com a contagem por severidade (`CRITICAL: n | HIGH: n | MEDIUM: n | LOW: n`) e o rodapé `Total: N findings`.
6. Quando o usuário indicar (ou quando o fluxo do desafio pedir), salve o relatório em `reports/audit-project-N.md` na raiz do repositório (N = 1, 2 ou 3 conforme o projeto).
7. **PAUSE AQUI.** Pergunte exatamente:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- **Não modifique nenhum arquivo do projeto antes de receber `y`.**
- Se a resposta for `n`, encerre a execução educadamente sem tocar em nada.

---

## Fase 3 — Refatoração

Execute **somente após o `y`** da Fase 2.

1. Leia `references/mvc-guidelines.md` (estrutura-alvo e regras de dependência) e `references/refactoring-playbook.md` (transformações antes/depois).
2. Crie a estrutura de diretórios MVC conforme as guidelines, usando as camadas: **Config**, **Models**, **Views/Routes**, **Controllers**, **Middlewares** e **Entry point / Composition root** (nomes equivalentes para Node: `config/`, `models/`, `routes/`, `controllers/`, `middlewares/`, `app.js`).
3. Aplique os padrões do playbook para **eliminar cada finding** da Fase 2, no mínimo:
   - extrair configuração para o módulo Config (zero valores hardcoded; criar `.env.example`);
   - criar Models para abstrair o acesso a dados (um por domínio);
   - separar Views/Routes (rotas HTTP finas, sem SQL nem regra de negócio);
   - concentrar o fluxo da aplicação em Controllers;
   - centralizar o error handling em Middlewares;
   - definir o Entry point / Composition root limpo (monta a app, injeta dependências, registra rotas e middlewares — nada de lógica);
   - **aplicar de fato autenticação/autorização (RP-12) às rotas destrutivas e sensíveis marcadas em AP-05/AP-06** — o middleware/decorator fica LIGADO às rotas por padrão. Entregar a infra de auth desconectada (decorator declarado mas não aplicado, `ENFORCE_AUTH=0`/flag desligada por padrão, comentário "não aplicado ao baseline") **NÃO** elimina o finding e **reprova a Fase 3**.
4. **Preserve o contrato de endpoints (método + path) — mas segurança vence contrato.** Todos os endpoints originais continuam existindo com o mesmo método+path. **Exceção obrigatória:** as rotas que a Fase 2 marcou em AP-05/AP-06 (destrutivas/sensíveis sem auth) passam a exigir `Authorization` — sem token retornam **401/403**, o que é a *correção* do finding, não uma quebra de contrato. Rotas de SQL arbitrário são removidas.
5. Ao final, imprima a nova estrutura e rode a **validação**:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios resultante>

## Validation
  ✓/✗ Application boots without errors
  ✓/✗ All endpoints respond correctly
  ✓/✗ Sensitive routes (AP-05/AP-06) enforce auth: 401 without token, 2xx with token
  ✓/✗ Zero anti-patterns remaining
================================
```

Validação obrigatória (reporte ✓ ou ✗ para cada item, com evidência):

- **Boot:** inicie a aplicação (`python app.py` / `npm start` ou equivalente detectado na Fase 1) e confirme que sobe sem tracebacks/exceptions. Encerre o processo depois.
- **Endpoints:** exercite os endpoints originais (via `curl` ou requisições equivalentes) e confirme que cada um responde com status coerente. Liste método + path + status.
- **Autenticação (obrigatório quando a Fase 2 apontou AP-05/AP-06):** para CADA rota destrutiva/sensível marcada, prove com evidência: (a) sem `Authorization` → **401/403**; (b) com token válido obtido no login → status esperado (2xx). Um **200 sem token** numa rota que a auditoria marcou como "sem auth" é **✗ (falha)** — o finding continua reproduzível na app. Liste método + path + status-sem-token + status-com-token.
- Se algo falhar (✗), corrija e revalide antes de encerrar — não entregue a Fase 3 com validação quebrada.

---

## Regras gerais

- **Adapte o esforço ao nível de organização do projeto:** um monolito procedural (tudo em 3-4 arquivos) exige criar as camadas do zero; um projeto já parcialmente em camadas (ex.: `models/`, `routes/`, `services/` existentes) exige **reorganizar e completar** — mover lógica das rotas para controllers/services, absorver ou remover camadas de fachada/código morto — em vez de recriar tudo. Siga a "Regra de adaptação" das guidelines.
- **Se o projeto já usa ORM** (ex.: SQLAlchemy), refatore **sobre o ORM** — nunca reintroduza SQL cru.
- **Nunca invente arquivo/linha:** todo finding e toda transformação citam evidência real do código.
- **Não quebre contratos — exceto para corrigir segurança:** os endpoints originais (método + path) continuam respondendo após a refatoração; a única mudança de status permitida (e exigida) na trilha feliz é que rotas destrutivas/sensíveis marcadas em AP-05/AP-06 passam a exigir `Authorization` (401/403 sem token). Nunca deixe a auth desconectada para "preservar o baseline" — isso mantém o finding vivo.
- **Idioma:** todo o output (resumos, relatório, mensagens) em português; os rótulos estruturais dos blocos (`PHASE 1: PROJECT ANALYSIS`, `## Summary`, `File:`, `Total:` etc.) permanecem como nos templates.
