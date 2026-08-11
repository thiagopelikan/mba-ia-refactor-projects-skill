================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js) + Express 4.18.2
Files:   3 analyzed | ~180 lines of code

## Summary
CRITICAL: 6 | HIGH: 7 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: src/utils.js:1-7
Description: Objeto `config` com credenciais literais no código-fonte: `dbUser: "admin_master"` (linha 2), `dbPass: "senha_super_secreta_prod_123"` (linha 3), chave de gateway de pagamento com prefixo de produção `paymentGatewayKey: "pk_live_1234567890abcdef"` (linha 4) e `smtpUser: "no-reply@fullcycle.com.br"` (linha 5). A chave `pk_live` ainda vaza no stdout a cada checkout (ver finding AP-04 em AppManager.js:45).
Impact: Qualquer pessoa com acesso ao repositório (ou ao histórico do git) obtém credenciais reais de produção; rotacionar a chave exige alterar código e fazer deploy; o segredo vaza também em logs.
Recommendation: Aplicar RP-01 — extrair para módulo `config/` lendo de variáveis de ambiente (`process.env`), com `.env.example` documentando as chaves sem valores reais.

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: src/AppManager.js:18
Description: Seed insere usuário com senha em texto plano: `INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')`. A senha nunca passa por hash — nem pelo `badCrypto` usado no checkout.
Impact: Credencial real de usuário legível por qualquer um com acesso ao código; como o banco é `:memory:`, esse usuário com senha em claro é recriado a cada boot, em qualquer ambiente.
Recommendation: Aplicar RP-01 (seed fora do código, com valores de ambiente) + RP-04 (armazenar apenas hash seguro com salt — bcrypt/scrypt/argon2).

### [CRITICAL] God Class / God Module / God Method (AP-03)
File: src/AppManager.js:4-139
Description: A classe `AppManager` concentra tudo: conexão SQLite (linha 7), DDL das 5 tabelas + seed (`initDb`, linhas 10-23), roteamento HTTP (`setupRoutes`, linhas 25-138), regra de negócio de pagamento (linha 46), criação de usuário com hash (linhas 66-72), auditoria (linha 57) e cache (linha 59). Contém também God Methods: o handler de checkout tem 50 linhas com 5 níveis de aninhamento (linhas 28-78) e o de relatório tem 49 linhas com 4 níveis (linhas 80-129).
Impact: Viola completamente a separação de responsabilidades do MVC; impossível testar pagamento, matrícula ou relatório em isolamento; qualquer mudança em uma responsabilidade arrisca todas as outras.
Recommendation: Aplicar RP-03 — quebrar em `config/`, `models/` (users, courses, enrollments, payments, audit), `controllers/`, `routes/` e `middlewares/`, com entry point limpo em `app.js`.

### [CRITICAL] Weak/Broken Password Hashing & Exposição de Senha (AP-04)
File: src/utils.js:17-23
Description: Hash caseiro `badCrypto`: concatena 10.000 vezes os 2 primeiros caracteres do base64 da senha (`Buffer.from(pwd).toString('base64').substring(0, 2)`, linha 20) e trunca em 10 caracteres (linha 22). O resultado é apenas os 2 primeiros caracteres base64 repetidos 5x — depende só do primeiro ~1,5 byte da senha, sem salt, determinístico e trivialmente reversível. Usado em `AppManager.js:68` para criar usuários no checkout.
Impact: Todas as senhas que começam com os mesmos 1-2 caracteres colidem no mesmo "hash"; um dicionário de dezenas de entradas reverte qualquer senha; equivale a armazenar texto plano.
Recommendation: Aplicar RP-04 — substituir por bcrypt/scrypt/argon2 com salt; nunca implementar hash próprio.

### [CRITICAL] Weak/Broken Password Hashing & Exposição de Senha (AP-04)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` loga o número completo do cartão de crédito e a chave `pk_live` a cada checkout. Confirmado no baseline: o stdout registrou `Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef`.
Impact: PAN completo em log viola PCI-DSS; logs costumam ir para arquivos/agregadores acessíveis a muita gente — vazamento direto de dado de pagamento + segredo de produção em cada requisição.
Recommendation: Aplicar RP-04 (nunca logar dado sensível; mascarar `****4444`) + RP-01 (segredo sai do código e nunca vai a log).

