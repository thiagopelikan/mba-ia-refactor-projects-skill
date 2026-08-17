# Catálogo de Anti-patterns (Fase 2)

16 anti-patterns com ID citável, severidade, sinais de detecção acionáveis e stacks aplicáveis. Na auditoria, cruze **cada arquivo-fonte** contra **todas** as entradas. Cite sempre o ID (ex.: `AP-02`) e o nome no finding, com arquivo:linha exatos.

Escala de severidade (usar literalmente): **CRITICAL** (falha grave de segurança/arquitetura), **HIGH** (forte violação MVC/SOLID), **MEDIUM** (padronização, performance moderada, validação), **LOW** (legibilidade, nomenclatura, código morto).

Distribuição: 5 CRITICAL · 5 HIGH · 4 MEDIUM · 2 LOW.

---

## AP-01 — Hardcoded Credentials / Secrets

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - `SECRET_KEY = "..."`, `password = "..."`, `API_KEY = "..."` como literais no código;
  - chaves com prefixo de produção: `pk_live_`, `sk_live_`;
  - credenciais SMTP literais (`smtp_user =`, `smtp_password =`, host+porta+senha juntos);
  - senhas em texto plano em scripts de seed (`INSERT INTO usuarios ... '123456'`);
  - secrets expostos em endpoints (ex.: `/health` devolvendo a `SECRET_KEY` no JSON).
- **Por que é problema:** qualquer pessoa com acesso ao repositório (ou ao endpoint) obtém credenciais reais; rotacionar exige deploy; vaza em logs e histórico do git.
- **Stacks aplicáveis:** todas (Python, Node, etc.).

## AP-02 — SQL Injection

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - query SQL montada por concatenação ou interpolação com input do usuário: `"... WHERE id = " + str(id)`, `f"SELECT ... WHERE nome LIKE '%{termo}%'"`, template literal `` `... WHERE email = '${email}'` `` em Node;
  - ausência de placeholders (`?` no sqlite3, `%s`/`:param` em outros drivers) em queries que recebem variáveis;
  - `cursor.execute(query)` onde `query` foi construída com `+` ou f-string.
- **Por que é problema:** permite ler/alterar/apagar qualquer dado do banco com um parâmetro malicioso (`' OR '1'='1`, `; DROP TABLE ...`).
- **Stacks aplicáveis:** qualquer stack com SQL cru (Python `sqlite3`, Node `sqlite3`/`pg`). Em projetos com ORM, procure também `text()`/`raw` interpolados.

## AP-03 — God Class / God Module / God Method

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - um único arquivo/classe concentra conexão com DB + regra de negócio + roteamento + serialização + integração externa (email, pagamento);
  - arquivo > ~250 linhas cobrindo múltiplos domínios (ex.: `models.py` com produtos, usuários, pedidos E validação E formatação);
  - método/função > ~50 linhas ou com aninhamento > 3 níveis (inclui callback hell de 4-5 níveis em Node);
  - classe "gerente de tudo" (ex.: `AppManager`) instanciada uma vez e usada por todas as rotas.
- **Por que é problema:** viola completamente a separação de responsabilidades; impossível testar em isolamento; qualquer mudança afeta tudo.
- **Stacks aplicáveis:** todas.

## AP-04 — Weak/Broken Password Hashing & Exposição de Senha

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - `hashlib.md5(senha)`, `sha1(...)` **sem salt**; hash caseiro reversível (ex.: função `badCrypto` fazendo XOR/base64);
  - senha armazenada em texto plano;
  - senha ou hash de senha **devolvidos na resposta da API**: campo `senha`/`password`/`password_hash` em `to_dict()`, em `GET /usuarios` ou no JSON de resposta do login;
  - número de cartão de crédito ou secret logado (`console.log(cartao)`, `print(senha)`).
- **Por que é problema:** MD5/SHA1 sem salt quebram por rainbow table em segundos; hash reversível equivale a texto plano; devolver o hash na API entrega o material de ataque de graça.
- **Stacks aplicáveis:** todas.

