================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python + Flask 3.0.0 + Flask-SQLAlchemy 3.1.1 (SQLite)
Files:   15 analyzed | ~1158 lines of code

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 9 | LOW: 6

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:13
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` — a chave de assinatura da aplicação está como literal no código-fonte, versionada no git.
Impact: Qualquer pessoa com acesso ao repositório obtém a chave usada para assinar sessões/cookies; rotacionar exige alterar código e fazer deploy; a chave vaza no histórico do git para sempre.
Recommendation: Aplicar RP-01 — extrair para módulo Config lendo de variável de ambiente (obrigatória, sem default), com `.env.example` documentando a chave. `python-dotenv` já está declarada no requirements.txt e pode finalmente ser usada.

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: services/notification_service.py:7-10
Description: Credenciais SMTP completas hardcoded: `self.email_host = 'smtp.gmail.com'`, `self.email_port = 587`, `self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'` — host+porta+usuário+senha juntos, usados em `server.login(...)` na linha 17.
Impact: Senha de e-mail em texto plano no repositório; qualquer leitor do código pode enviar e-mails como a aplicação. Agrava o fato de o arquivo ser código morto (ver AP-14): o secret está exposto sem sequer haver funcionalidade em produção que o justifique.
Recommendation: Aplicar RP-01 — mover host/porta/usuário/senha para Config via variáveis de ambiente; se o serviço não for conectado ao fluxo real na Fase 3, remover o arquivo (RP-14) e as credenciais junto.

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: seed.py:19, 26, 33
Description: Senhas triviais em texto plano no script de seed: `u1.set_password('1234')` (conta **admin**), `u2.set_password('abcd')`, `u3.set_password('pass')` — todas abaixo até do mínimo de 4 caracteres exigido pela própria API para `pass`... e previsíveis por qualquer dicionário.
Impact: Contas conhecidas (inclusive admin joao@email.com/1234) entram em qualquer ambiente que rode o seed; combinado com MD5 sem salt (AP-04), o hash `81dc9bdb52d04dc20036dbd8313ed055` de "1234" é reconhecível de tabela pública.
Recommendation: Aplicar RP-01 — seeds lendo credenciais de env vars ou gerando senhas aleatórias impressas uma única vez; nunca senhas fixas versionadas.

### [CRITICAL] Weak/Broken Password Hashing & Exposição de Senha (AP-04)
File: models/user.py:29, 32
Description: Hash de senha com MD5 sem salt: `self.password = hashlib.md5(pwd.encode()).hexdigest()` em `set_password` e comparação equivalente em `check_password`.
Impact: MD5 sem salt quebra por rainbow table em segundos (o baseline confirmou: senha "1234" vira o hash público `81dc9bdb52d04dc20036dbd8313ed055`); usuários com a mesma senha têm o mesmo hash, permitindo ataque em massa.
Recommendation: Aplicar RP-04 — `werkzeug.security.generate_password_hash`/`check_password_hash` (salt automático), com re-hash no próximo login bem-sucedido para migrar hashes antigos.

### [CRITICAL] Weak/Broken Password Hashing & Exposição de Senha (AP-04)
File: models/user.py:21; routes/user_routes.py:33, 85-86, 209
Description: `User.to_dict()` inclui `'password': self.password` (models/user.py:21) e é devolvido em três endpoints: `GET /users/<id>` (user_routes.py:33), `POST /users` (user_routes.py:85-86) e no `POST /login` (user_routes.py:209, dentro de `'user': user.to_dict()`). Confirmado no baseline: o login respondeu `"password":"81dc9bdb52d04dc20036dbd8313ed055"`.
Impact: A API entrega o material de ataque de graça — qualquer cliente coleta os hashes MD5 de todos os usuários e os quebra offline; combinado com o MD5 sem salt, equivale a expor as senhas.
Recommendation: Aplicar RP-04 — remover senha/hash do `to_dict()` (serialização segura no Model); nenhuma resposta da API pode conter o campo.