### [CRITICAL] Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth (AP-05)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` executa `DELETE FROM users WHERE id = ?` (linha 133) sem nenhuma verificação de autenticação ou autorização — qualquer cliente anônimo apaga qualquer usuário. Confirmado no baseline: `curl -X DELETE /api/users/1` → 200.
Impact: Destruição de dados por requisição anônima; combinado com a ausência de FK/cascade, ainda corrompe a integridade (ver AP-09).
Recommendation: Aplicar RP-12 — exigir autenticação/autorização (middleware) em rotas destrutivas; avaliar soft-delete.

### [HIGH] Missing Authentication / Authorization (AP-06)
File: src/AppManager.js:80, 40, 73-75
Description: Nenhuma rota tem autenticação. `GET /api/admin/financial-report` (linha 80) é rota administrativa aberta ao público — devolve nomes de alunos e valores pagos (confirmado no baseline: 200 sem credencial). Pior: no checkout, o usuário é localizado só pelo email (linha 40) e, se existir, a matrícula/cobrança é feita na conta dele sem verificar a senha (linhas 73-75) — basta conhecer o email de alguém para operar em nome dele.
Impact: Exposição de dados pessoais e financeiros a qualquer anônimo; apropriação de conta alheia por email; impossível auditar quem fez o quê.
Recommendation: Aplicar RP-12 — middleware de autenticação (JWT/sessão) nas rotas sensíveis e verificação de credencial antes de usar conta existente.

### [HIGH] Business Logic in Controller/Route (AP-07)
File: src/AppManager.js:28-78
Description: O handler HTTP de `POST /api/checkout` contém toda a regra de negócio inline: decisão de aprovação do "gateway" (`cc.startsWith("4") ? "PAID" : "DENIED"`, linha 46), criação de usuário com hash (linhas 66-72), matrícula (linha 50), pagamento (linha 54), auditoria (linha 57) e cache (linha 59) — parsing, validação, SQL e formatação de resposta misturados na rota.
Impact: A regra de pagamento/matrícula não é testável sem subir HTTP; qualquer nova rota que precise da mesma regra vai duplicá-la; viola MVC e SRP.
Recommendation: Aplicar RP-05 — mover o fluxo para um controller/serviço de checkout que orquestre models (User, Course, Enrollment, Payment), deixando a rota fina.

### [HIGH] Global Mutable State (AP-08)
File: src/utils.js:9, 12-15
Description: `globalCache = {}` é variável de módulo mutável compartilhada entre todas as requisições; `logAndCache` (linhas 12-15) só adiciona chaves (`globalCache[key] = data`, chamada por checkout em `AppManager.js:59` com chave `last_checkout_${userId}`) e nada nunca remove — cresce indefinidamente.
Impact: Memory leak proporcional ao número de checkouts; condição de corrida entre requisições; estado divergente entre workers/instâncias — impossibilita escalar horizontalmente.
Recommendation: Aplicar RP-06 — remover o cache global; se cache for necessário, usar store com escopo e expiração (ex.: Redis) injetado via composition root.

### [HIGH] Global Mutable State (AP-08)
File: src/utils.js:10, 25; src/AppManager.js:2
Description: `totalRevenue = 0` (linha 10) é exportado por valor em `module.exports` (linha 25): como number primitivo, o `require` em `AppManager.js:2` recebe uma cópia congelada em `0` — qualquer reatribuição em um módulo jamais refletiria no outro. O acumulador de receita é, por construção, um bug: nunca sairia de zero para os consumidores.
Impact: Estado de negócio (receita) modelado como global quebrado; se algum código passasse a "somar" nele, produziria relatório financeiro silenciosamente errado (sempre 0 ou divergente por módulo/worker).
Recommendation: Aplicar RP-06 — eliminar o acumulador global; receita deve ser derivada do banco (SUM sobre payments), nunca de variável de módulo.

### [HIGH] Missing Transaction / Non-atomic Writes (AP-09)
File: src/AppManager.js:50-63, 66-72
Description: O checkout encadeia até 4 INSERTs relacionados (users linha 69 → enrollments linha 50 → payments linha 54 → audit_logs linha 57) via callbacks independentes, sem `BEGIN`/`COMMIT`/`ROLLBACK`. Se o INSERT de payments falhar (linha 55), a matrícula já persistida fica sem pagamento; se audit_logs falhar, o erro é até ignorado.
Impact: Falha no meio do fluxo deixa o banco inconsistente — matrícula sem pagamento (aluno com acesso grátis) ou usuário criado sem matrícula; impossível reconciliar o financeiro.
Recommendation: Aplicar RP-07 — envolver o conjunto em transação (`BEGIN TRANSACTION`/`COMMIT` com `ROLLBACK` no erro), idealmente com a API promisificada.