## AP-05 — Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth

- **Severidade:** CRITICAL
- **Sinais de detecção:**
  - endpoint que executa SQL vindo do body/query string: `/admin/query` com `cursor.execute(request.json['sql'])`;
  - uso de `eval()`/`exec()`/`Function()` sobre input externo;
  - endpoints destrutivos sem nenhuma verificação de autenticação: `/admin/reset-db` que dá DROP/DELETE em tabelas, `DELETE /recurso/<id>` aberto ao público.
- **Por que é problema:** qualquer cliente anônimo pode executar comandos arbitrários ou destruir o banco inteiro com uma única requisição.
- **Remediação (RP-12) tem de ser viva:** SQL arbitrário → **remover**; rota destrutiva legítima → auth **aplicada à rota** e verificada (401 sem token). Infra de auth desconectada (decorator não aplicado, flag desligada por padrão) **não** corrige o finding — a Fase 3 valida 401 sem token e 2xx com token.
- **Stacks aplicáveis:** todas.

## AP-06 — Missing Authentication / Authorization

- **Severidade:** HIGH
- **Sinais de detecção:**
  - rotas sensíveis (admin, escrita, dados pessoais) sem middleware/decorator de auth (`@login_required`, verificação de token no handler ou em middleware);
  - "token" previsível/sem assinatura: `f"fake-jwt-token-{user_id}"`, token = id do usuário, token nunca verificado nas rotas seguintes;
  - login que responde sucesso sem criar sessão/token verificável.
- **Por que é problema:** qualquer usuário (ou não-usuário) acessa ou modifica dados de outros; o "token" pode ser forjado trivialmente.
- **Remediação (RP-12) tem de ser viva:** token assinado/verificável + middleware/decorator **aplicado às rotas sensíveis por padrão** (não atrás de flag desligada, não só declarado). A Fase 3 valida 401 sem token e 2xx com token em cada rota apontada.
- **Stacks aplicáveis:** todas.

## AP-07 — Business Logic in Controller/Route

- **Severidade:** HIGH
- **Sinais de detecção:**
  - cálculo de negócio (desconto, frete, total do pedido, regras de pagamento) dentro do handler HTTP (`@app.route` / `app.post(...)`);
  - efeitos colaterais no handler: envio de email, cobrança, escrita em múltiplas tabelas orquestrada inline;
  - handler > ~40 linhas misturando parsing de request, validação, SQL/ORM e formatação de resposta.
- **Por que é problema:** viola MVC e SRP; a regra de negócio não é testável sem HTTP; duplicação inevitável entre rotas.
- **Stacks aplicáveis:** todas.

## AP-08 — Global Mutable State

- **Severidade:** HIGH
- **Sinais de detecção:**
  - variável de módulo mutável compartilhada entre requisições: `globalCache = {}`, `totalRevenue = 0`, listas/dicts acumulando dados por request sem limpeza (memory leak);
  - conexão de banco singleton criada no import e reutilizada por todas as rotas sem escopo;
  - estado de negócio (contadores, carrinhos, sessões) em variáveis globais em vez do banco.
- **Por que é problema:** condições de corrida entre requisições, vazamento de memória, dados inconsistentes entre workers, impossível escalar horizontalmente.
- **Stacks aplicáveis:** todas (muito comum em Node com objetos de módulo e em Flask com globals de módulo).

## AP-09 — Missing Transaction / Non-atomic Writes

- **Severidade:** HIGH
- **Sinais de detecção:**
  - múltiplos INSERT/UPDATE relacionados (pedido + itens + baixa de estoque; enrollment + payment) sem `BEGIN`/`commit`/`rollback` envolvendo o conjunto;
  - `commit()` chamado após cada escrita individual, ou ausência de `rollback` em caso de erro no meio do fluxo;
  - em Node com callbacks: `db.run(...)` encadeados sem transação — se o segundo falha, o primeiro persiste.
