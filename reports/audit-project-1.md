================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1 (SQLite via sqlite3, SQL cru)
Files:   4 analyzed | ~780 lines of code (app.py 88, controllers.py 292, models.py 314, database.py 86)

## Summary
CRITICAL: 11 | HIGH: 7 | MEDIUM: 7 | LOW: 4

## Findings

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:7
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — chave de assinatura de sessão como literal no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório (ou ao histórico do git) obtém a chave que assina sessões; rotacionar exige alterar código e redeploy.
Recommendation: Aplicar RP-01 — extrair para `config/settings.py` lendo `os.environ["SECRET_KEY"]` (obrigatória, falha no boot se ausente) e documentar em `.env.example`.

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: controllers.py:285-289
Description: `GET /health` devolve no JSON `"db_path": "loja.db"`, `"debug": True` e `"secret_key": "minha-chave-super-secreta-123"` — o endpoint expõe a SECRET_KEY publicamente e sem autenticação.
Impact: Vazamento da chave de assinatura via HTTP para qualquer cliente anônimo; entrega o material de ataque de graça, além de revelar caminho do banco e modo debug.
Recommendation: Aplicar RP-01 — `/health` deve devolver apenas `{"status": "ok"}` (ou contadores não sensíveis); nunca secrets/config interna. (Mudança de comportamento registrada no baseline.)

### [CRITICAL] SQL Injection (AP-02)
File: models.py:28, 47-50, 57-61, 68, 92, 126-129, 140, 148-151, 155, 157-161, 163-166, 174, 188, 192, 220, 224, 279-281
Description: Praticamente TODAS as queries são montadas por concatenação de strings com input do usuário, sem placeholders. Ex.: `cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))` (linha 28); `INSERT INTO produtos (...) VALUES ('" + nome + "', ...")` (47-50); `UPDATE pedidos SET status = '" + novo_status + "' WHERE id = " + str(pedido_id)` (279-281). Nenhuma usa o placeholder `?` do sqlite3.
Impact: Um parâmetro malicioso (`' OR '1'='1`, `'; DROP TABLE produtos; --`) lê/altera/apaga qualquer dado do banco. Superfície de ataque em todo o CRUD de produtos, usuários e pedidos.
Recommendation: Aplicar RP-02 — parametrizar 100% das queries com `cursor.execute("... WHERE id = ?", (id,))`; as queries parametrizadas ficam nos Models por domínio.

### [CRITICAL] SQL Injection (AP-02)
File: models.py:105-111
Description: `login_usuario` monta `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` com input bruto do formulário de login.
Impact: Bypass de autenticação trivial — enviar email `admin@loja.com'--` ou senha `' OR '1'='1` autentica como qualquer usuário sem conhecer a senha. É a rota mais crítica do sistema.
Recommendation: Aplicar RP-02 (parametrizar) em conjunto com RP-04 (hash de senha) — a verificação passa a comparar hash com placeholders parametrizados.

### [CRITICAL] SQL Injection (AP-02)
File: models.py:289-297
Description: `buscar_produtos` concatena o termo de busca dentro de um LIKE: `query += " AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"`, e também `categoria`, `preco_min`, `preco_max` por concatenação.
Impact: `GET /produtos/busca?q=...` fica injetável via query string; o `%` do LIKE no meio do SQL agrava (permite fechar a string e emendar SQL).
Recommendation: Aplicar RP-02 — usar `LIKE ?` com o `%` no parâmetro (`(f"%{termo}%",)`), montando a cláusula com placeholders.

### [CRITICAL] God Class / God Module / God Method (AP-03)
File: models.py:1-314
Description: `models.py` (314 linhas) concentra acesso a dados (SQL cru), regra de negócio (cálculo de desconto/faturamento em 256-273), orquestração de pedido com baixa de estoque (133-169) e serialização de resposta (dicts em 12-21, 31-40, 79-86, 95-102, 304-313) para 4 domínios (produtos, usuários, pedidos, itens). Não há separação de camadas — `app.py` só registra rotas, `controllers.py` só faz parsing/try-except.
Impact: Viola completamente a separação de responsabilidades do MVC; impossível testar regra de negócio em isolamento; qualquer mudança em um domínio arrisca os outros.
Recommendation: Aplicar RP-03 (+ RP-13/estrutura) — quebrar em `models/` por domínio (produto, usuario, pedido) recebendo a conexão, `controllers/` orquestrando e `views/routes.py` finas.

