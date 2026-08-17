# Plano de Remediação — Aplicar Autenticação de Fato (RP-12 vivo)

**Data:** 2026-08-17
**Motivo:** A entrega foi reprovada. Nos 3 projetos a Fase 3 montou a infraestrutura de
autenticação mas **não a ligou às rotas sensíveis** (`ENFORCE_AUTH=0` no ecommerce; decorators
declarados mas não aplicados no task-manager). Assim, os próprios findings CRITICAL/HIGH da
auditoria (DELETE sem auth, relatório financeiro público) continuam reproduzíveis na aplicação
como ela sobe.

## Causa-raiz (por que a skill deixou isso passar)

1. **SKILL.md** — a regra "o contrato HTTP não pode quebrar" (Fase 3, item 4, e Regras gerais)
   não tinha exceção para segurança. Foi lida como "manter 200 sem token", o oposto da correção.
2. **Validação da Fase 3** — só exige "endpoints respondem"; um `200` **sem token** numa rota que
   a auditoria marcou como "sem auth" **passa** na validação atual. A validação nunca testa auth.
3. **RP-12** — descreve auth corretamente (inclusive "apenas passam a exigir auth"), mas não
   **proíbe** entregar a infra desconectada (decorator não aplicado, flag default-off).

Conclusão: a lógica do playbook estava quase certa; faltou **obrigar a aplicação viva** e
**validar** isso. O erro é de execução + lacuna de skill, não de conceito.

## Princípio da correção

**Segurança vence contrato.** Para as rotas que a Fase 2 marcou em AP-05/AP-06, o comportamento
correto muda de "200 anônimo" para **401/403 sem token** e **2xx com token** (obtido no login).
Isso É a correção do finding — não é quebra de contrato. Método+path permanecem.

---

## Fase A — Endurecer a skill (documentar nos agentes p/ não recorrer) ✅ nesta entrega

Aplicar em **todas as 3 cópias idênticas** de `.claude/skills/refactor-arch/`:

1. **SKILL.md — Fase 3, item 3:** adicionar item obrigatório: aplicar RP-12 de fato às rotas
   destrutivas/sensíveis dos findings AP-05/AP-06; infra desconectada (decorator não aplicado,
   `ENFORCE_AUTH=0`, flag default-off, comentário "não aplicado ao baseline") **não** elimina o
   finding e reprova a Fase 3.
2. **SKILL.md — Fase 3, item 4:** carve-out de segurança na regra de contrato (rotas AP-05/AP-06
   passam a exigir `Authorization`; 401/403 sem token não é quebra de contrato).
3. **SKILL.md — bloco de Validação:** novo item obrigatório — para cada rota flagada, provar
   `401/403 sem token` e `2xx com token`. `200` sem token numa rota flagada = ✗.
4. **SKILL.md — Regras gerais:** emendar "Não quebre contratos" com a exceção de segurança.
5. **refactoring-playbook.md — RP-12 (Notas):** aviso explícito de que a aplicação é obrigatória
   e que infra desconectada/atrás de flag desligada reprova a Fase 3.
6. **anti-patterns-catalog.md — AP-05/AP-06:** nota de que a remediação tem de ser verificada viva.
7. **mvc-guidelines.md — Middlewares:** auth "efetivamente aplicada", não opcional.

Manter as 3 cópias byte-idênticas (editar uma, sincronizar as outras; `diff -rq` deve bater).

## Fase B — Re-rodar a Fase 3 (auth) em cada projeto

Rotas a proteger, conforme cada relatório (o `/login` já emite token verificável nos 3):

- **code-smells-project** (AP-06): mutações de produto (`POST/PUT/DELETE /produtos[/<id>]`),
  criação de pedido (`POST /pedidos`) e listagem de usuários (`GET /usuarios`, dado sensível) →
  exigir token; rotas `/admin/*` já removidas (AP-05).
- **ecommerce-api-legacy** (AP-05/AP-06): `DELETE /api/users/:id` e `GET /api/admin/financial-report`
  (todo `/api/admin/*`) → aplicar `authMiddleware` **sempre** (remover o gate `ENFORCE_AUTH`;
  auth ligada por padrão).
- **task-manager-api** (AP-05/AP-06): `DELETE /tasks/<id>`, `DELETE /users/<id>`,
  `DELETE /categories/<id>` (e rotas admin) → aplicar `@auth_required`/`@admin_required`;
  remover o comentário/So padrão "não aplicado ao baseline".

Login continua público; leituras não sensíveis permanecem públicas (evitar 401 em massa que
esconderia regressões — proteger o que a auditoria apontou, não tudo).

## Fase C — Re-validar com testes autenticados

Para cada projeto, subir a app e provar, com evidência (curl), em cada rota flagada:
- sem `Authorization` → **401/403**;
- `POST /login` → obter token;
- com `Bearer <token>` → **2xx** esperado.
Além do boot limpo + endpoints públicos ainda respondendo. Atualizar os baselines
(`.superpowers/sdd/baseline-project-*.md`) para refletir o novo contrato dessas rotas.

## Fase D — Atualizar docs + re-entregar

- Atualizar `reports/audit-project-*.md`? Não — os relatórios permanecem (retratam o legado).
  Registrar a mudança de comportamento (rotas agora exigem auth) no output/README.
- Atualizar `reports/checklist-validacao.html` com a nova evidência de auth por projeto.
- Atualizar README (Resultados) mencionando a auth aplicada.
- Commit + merge em `main` + push para `origin`.

## Critério de aceite (o que o avaliador vai checar)

Na aplicação **como ela sobe** (sem flags manuais): cada rota destrutiva/sensível dos relatórios
retorna **401/403 sem token** e funciona **com token**. Nenhum `ENFORCE_AUTH=0` nem decorator
desconectado. Validação da Fase 3 prova isso nos 3 projetos.