- **Por que é problema:** falha no meio do fluxo deixa o banco inconsistente (pedido sem itens, pagamento sem matrícula, estoque errado).
- **Stacks aplicáveis:** todas.

## AP-10 — Insecure Config em Produção

- **Severidade:** HIGH
- **Sinais de detecção:**
  - `app.run(debug=True)` (debugger interativo do Werkzeug exposto = RCE);
  - bind em `0.0.0.0` sem necessidade;
  - CORS aberto: `CORS(app)` sem restrição de origins, `Access-Control-Allow-Origin: *` em API autenticada;
  - Express sem `helmet`, `express.json()` sem `limit`, ausência de rate limiting em rotas de login.
- **Por que é problema:** debug=True permite execução remota de código; CORS aberto + credenciais permite abuso cross-site; payloads ilimitados permitem DoS.
- **Stacks aplicáveis:** Flask (debug/CORS), Express (helmet/limit), equivalentes em outras stacks.

## AP-11 — N+1 Query

- **Severidade:** MEDIUM
- **Sinais de detecção:**
  - query dentro de loop: `for pedido in pedidos: cursor.execute("SELECT ... WHERE pedido_id = ?", ...)`;
  - ORM: `Model.query.get(id)` / `db.session.get(...)` chamado por item dentro de um `for` sobre uma lista de resultados;
  - ausência de JOIN ou eager loading (`joinedload`, `selectinload`) quando a rota monta lista com dados de tabela relacionada;
  - em Node: `db.get`/`db.all` dentro de `forEach`/loop de resultados.
- **Por que é problema:** 1 + N queries por requisição; latência cresce linearmente com os dados; derruba o banco sob carga.
- **Stacks aplicáveis:** todas (SQL cru e ORM).

## AP-12 — Deprecated API Usage (seção obrigatória)

- **Severidade:** MEDIUM
- **Regra:** identificar **cada uso** de API obsoleta E recomendar o equivalente moderno. Conte as ocorrências (ex.: "22 usos de `datetime.utcnow()`"). Um finding por API deprecated (agrupando as ocorrências), não por linha.

### Python

| API deprecated (sinal de detecção) | Substituto moderno |
|---|---|
| `datetime.utcnow()` (deprecated desde Python 3.12 — retorna datetime naive) | `datetime.now(timezone.utc)` |
| `datetime.utcfromtimestamp(ts)` | `datetime.fromtimestamp(ts, tz=timezone.utc)` |
| SQLAlchemy `Model.query.get(id)` / `Query.get()` (legacy, removido no SQLAlchemy 2.x style) | `db.session.get(Model, id)` |
| `Model.query.filter(...)` (API legacy `Query`) | `db.session.execute(select(Model).where(...))` (estilo 2.0) |
| `@app.before_first_request` (removido no Flask 2.3+) | inicialização no factory / `with app.app_context():` |

### Node

| API deprecated (sinal de detecção) | Substituto moderno |
|---|---|
| `require('body-parser')` / `bodyParser.json()` (embutido desde Express 4.16) | `express.json()` / `express.urlencoded()` |
| `crypto.createCipher` / `crypto.createDecipher` (removidos no Node 22) | `crypto.createCipheriv` / `crypto.createDecipheriv` |
| `new Buffer(...)` (deprecated por risco de segurança) | `Buffer.from(...)` / `Buffer.alloc(...)` |
| Callbacks aninhados (error-first callbacks, callback hell) | `async/await` + Promises (`util.promisify`, `fs.promises`) |
| `url.parse(...)` | `new URL(...)` |
| Express 4 (`^4.x` no package.json) | avaliar migração para Express 5 quando aplicável |

- **Por que é problema:** APIs deprecated quebram em upgrades de runtime/lib, algumas têm falhas de segurança conhecidas (`new Buffer`, `createCipher`), e datetimes naive causam bugs de timezone silenciosos.
- **Stacks aplicáveis:** Python e Node (tabelas acima); para outras stacks, consultar changelog do runtime.