### [CRITICAL] God Class / God Module / God Method (AP-03)
File: models.py:133-169
Description: `criar_pedido` é um God Method de ~37 linhas que faz validação de estoque, cálculo de total (regra de negócio), INSERT em `pedidos`, loop de INSERT em `itens_pedido` e UPDATE de estoque — tudo inline, com dois loops sobre `itens` e query dentro de loop.
Impact: Método impossível de testar unitariamente sem banco; mistura validação, cálculo, persistência e efeito em estoque; concentra também AP-02, AP-09 e AP-11.
Recommendation: Aplicar RP-03 + RP-05 — extrair `calcular_total`/regra de domínio, mover persistência para `PedidoModel.criar_com_itens` transacional.

### [CRITICAL] Weak/Broken Password Hashing & Exposição de Senha (AP-04)
File: database.py:76-78, models.py:126-129, 109-111
Description: Senhas armazenadas em TEXTO PLANO — seed insere `("Admin","admin@loja.com","admin123","admin")` etc. (database.py:76-78), `criar_usuario` grava `senha` sem hashing (models.py:126-129) e o login compara texto plano diretamente no SQL (models.py:109-111). Nenhum algoritmo de hash é usado.
Impact: Vazamento do banco expõe todas as senhas reais imediatamente; usuários que reusam senha ficam comprometidos em outros serviços.
Recommendation: Aplicar RP-04 — hash com `werkzeug.security.generate_password_hash`/`check_password_hash` (salt embutido); nunca armazenar/comparar texto plano.

### [CRITICAL] Weak/Broken Password Hashing & Exposição de Senha (AP-04)
File: models.py:83, 99
Description: `get_todos_usuarios` e `get_usuario_por_id` incluem o campo `"senha": row["senha"]` no dict serializado, então `GET /usuarios` e `GET /usuarios/<id>` devolvem a senha de todos os usuários no JSON de resposta (verificado no baseline: `"senha":"admin123"` etc.).
Impact: Qualquer cliente anônimo lê todas as senhas via API; combinado com o armazenamento em texto plano (finding acima), é vazamento total de credenciais por um GET.
Recommendation: Aplicar RP-04 — `to_dict()` do usuário jamais inclui `senha`/hash; expor apenas `{id, nome, email, tipo}`. (Mudança de comportamento registrada no baseline.)

### [CRITICAL] Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth (AP-05)
File: app.py:59-78
Description: `POST /admin/query` executa SQL arbitrário vindo do body: `query = dados.get("sql", "")` seguido de `cursor.execute(query)`, com commit para não-SELECT. Sem qualquer autenticação.
Impact: Qualquer cliente anônimo executa `DROP TABLE`, exfiltra dados ou altera qualquer registro com uma única requisição — comprometimento total do banco.
Recommendation: Aplicar RP-12 — REMOVER o endpoint (nenhuma refatoração torna SQL arbitrário via HTTP aceitável); consultas ad-hoc pertencem a ferramentas de DB. Registrar a remoção na Fase 3.

### [CRITICAL] Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth (AP-05)
File: app.py:47-57
Description: `POST /admin/reset-db` executa `DELETE FROM itens_pedido/pedidos/produtos/usuarios` e commita, apagando o banco inteiro. Sem autenticação nenhuma.
Impact: Qualquer cliente anônimo destrói todos os dados da aplicação com um POST.
Recommendation: Aplicar RP-12 — remover ou colocar atrás de auth real (`@auth_required` com token verificável); se mantido, restringir a admin autenticado.