### [CRITICAL] Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth (AP-05)
File: routes/task_routes.py:225-238; routes/user_routes.py:134-151; routes/report_routes.py:211-223
Description: Todos os endpoints destrutivos são públicos, sem qualquer verificação de autenticação/autorização: `DELETE /tasks/<id>`, `DELETE /users/<id>` (que ainda apaga em cascata todas as tasks do usuário, user_routes.py:140-142) e `DELETE /categories/<id>`. Nenhuma rota do projeto verifica token, sessão ou role.
Impact: Qualquer cliente anônimo apaga usuários, tasks e categorias inteiras com uma única requisição HTTP — perda de dados irreversível sem sequer registrar quem foi.
Recommendation: Aplicar RP-12 — proteger as rotas destrutivas com decorator de auth verificável (JWT assinado com a SECRET_KEY vinda da Config) e exigir role adequado; o contrato (método+path) permanece, apenas passa a exigir `Authorization`.

### [HIGH] Missing Authentication / Authorization (AP-06)
File: routes/user_routes.py:210; models/user.py:34-38
Description: O login devolve token falso previsível: `'token': 'fake-jwt-token-' + str(user.id)` — sem assinatura, derivável por qualquer um (`fake-jwt-token-2`, `-3`, ...) e **nunca verificado** em nenhuma rota subsequente. O campo `role` (user/admin/manager) e o método `is_admin()` (models/user.py:34-38) existem, mas nenhuma rota os consulta.
Impact: Autenticação puramente decorativa: qualquer cliente forja o "token" de qualquer usuário; não há nenhuma fronteira de autorização em toda a API (leitura de dados pessoais, escrita e deleção abertas).
Recommendation: Aplicar RP-12 — emitir token assinado (PyJWT com SECRET_KEY da Config) ou token aleatório server-side (`secrets.token_urlsafe`) armazenado e verificado por decorator `@auth_required` nas rotas sensíveis, com checagem de role nas administrativas.

### [HIGH] Business Logic in Controller/Route (AP-07)
File: routes/task_routes.py:11-63, 85-154, 156-223, 273-299; routes/user_routes.py:42-90, 153-183; routes/report_routes.py:12-101
Description: Toda a regra de negócio vive nos handlers HTTP: cálculo de "overdue" inline (task_routes.py:30-39), validação de título/status/prioridade inline (task_routes.py:89-144), serialização manual campo a campo (task_routes.py:17-28), estatísticas e taxa de conclusão (task_routes.py:273-299), e `summary_report` com 90 linhas montando um relatório inteiro dentro da rota (report_routes.py:12-101). Handlers com 50-90+ linhas misturando parsing, validação, ORM e formatação.
Impact: Viola MVC/SRP — a regra de negócio não é testável sem subir HTTP; a duplicação entre rotas já aconteceu (ver AP-14); qualquer mudança de regra exige editar múltiplos handlers.
Recommendation: Aplicar RP-05 (mover regras para Models/serviços de domínio) e RP-03 (rotas finas → controllers → models), aproveitando os métodos já existentes e ignorados como `Task.is_overdue()`.

### [HIGH] Global Mutable State (AP-08)
File: services/notification_service.py:6, 31-36, 43-48
Description: `NotificationService` acumula notificações em lista em memória (`self.notifications = []`, `append` em notify_task_assigned) e as consulta de lá (`get_notifications`) — estado de negócio que deveria estar no banco, crescendo sem limite e por processo.
Impact: Se a camada for conectada ao fluxo real, é memory leak e dado inconsistente entre workers/restarts (notificações "somem"); o padrão precisa ser corrigido antes de a camada ser absorvida na Fase 3.
Recommendation: Aplicar RP-06 — persistir notificações no banco (model próprio) e derivar consultas de lá; nenhum estado de negócio em atributos/variáveis de módulo.

### [HIGH] Missing Transaction / Non-atomic Writes (AP-09)
File: seed.py:11-14, 37, 63, 92
Description: O seed apaga as três tabelas e commita (linhas 11-14) e depois insere usuários, categorias e tasks com `commit()` separado por bloco (linhas 37, 63, 92) — quatro transações independentes para um fluxo que só faz sentido completo.
Impact: Falha no meio (ex.: violação de unique) deixa o banco em estado inconsistente: tabelas já esvaziadas e apenas parte dos dados repovoada, sem rollback do conjunto.
Recommendation: Aplicar RP-07 — acumular todas as escritas na `db.session` e commitar uma única vez ao final, com `rollback()` no except.