### [HIGH] Missing Transaction / Non-atomic Writes (AP-09)
File: src/AppManager.js:131-137
Description: `DELETE /api/users/:id` apaga só a linha de `users` (linha 133) e deixa `enrollments` e `payments` órfãos — a própria resposta admite: "Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco." (linha 135). Não há FK com `ON DELETE`, transação nem limpeza relacionada.
Impact: Integridade referencial corrompida a cada delete; o relatório financeiro passa a mostrar `student: 'Unknown'` (linha 113) e valores irreconciliáveis.
Recommendation: Aplicar RP-07 — delete transacional das entidades relacionadas (ou FKs com `ON DELETE CASCADE`/soft-delete), dentro de uma transação única.

### [HIGH] Insecure Config em Produção (AP-10)
File: src/app.js:5-6
Description: Express configurado sem nenhum hardening: sem `helmet` (headers de segurança), `express.json()` sem `limit` (linha 6 — payload ilimitado), sem rate limiting no checkout (rota que cria usuários e "processa" cartões pode ser martelada à vontade), sem CORS explícito.
Impact: Payloads gigantes permitem DoS por memória; ausência de rate limit permite brute-force/enumeração de emails e flood de checkouts; sem headers de segurança padrão.
Recommendation: Aplicar RP-12 — adicionar `helmet`, `express.json({ limit: '...' })` e rate limiting (ex.: `express-rate-limit`) nas rotas sensíveis, configurados no composition root.

### [MEDIUM] N+1 Query (AP-11)
File: src/AppManager.js:83-127
Description: O relatório financeiro faz `db.all` de todos os cursos (linha 83) e, por curso, `db.all` de enrollments (linha 92); por enrollment, `db.get` do user (linha 104) e `db.get` do payment (linha 106) — padrão 1 + C + 2×E queries dentro de `forEach` aninhados, sincronizado por contadores manuais (`coursesPending`/`enrPending`, linhas 86, 93).
Impact: Latência cresce linearmente com alunos/cursos (com 100 cursos × 1.000 matrículas seriam ~200.101 queries por request); os contadores manuais ainda tornam a ordem do array não-determinística.
Recommendation: Aplicar RP-09 — uma única query com JOIN (courses ⟕ enrollments ⟕ users ⟕ payments) + agregação, montando o shape no controller.

### [MEDIUM] Deprecated API Usage (AP-12)
File: src/AppManager.js:37-77, 83-128
Description: Todo o acesso a dados usa error-first callbacks aninhados (callback hell): 5 níveis no checkout (`db.get` → `db.get` → `db.run` → `db.run` → `db.run`, linhas 37-63) e 4 níveis no relatório com sincronização manual por contadores (linhas 83-127) — 11 chamadas de callback no total. O catálogo lista o padrão como obsoleto frente a `async/await` + Promises.
Impact: Fluxo ilegível e propenso a erro (callbacks esquecem tratamento de `err` — ver AP-16); impossibilita `try/catch` e transações limpas; dificulta manutenção e testes.
Recommendation: Aplicar RP-13 — promisificar o driver (`util.promisify` ou wrapper) e reescrever os fluxos com `async/await`.

### [MEDIUM] Deprecated API Usage (AP-12)
File: package.json:10-11
Description: `"express": "^4.18.2"` — projeto na major 4 do Express (o catálogo recomenda avaliar migração para Express 5) e com range `^` em vez de versão pinada; idem `"sqlite3": "^5.1.6"`. Não há lockfile-based pin de major no manifesto.
Impact: Express 4 fica para trás em correções e no tratamento nativo de erros async (relevante dado o callback hell); ranges permitem que builds diferentes resolvam versões diferentes.
Recommendation: Aplicar RP-10 — planejar migração para Express 5 durante a refatoração e pinar versões no manifesto.