### [HIGH] Missing Authentication / Authorization (AP-06)
File: controllers.py:167-186, app.py:11-30, 47-59
Description: O `login` responde sucesso devolvendo os dados do usuário mas NÃO cria token/sessão verificável (controllers.py:167-186) — não há material de autenticação. Nenhuma rota exige auth: escrita/atualização/exclusão de produtos, criação de pedidos, listagem de usuários (com senha) e as rotas `/admin/*` estão todas abertas.
Impact: Qualquer usuário anônimo cria/edita/deleta recursos e lê dados pessoais de terceiros; não há noção de identidade autenticada em nenhum handler.
Recommendation: Aplicar RP-12 — emitir token verificável no login (JWT assinado com a SECRET_KEY, ou `secrets.token_urlsafe` server-side) e proteger rotas sensíveis com middleware `auth_required`.

### [HIGH] Business Logic in Controller/Route (AP-07)
File: controllers.py:208-210
Description: O handler `criar_pedido` dispara efeitos colaterais inline após a criação: `print("ENVIANDO EMAIL ...")`, `print("ENVIANDO SMS ...")`, `print("ENVIANDO PUSH ...")` — notificações modeladas como print dentro da rota HTTP.
Impact: Regra/efeito de negócio acoplado ao handler; não testável sem HTTP; impossível reusar ou trocar o canal de notificação; viola MVC/SRP.
Recommendation: Aplicar RP-05 — mover para um colaborador `notificador` injetado pelo composition root, chamado pelo controller de domínio; substituir `print` por logging (RP-15).

### [HIGH] Business Logic in Controller/Route (AP-07)
File: controllers.py:247-250
Description: `atualizar_status_pedido` embute regra de negócio no handler: `if novo_status == "aprovado": print("... Preparar envio.")` e `if novo_status == "cancelado": print("... Devolver estoque.")` — inclusive uma ação de negócio prometida (devolver estoque) que na prática não acontece.
Impact: Lógica de transição de estado dispersa na rota; comportamento (devolução de estoque) descrito mas não implementado; não testável isoladamente.
Recommendation: Aplicar RP-05 — transição de status e seus efeitos (notificação, devolução de estoque) no `PedidoModel`; controller apenas orquestra.

### [HIGH] Global Mutable State (AP-08)
File: database.py:4, 9-10
Description: Conexão SQLite singleton em variável de módulo: `db_connection = None` (linha 4), criada uma vez com `sqlite3.connect(db_path, check_same_thread=False)` (linha 10) e reutilizada por todas as requisições e threads.
Impact: `check_same_thread=False` + conexão global compartilhada gera condições de corrida entre requisições concorrentes (cursores/transações se misturam), dados inconsistentes e impossibilidade de escalar; um erro não revertido contamina requisições seguintes.
Recommendation: Aplicar RP-06 — conexão por request via `flask.g` + `teardown_appcontext`, injetada nos models pelo composition root.

### [HIGH] Missing Transaction / Non-atomic Writes (AP-09)
File: models.py:133-169
Description: `criar_pedido` faz INSERT em `pedidos`, N INSERTs em `itens_pedido` e N UPDATEs de estoque com um único `db.commit()` no fim (linha 168), sem `try/except`+`rollback` e sem transação explícita. Um erro no meio do loop deixa a conexão global com estado sujo (a próxima chamada pode commitar escritas parciais) e não há reversão da baixa de estoque já aplicada.
Impact: Falha no meio do fluxo pode deixar pedido/itens/estoque inconsistentes; sem rollback, a conexão singleton propaga o estado sujo para outras requisições.
Recommendation: Aplicar RP-07 — envolver o conjunto em transação (`try: ... db.commit() except: db.rollback(); raise`) dentro do `PedidoModel`.

### [HIGH] Insecure Config em Produção (AP-10)
File: app.py:8, 88
Description: `app.config["DEBUG"] = True` (linha 8) e `app.run(host="0.0.0.0", port=5000, debug=True)` (linha 88) — debugger interativo do Werkzeug habilitado e bind em todas as interfaces. O `/health` ainda anuncia `"ambiente": "producao"`.
Impact: `debug=True` expõe o console interativo do Werkzeug = execução remota de código em caso de exceção; `0.0.0.0` expõe o serviço em toda a rede. Combinação crítica em produção.
Recommendation: Aplicar RP-01/RP-08 — `DEBUG` via env var (default `0`), nunca `debug=True` fixo; bind controlado por config; error handling central em vez do debugger.