### [HIGH] Insecure Config em Produção (AP-10)
File: app.py:15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` (app.py:34) — debugger interativo do Werkzeug exposto em todas as interfaces — e `CORS(app)` sem restrição de origins (app.py:15) em uma API que manipula usuários e senhas. Porta 5000 hardcoded (no macOS colide com o AirPlay Receiver, como visto no baseline).
Impact: `debug=True` + bind em 0.0.0.0 = execução remota de código via console do Werkzeug para qualquer host da rede; CORS aberto permite abuso cross-site; porta fixa impede configurar por ambiente.
Recommendation: Aplicar RP-01 (debug/host/porta/origins via Config e env vars, default seguro `debug=False`) e RP-08 (respostas de erro padronizadas sem stack trace).

### [MEDIUM] N+1 Query (AP-11)
File: routes/task_routes.py:41-57
Description: `GET /tasks` itera `Task.query.all()` e, por task, executa `User.query.get(t.user_id)` (linha 42) e `Category.query.get(t.category_id)` (linha 51) para obter `user_name`/`category_name` — 1 + 2N queries por requisição.
Impact: Latência cresce linearmente com o número de tasks (com 1000 tasks são ~2001 queries); derruba o banco sob carga em um endpoint de listagem básico.
Recommendation: Aplicar RP-09 — eager loading (`selectinload(Task.user)`, `selectinload(Task.category)` — os relationships já existem em models/task.py:20-21) reduzindo a 2-3 queries fixas.

### [MEDIUM] N+1 Query (AP-11)
File: routes/report_routes.py:53-68, 163; routes/user_routes.py:22
Description: `GET /reports/summary` faz `Task.query.filter_by(user_id=u.id).all()` dentro do loop de usuários (report_routes.py:56); `GET /categories` faz `Task.query.filter_by(category_id=c.id).count()` por categoria (report_routes.py:163); `GET /users` dispara lazy load de `u.tasks` por usuário via `len(u.tasks)` (user_routes.py:22).
Impact: Cada relatório/listagem executa 1 + N queries (ou mais); `/reports/summary` ainda soma ~10 `count()` separados (linhas 15-28) que poderiam ser um único GROUP BY.
Recommendation: Aplicar RP-09 — agregações com `func.count` + `group_by` no Model e eager loading nos relacionamentos.

### [MEDIUM] N+1 Query (AP-11)
File: routes/task_routes.py:14, 266, 281; routes/user_routes.py:12; routes/report_routes.py:30, 53
Description: Nenhuma listagem tem paginação: `Task.query.all()` em `GET /tasks`, `/tasks/search` e `/tasks/stats`, `User.query.all()` em `GET /users` e nos relatórios — a tabela inteira é carregada e serializada a cada requisição.
Impact: Consumo de memória e latência crescem sem limite com o volume de dados; junto com os N+1 acima, um único GET pode varrer o banco todo. O próprio seed reconhece o problema ("Adicionar paginação na API", seed.py:70).
Recommendation: Aplicar RP-09 — paginação nos Models (`limit/offset` ou `db.paginate`) com parâmetros `page`/`per_page` validados nas rotas.

### [MEDIUM] Deprecated API Usage (AP-12)
File: models/user.py:14; models/task.py:15, 16, 52; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; seed.py:66, 67, 69, 70, 74; services/notification_service.py:35; utils/helpers.py:38
Description: **22 usos de `datetime.utcnow()`** (deprecated desde Python 3.12 — retorna datetime naive). Inclui os `default=datetime.utcnow` das colunas dos três models (com `onupdate` em models/task.py:16). Evidência viva: rodar `python seed.py` no baseline emitiu `DeprecationWarning: datetime.datetime.utcnow() is deprecated...`.
Impact: Quebra em upgrade futuro do Python; datetimes naive causam bugs silenciosos de timezone em toda comparação de `due_date`/`created_at` (o "overdue" da API depende disso).
Recommendation: Aplicar RP-10 — substituir todas as ocorrências por `datetime.now(timezone.utc)`; em colunas, `default=lambda: datetime.now(timezone.utc)`.

### [MEDIUM] Deprecated API Usage (AP-12)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213
Description: **16 usos de `Model.query.get(id)`** (API legacy `Query.get()`, removida no estilo SQLAlchemy 2.x) — ex.: `Task.query.get(task_id)` (task_routes.py:67), `User.query.get(user_id)` (user_routes.py:29). Todo o restante do acesso a dados também usa a API legacy `Model.query.filter/filter_by/all/count` em vez do estilo 2.0.
Impact: SQLAlchemy 2.x emite `LegacyAPIWarning` e o padrão está a um upgrade de quebrar; mantém o código preso ao estilo 1.x.
Recommendation: Aplicar RP-10 — `db.session.get(Model, id)` para os 16 casos; migrar consultas para `db.session.execute(select(Model).where(...))` nos Models durante a Fase 3.

### [MEDIUM] Missing Input Validation (AP-13)
File: routes/task_routes.py:113, 182, 261, 264; routes/report_routes.py:196-197; routes/user_routes.py:61, 106, 125
Description: Comparações e conversões sobre input não validado: `if priority < 1` com `priority` vindo do JSON sem checagem de tipo (task_routes.py:113 e 182 — enviar `"priority": "alta"` gera TypeError → 500); `int(priority)`/`int(user_id)` sobre query string sem tratamento (task_routes.py:261, 264 — `?priority=abc` → ValueError → 500); `update_category` acessa `data['name']` sem verificar se `get_json()` retornou None (report_routes.py:196-197 → TypeError → 500); regex de e-mail fraco que aceita `a@b` sem TLD (user_routes.py:61, 106); `user.active = data['active']` aceita qualquer tipo (user_routes.py:125).
Impact: Payloads malformados derrubam handlers com 500 genérico em vez de 400 com mensagem clara; dados inválidos entram no banco.
Recommendation: Aplicar RP-11 — validadores centralizados por domínio (presença + tipo + faixa) chamados pelos controllers; `marshmallow` já está declarada no requirements.txt e poderia ser usada.

### [MEDIUM] Code Duplication & Dead Layers (AP-14)
File: services/notification_service.py:1-48; services/__init__.py:1
Description: A camada `services/` inteira é código morto de fachada: busca global confirma que `NotificationService` não é importado por nenhum arquivo do projeto — nenhuma rota envia notificação. O diretório existe apenas para aparentar arquitetura em camadas.
Impact: Falsa impressão de organização; carrega credenciais SMTP reais (AP-01) e estado global (AP-08) sem entregar funcionalidade; confunde manutenção ("onde ligo a notificação?").
Recommendation: Aplicar RP-14 — na Fase 3, ou conectar o serviço ao fluxo real (via Config e injeção no composition root) ou removê-lo, registrando a remoção.

### [MEDIUM] Code Duplication & Dead Layers (AP-14)
File: utils/helpers.py:9-116; routes/report_routes.py:7
Description: `utils/helpers.py` duplica regras que vivem inline nas rotas e não é usado: `validate_email` (helpers:19-23) duplica o regex de user_routes.py:61 e 106; `process_task_data` (helpers:57-108) duplica toda a validação de task de task_routes.py:89-144 e 166-213; `parse_date` (helpers:43-50) duplica o `strptime` de task_routes.py:136 e 203; as constantes `VALID_STATUSES`/`VALID_ROLES`/`MIN_TITLE_LENGTH` (helpers:110-116) duplicam as listas/números literais das rotas. O único import real (`format_date, calculate_percentage` em report_routes.py:7) é morto — nenhuma das duas funções é chamada no arquivo.
Impact: Duas implementações da mesma regra divergem garantidamente (a das rotas não faz `strip()` do título; a do helpers aceita `dd/mm/YYYY` extra); correções aplicadas em só um dos clones.
Recommendation: Aplicar RP-14 — eleger a implementação canônica (validadores/constantes), conectá-la ao fluxo real via controllers e remover os clones.

### [MEDIUM] Code Duplication & Dead Layers (AP-14)
File: routes/task_routes.py:17-28, 30-39, 71-80, 283-287; routes/user_routes.py:171-180; routes/report_routes.py:33-43, 132-135; models/task.py:50-60
Description: O cálculo de "overdue" (`due_date < utcnow` + status ≠ done/cancelled) está copiado **6 vezes** nas rotas, enquanto `Task.is_overdue()` (models/task.py:50-60) implementa exatamente essa regra e **nunca é chamado**. A serialização de task também é duplicada: `to_dict()` existe no model e task_routes.py:17-28 remonta o mesmo dict campo a campo.
Impact: Regra de negócio central mantida em 7 lugares; qualquer ajuste (ex.: considerar timezone) precisa ser replicado em todos — e o model já divergiu das rotas (rotas adicionam `overdue` ao dict, model não).
Recommendation: Aplicar RP-14 — usar `Task.is_overdue()`/`to_dict()` como implementação única (corrigindo o utcnow via RP-10) e remover as cópias inline.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: routes/task_routes.py:62, 137, 204, 236; routes/user_routes.py:130, 149; routes/report_routes.py:186, 207, 221; utils/helpers.py:46, 49, 88
Description: **12 `except:` nus** — capturam inclusive `KeyboardInterrupt`/`SystemExit` e escondem a causa raiz; em task_routes.py:62 o except nu engole qualquer erro do `GET /tasks` e devolve `{'error': 'Erro interno'}` sem log algum.
Impact: Debugging às cegas (erros silenciados), comportamento incorreto mascarado como "Erro interno", e handlers try/except duplicados por rota.
Recommendation: Aplicar RP-08 — error handler central com exceções tipadas e logging real; nos casos pontuais (parse de data), capturar `ValueError` específico.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: requirements.txt:4-6
Description: Três dependências declaradas e nunca importadas em nenhum arquivo do projeto (busca global): `marshmallow==3.20.1`, `requests==2.31.0`, `python-dotenv==1.0.0`.
Impact: Deploy inchado, superfície de vulnerabilidade desnecessária e sinal enganoso (sugere validação por schema e config por .env que não existem).
Recommendation: Aplicar RP-15 — remover do manifesto, ou passar a usá-las de verdade na Fase 3 (dotenv na Config/RP-01, marshmallow na validação/RP-11).

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: app.py:7; routes/task_routes.py:7; routes/user_routes.py:6; routes/report_routes.py:7-8; models/task.py:3
Description: Imports mortos espalhados: `os, sys, json` em app.py:7 (só `datetime` é usado); `json, os, sys, time` em task_routes.py:7 (nenhum usado); `hashlib, json` em user_routes.py:6 (só `re` é usado); `json` em report_routes.py:8 e models/task.py:3; além do import morto `format_date, calculate_percentage` (report_routes.py:7, nunca chamados).
Impact: Ruído que sugere dependências inexistentes (hashlib na rota insinua hashing local) e polui a leitura.
Recommendation: Aplicar RP-15 — remover todos os imports não usados (lint com ruff/flake8 F401 na Fase 3).

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: routes/task_routes.py:149, 153, 219, 234; routes/user_routes.py:83, 89, 147; services/notification_service.py:21, 24; utils/helpers.py:39-41; seed.py:93-96
Description: `print()` usado como logging de produção nos handlers e serviços (ex.: `print(f"Task criada: {task.id}...")`, `print(f"ERRO: {str(e)}")`), sem níveis, timestamps ou destino configurável.
Impact: Logs se perdem conforme o servidor WSGI, não há severidade/estrutura para diagnóstico, e mensagens de erro internas ficam fora de qualquer observabilidade.
Recommendation: Aplicar RP-08/RP-15 — `logging.getLogger(__name__)` com handler configurado no composition root; prints de erro migram para `logger.exception`.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: app.py:30-31
Description: `with app.app_context(): db.create_all()` executado no nível do módulo — o schema do banco é criado/alterado como efeito colateral de qualquer import de `app.py` (inclusive pelo `seed.py:2` e por futuros testes).
Impact: Importar o módulo muta o banco; impede gerenciar schema por migrações (Alembic) e cria surpresas em ambientes onde o import acontece antes da configuração correta.
Recommendation: Aplicar RP-03 — mover a criação de schema para o composition root/factory (`create_app()`) ou comando CLI explícito (`flask db upgrade`/script de bootstrap).

### [LOW] Poor Naming / Magic Numbers (AP-15)
File: routes/report_routes.py:24-28, 160-161; routes/user_routes.py:14; routes/task_routes.py:16, 96-100, 113; routes/user_routes.py:64, 115; models/task.py:45-48
Description: Variáveis de 1-2 letras fora de índice de loop (`u`, `t`, `c`, `p1`..`p5` em report_routes.py:24-28) e números mágicos repetidos sem constante: limites de título 3/200 (task_routes.py:96-100), prioridade 1..5 (task_routes.py:113; models/task.py:46), senha mínima 4 (user_routes.py:64, 115), cor default `'#000000'` (report_routes.py:180; models/category.py:10). As constantes nomeadas existem em utils/helpers.py:110-116 — e não são usadas (ver AP-14).
Impact: Intenção ilegível (`p4` é prioridade "low"? "minimal"?); limites alterados em um ponto e não no outro divergem silenciosamente.
Recommendation: Aplicar RP-15 — nomes descritivos e constantes únicas por domínio (aproveitando as já definidas em helpers ao absorver a camada via RP-14).

================================
Total: 26 findings
================================