### [MEDIUM] Missing Input Validation (AP-13)
File: src/AppManager.js:35, 46, 68, 132
Description: A validação do checkout (linha 35) só checa presença de 4 campos: `pwd` não é validado e cai no default `"123456"` (linha 68 — conta criada silenciosamente com senha fraca conhecida); tipos nunca são checados — **crash confirmado em teste**: enviar `"card"` como número JSON (`4111222233334444` sem aspas) passa na checagem truthy e explode em `cc.startsWith` (linha 46) com `TypeError` dentro do callback do sqlite3, **derrubando o processo Node inteiro** (nenhuma resposta; servidor morto). Email não tem validação de formato; `req.params.id` do DELETE (linha 132) não é validado como número. Erros de payload viram texto plano sem shape de erro JSON consistente.
Impact: Um único request malformado tira a API do ar (DoS trivial); contas nascem com senha default previsível; dados inválidos entram no banco.
Recommendation: Aplicar RP-11 — validar presença/tipo/formato no início do fluxo (biblioteca de schema ou checks explícitos) respondendo 400 com JSON de erro; tornar `pwd` obrigatório.

### [MEDIUM] Code Duplication & Dead Layers (AP-14)
File: src/AppManager.js:38, 41, 51, 55, 70, 84
Description: O padrão de tratamento de erro `if (err) return res.status(500).send("Erro ...")` é copiado 6 vezes com textos levemente diferentes ("Erro DB", "Erro Matrícula", "Erro Pagamento", "Erro ao criar usuário") em vez de um error handler central; o handler ainda alterna `this.db`/`self.db` (linhas 37/54) para o mesmo objeto, duplicando a referência por causa dos `function(err)` aninhados.
Impact: Manutenção sêxtupla do mesmo comportamento; respostas de erro inconsistentes (text/plain com mensagens divergentes); qualquer padronização exige tocar todos os clones.
Recommendation: Aplicar RP-08 (middleware de erro central com `next(err)`) + RP-14 (deduplicar; arrow functions/async eliminam o `self`).

### [LOW] Poor Naming / Magic Numbers (AP-15)
File: src/AppManager.js:29-33, 46, 68; src/utils.js:19-22
Description: Variáveis de 1-3 letras sem significado: `u`, `e`, `p`, `cid`, `cc` (linhas 29-33), espelhando um contrato de API também abreviado (`usr`, `eml`, `pwd`, `c_id`). Números/strings mágicos: `"4"` como regra de aprovação do gateway (linha 46), `"123456"` como senha default (linha 68), `10000` iterações e `substring(0, 2)`/`substring(0, 10)` sem constantes nomeadas (utils.js:19-22).
Impact: O leitor não infere intenção (`e` é email ou erro?); a regra de negócio central do pagamento está escondida num literal de um caractere.
Recommendation: Aplicar RP-15 — renomear para nomes completos (`user`, `email`, `courseId`, `cardNumber`) e extrair literais para constantes nomeadas no módulo de domínio.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: src/AppManager.js:2; src/utils.js:25
Description: `totalRevenue` é importado em `AppManager.js:2` e nunca usado em lugar nenhum da classe; `utils.js:25` exporta `globalCache` e `totalRevenue` que nenhum outro módulo consome de forma útil (o import existente é morto). São exports/imports de fachada.
Impact: Ruído que sugere funcionalidades (acúmulo de receita, cache compartilhado) que não existem de fato; confunde a leitura e a refatoração.
Recommendation: Aplicar RP-15 — remover imports/exports mortos na refatoração.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: src/AppManager.js:57-61, 92-93, 104-106, 133-135; src/utils.js:13
Description: Erros engolidos e `console.log` como logging de produção: o callback do INSERT em audit_logs (linha 57) ignora `err` e responde 200 mesmo se a auditoria falhar; o DELETE ignora `err` e responde sucesso incondicionalmente (linhas 133-135); no relatório, os `err` dos callbacks internos (linhas 92, 104, 106) nunca são checados — se `db.all` falhar, `enrollments.length` (linha 93) explode com TypeError e derruba o processo. `console.log` é o único mecanismo de log (utils.js:13, AppManager.js:45, app.js:13) — incluindo dado sensível, já escalado para AP-04.
Impact: Falhas silenciosas (auditoria perdida sem sinal, delete "bem-sucedido" que não deletou), caminho de crash escondido no relatório e ausência de logging estruturado para investigar qualquer incidente.
Recommendation: Aplicar RP-08 (propagar erros ao middleware central) + RP-15 (logger estruturado; nunca ignorar `err`).

================================
Total: 21 findings
================================