### [HIGH] Insecure Config em Produção (AP-10)
File: app.py:9
Description: `CORS(app)` habilita CORS para todas as origens (`Access-Control-Allow-Origin: *`) sem restrição, numa API que manipula dados de usuários/pedidos.
Impact: Qualquer site pode chamar a API a partir do navegador da vítima; combinado com ausência de auth, permite abuso cross-site.
Recommendation: Aplicar RP-08 — restringir CORS a origens conhecidas via config (`CORS(app, origins=[...])`).

### [MEDIUM] N+1 Query (AP-11)
File: models.py:171-201
Description: `get_pedidos_usuario` executa 1 query de pedidos e, para cada pedido, uma query de itens (linha 188) e, para cada item, uma query do nome do produto (linha 192) — padrão 1 + N + (N·M) usando `cursor2`/`cursor3` dentro de loops.
Impact: Latência cresce linearmente com pedidos e itens; sob carga derruba o banco; agravado pela conexão global compartilhada.
Recommendation: Aplicar RP-09 — consolidar com JOIN (`pedidos LEFT JOIN itens_pedido JOIN produtos`) e agrupar em memória; a query fica no `PedidoModel`.

### [MEDIUM] N+1 Query (AP-11)
File: models.py:203-233
Description: `get_todos_pedidos` repete exatamente o mesmo padrão N+1 de `get_pedidos_usuario` (query de itens por pedido em 220, query de nome de produto por item em 224).
Impact: Mesmo problema de performance, agora sobre TODOS os pedidos do sistema (`GET /pedidos`) — pior escala.
Recommendation: Aplicar RP-09 (JOIN) — e RP-14 para eliminar a duplicação com o finding acima.

### [MEDIUM] Missing Input Validation (AP-13)
File: controllers.py:118-121
Description: `buscar_produtos` faz `preco_min = float(preco_min)` / `preco_max = float(preco_max)` sobre valores da query string sem validação — `?preco_min=abc` lança `ValueError` que vira 500 genérico em vez de 400.
Impact: Requisição malformada derruba o handler com 500 e vaza `str(e)` no corpo; sem mensagem clara de erro para o cliente.
Recommendation: Aplicar RP-11 — validar/parsear com tratamento (`try` ou checagem), respondendo 400 com mensagem clara.

### [MEDIUM] Missing Input Validation (AP-13)
File: controllers.py:37-46, 81-90
Description: `criar_produto`/`atualizar_produto` checam presença das chaves mas usam `preco`/`estoque` sem validar tipo: `if preco < 0` (linha 43) quebra com `TypeError` se `preco` vier como string, e valores são concatenados direto no SQL (models). Não há `isinstance`.
Impact: Payloads com tipo errado geram 500 em vez de 400; strings entram no SQL cru (reforça AP-02).
Recommendation: Aplicar RP-11 — validador de domínio checando presença + tipo + faixa antes de persistir, retornando 400.

### [MEDIUM] Missing Input Validation (AP-13)
File: controllers.py:195-203, models.py:139-140, 144
Description: `criar_pedido` não valida a estrutura de `itens`: cada item é acessado como `item["produto_id"]` e `item["quantidade"]` em models.py (139-140, 144) sem checar presença/tipo — item sem essas chaves gera `KeyError` → 500; `quantidade` negativa/zero não é barrada.
Impact: Payload de pedido malformado derruba o handler (500) e permite quantidades inválidas entrarem no cálculo/estoque.
Recommendation: Aplicar RP-11 — validar cada item (presença de `produto_id`/`quantidade`, tipos numéricos, `quantidade > 0`) no controller/validador de domínio.