## AP-13 — Missing Input Validation

- **Severidade:** MEDIUM
- **Sinais de detecção:**
  - campos do body usados direto sem checar presença/tipo: `data['nome']` (KeyError → 500), `req.body.email` sem verificação;
  - conversão/comparação numérica sobre input não validado: `int(request.args['page'])`, `if data['preco'] < 0` quando `preco` pode ser string/ausente;
  - ausência de resposta 400 com mensagem clara para payload inválido — erros viram 500 genérico.
- **Por que é problema:** requisições malformadas derrubam o handler (500 em vez de 400), dados inválidos entram no banco, mensagens de erro vazam stack trace.
- **Stacks aplicáveis:** todas.

## AP-14 — Code Duplication & Dead Layers (camadas de fachada)

- **Severidade:** MEDIUM
- **Sinais de detecção:**
  - blocos de validação/serialização repetidos em várias rotas (mesmo `if not data.get(...)` copiado);
  - helper/service existente e **nunca importado**: diretório `services/` que nenhuma rota usa (código morto de fachada), `utils/` duplicando função que já existe em `services/`;
  - duas implementações da mesma regra em lugares diferentes (divergência garantida).
- **Por que é problema:** manutenção dupla, correções aplicadas em só um dos clones, e camadas de fachada dão falsa impressão de arquitetura organizada.
- **Stacks aplicáveis:** todas (verificar imports reais, não a existência dos diretórios).

## AP-15 — Poor Naming / Magic Numbers

- **Severidade:** LOW
- **Sinais de detecção:**
  - variáveis de 1-2 letras fora de índices de loop: `u`, `e`, `p`, `cc`, `d`;
  - literais numéricos soltos sem constante nomeada: `10000`, `5000`, `0.1` (limite? desconto? timeout?);
  - nomes que mentem (`get_user` que também cria usuário) ou misturam idiomas sem padrão.
- **Por que é problema:** o leitor não consegue inferir intenção; números mágicos mudam em um lugar e não no outro.
- **Stacks aplicáveis:** todas.

## AP-16 — Dead Code / Bad Hygiene

- **Severidade:** LOW
- **Sinais de detecção:**
  - imports nunca usados; funções/arquivos nunca chamados; dependências declaradas no manifesto e não importadas;
  - `except:` nu (engole `KeyboardInterrupt`/`SystemExit` e esconde a causa) ou `catch (e) {}` vazio;
  - `print()` / `console.log` como logging de produção (inclusive logando dados sensíveis — se logar senha/cartão, escale para AP-04);
  - código comentado abandonado.
- **Por que é problema:** ruído que confunde a leitura, erros silenciados dificultam debugging, dependências mortas incham o deploy.
- **Stacks aplicáveis:** todas.

---

## Checklist de varredura rápida (aplicar por arquivo)

1. Secrets literais? (AP-01) — grep: `SECRET`, `password`, `pk_live`, `smtp`
2. SQL com `+`/f-string/template literal? (AP-02)
3. Arquivo/classe/função gigante multi-responsabilidade? (AP-03)
4. `md5`/`sha1`/hash caseiro/senha na resposta? (AP-04)
5. SQL/`eval` do body? rota destrutiva sem auth? (AP-05)
6. Rota sensível sem auth? token falso? (AP-06)
7. Regra de negócio no handler? (AP-07)
8. Global mutável entre requests? (AP-08)
9. Escritas relacionadas sem transação? (AP-09)
10. `debug=True`/CORS aberto/sem helmet? (AP-10)
11. Query em loop? (AP-11)
12. API deprecated das tabelas? (AP-12) — grep: `utcnow`, `.query.get`, `body-parser`, `createCipher`, `new Buffer`
13. Body usado sem validação? (AP-13)
14. Duplicação/camada morta? (AP-14)
15. Nomes ruins/números mágicos? (AP-15)
16. Imports mortos/`except:` nu/`print` como log? (AP-16)