### [MEDIUM] Code Duplication & Dead Layers (AP-14)
File: models.py:171-201, 203-233
Description: `get_pedidos_usuario` e `get_todos_pedidos` são blocos quase idênticos (montagem do dict de pedido + loops N+1 de itens e produto), diferindo só pelo `WHERE usuario_id`.
Impact: Manutenção dupla — uma correção (ex.: o fix de N+1) precisa ser aplicada em dois lugares e tende a divergir.
Recommendation: Aplicar RP-14 — extrair um único método de leitura de pedidos parametrizado por filtro, usado por ambas as rotas.

### [MEDIUM] Code Duplication & Dead Layers (AP-14)
File: models.py:12-21, 31-40, 304-313; controllers.py:28-54, 72-90
Description: Serialização de produto repetida em 3 pontos (get_todos_produtos, get_produto_por_id, buscar_produtos) e de usuário em 2; os blocos de validação de produto em `criar_produto` (28-54) e `atualizar_produto` (72-90) são praticamente copiados; o par `except Exception as e: return jsonify({"erro": str(e)}), 500` repete-se em quase todos os handlers de `controllers.py`.
Impact: Divergência garantida entre clones; validação e serialização inconsistentes ao longo do tempo; ruído.
Recommendation: Aplicar RP-14 + RP-08 — serializers/validators únicos por domínio e error handling central em middleware (elimina os try/except duplicados).

### [LOW] Poor Naming / Magic Numbers (AP-15)
File: models.py:256-262
Description: Regra de desconto do relatório usa números mágicos sem constante nomeada: `if faturamento > 10000: desconto = faturamento * 0.1 elif faturamento > 5000: ... * 0.05 elif faturamento > 1000: ... * 0.02`.
Impact: Intenção obscura (faixas e percentuais de desconto) e risco de alterar um número e não os relacionados.
Recommendation: Aplicar RP-15 — constantes nomeadas (`LIMITE_DESCONTO_*`, `PERCENTUAL_*`) no Model do domínio.

### [LOW] Poor Naming / Magic Numbers (AP-15)
File: controllers.py:14, 47-50; models.py:24, 187, 191, 219, 223
Description: `id` (builtin do Python) usado como nome de parâmetro em vários handlers/funções; `cursor2`/`cursor3` como nomes de cursores dentro dos loops N+1 (models.py:187-224); limites de tamanho de nome como literais soltos `2` e `200` (controllers.py:47-50).
Impact: Sombreamento de builtin e nomes que não revelam intenção dificultam leitura e manutenção.
Recommendation: Aplicar RP-15 — renomear `id`→`produto_id`/`usuario_id`, cursores descritivos, extrair `NOME_MIN`/`NOME_MAX`.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: models.py:2
Description: `import sqlite3` em `models.py` nunca é usado — a conexão vem de `get_db()` (database.py); import morto.
Impact: Ruído que sugere dependência inexistente; confunde a leitura.
Recommendation: Aplicar RP-15 — remover o import não utilizado.

### [LOW] Dead Code / Bad Hygiene (AP-16)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248-250; app.py:56, 83-86
Description: `print()` usado como logging de produção em todo o projeto (ex.: `print("Listando " + str(len(produtos)) + " produtos")`, `print("Login bem-sucedido: " + email)`, `print("!!! BANCO DE DADOS RESETADO !!!")`), inclusive logando email de usuário e eventos de auth.
Impact: Sem níveis/estrutura/timestamps; polui stdout; dados de usuário em log não estruturado; impossível filtrar/silenciar em produção.
Recommendation: Aplicar RP-15/RP-08 — trocar por `logging` estruturado e centralizar o log de erros no middleware de erro.

================================
Total: 29 findings
================================

---

## Nota — AP-12 (Deprecated API Usage — seção obrigatória)

Varredura por APIs obsoletas das tabelas do catálogo (`datetime.utcnow()`, `datetime.utcfromtimestamp()`, `Model.query.get()`, `Query.filter()`, `@app.before_first_request`) e equivalentes Node: **0 ocorrências**. O projeto não usa `datetime`, não usa ORM (SQLite acessado via `sqlite3` cru) e não usa `before_first_request`. Portanto AP-12 não gera finding neste projeto. Observação relacionada, já coberta por AP-08: a conexão usa `check_same_thread=False` num singleton global — não é API deprecated, mas é config insegura de concorrência.
