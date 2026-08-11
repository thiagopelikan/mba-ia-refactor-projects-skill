# Playbook de Refatoração (Fase 3)

15 padrões de transformação (RP-01 a RP-15), cada um com anti-pattern alvo (IDs do `references/anti-patterns-catalog.md`), objetivo, código ANTES/DEPOIS e notas. As camadas citadas (**Config, Models, Views/Routes, Controllers, Middlewares, Entry point / Composition root**) são as definidas em `references/mvc-guidelines.md`.

## Tabela de rastreabilidade — anti-pattern → padrão de refatoração

| Anti-pattern (catálogo) | Severidade | Padrão(ões) do playbook |
|---|---|---|
| AP-01 Hardcoded Credentials / Secrets | CRITICAL | RP-01 |
| AP-02 SQL Injection | CRITICAL | RP-02 |
| AP-03 God Class / God Module / God Method | CRITICAL | RP-03, RP-13 |
| AP-04 Weak/Broken Password Hashing & Exposição de Senha | CRITICAL | RP-04 |
| AP-05 Arbitrary SQL/Code Execution & Endpoints Destrutivos sem Auth | CRITICAL | RP-12 |
| AP-06 Missing Authentication / Authorization | HIGH | RP-12 |
| AP-07 Business Logic in Controller/Route | HIGH | RP-05 |
| AP-08 Global Mutable State | HIGH | RP-06 |
| AP-09 Missing Transaction / Non-atomic Writes | HIGH | RP-07 |
| AP-10 Insecure Config em Produção | HIGH | RP-01, RP-08 |
| AP-11 N+1 Query | MEDIUM | RP-09 |
| AP-12 Deprecated API Usage | MEDIUM | RP-10, RP-13 |
| AP-13 Missing Input Validation | MEDIUM | RP-11 |
| AP-14 Code Duplication & Dead Layers | MEDIUM | RP-14 |
| AP-15 Poor Naming / Magic Numbers | LOW | RP-15 |
| AP-16 Dead Code / Bad Hygiene | LOW | RP-08, RP-15 |

---

## RP-01 — Extrair config para módulo Config (remover hardcoded)

- **Anti-pattern alvo:** AP-01 (e a parte de configuração de AP-10)
- **Objetivo:** nenhum secret/valor configurável no código; tudo em `config/` lendo env vars, documentado em `.env.example`.

**ANTES** (`app.py`):

```python
app = Flask(__name__)
app.config['SECRET_KEY'] = "minha-chave-super-secreta-123"
SMTP_PASSWORD = "senha-smtp-123"
```

**DEPOIS** (`config/settings.py`):

```python
import os

SECRET_KEY = os.environ["SECRET_KEY"]          # obrigatória: falha cedo se ausente
DATABASE_PATH = os.environ.get("DATABASE_PATH", "app.db")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"
```

`.env.example` (na raiz):

```
SECRET_KEY=troque-por-uma-chave-aleatoria
DATABASE_PATH=app.db
SMTP_HOST=
SMTP_PASSWORD=
FLASK_DEBUG=0
```

**Versão Node** (`src/config/index.js`):

```js
module.exports = {
  port: process.env.PORT || 3000,
  paymentKey: process.env.PAYMENT_API_KEY,   // nunca pk_live_ hardcoded
  smtp: { host: process.env.SMTP_HOST, pass: process.env.SMTP_PASS },
};
```

- **Notas:** secrets obrigatórios sem default (falhar no boot é melhor que rodar com chave vazia); defaults só para valores não sensíveis. Remover também secrets expostos em endpoints (ex.: `/health` devolvendo `SECRET_KEY` — devolver apenas `{"status": "ok"}`).

## RP-02 — Parametrizar queries (eliminar SQL Injection)

- **Anti-pattern alvo:** AP-02
- **Objetivo:** toda query com variáveis usa placeholders do driver; nunca concatenação/f-string/template literal.

**ANTES** (Python):

```python
query = "SELECT * FROM produtos WHERE id = " + str(produto_id)
cursor.execute(query)
cursor.execute(f"SELECT * FROM usuarios WHERE nome LIKE '%{termo}%'")
```

**DEPOIS**:

```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
cursor.execute("SELECT * FROM usuarios WHERE nome LIKE ?", (f"%{termo}%",))
```

**Versão Node** (`sqlite3`):

```js
// ANTES
db.get(`SELECT * FROM users WHERE email = '${email}'`, cb);
// DEPOIS
db.get("SELECT * FROM users WHERE email = ?", [email], cb);
```

- **Notas:** o `%` do LIKE entra no **parâmetro**, não no SQL. Em ORM, usar a API de expressão (`.where(Model.nome == valor)`) — nunca `text()` interpolado. Estas queries parametrizadas moram nos Models.

## RP-03 — Quebrar God Class/Module em camadas MVC

- **Anti-pattern alvo:** AP-03
- **Objetivo:** separar o monolito nas camadas Config, Models, Views/Routes, Controllers, Middlewares e Entry point / Composition root, por domínio.

**ANTES** (`models.py` — um arquivo com tudo):

```python
# models.py (350 linhas): conexão + SQL + regra de negócio + validação + formatação
def criar_pedido(data):
    conn = sqlite3.connect("app.db")
    if not data.get("usuario_id"): return {"erro": "usuario_id obrigatorio"}   # validação
    total = sum(i["preco"] * i["qtd"] for i in data["itens"])                  # negócio
    conn.execute("INSERT INTO pedidos ...")                                    # dados
    return {"id": ..., "total": f"R$ {total:.2f}"}                             # apresentação
```

**DEPOIS** (cada responsabilidade em sua camada):

```python
# models/pedido_model.py — só dados e regra de domínio
class PedidoModel:
    def __init__(self, conn):
        self.conn = conn
    def criar(self, usuario_id, itens):
        total = sum(i["preco"] * i["qtd"] for i in itens)
        cur = self.conn.execute(
            "INSERT INTO pedidos (usuario_id, total) VALUES (?, ?)", (usuario_id, total))
        return {"id": cur.lastrowid, "total": total}

# controllers/pedido_controller.py — orquestra validação → model → resposta
class PedidoController:
    def __init__(self, pedido_model):
        self.pedido_model = pedido_model
    def criar(self, data):
        erro = validar_pedido(data)          # middlewares/validators
        if erro:
            return {"error": erro}, 400
        pedido = self.pedido_model.criar(data["usuario_id"], data["itens"])
        return pedido, 201

# views/routes.py — rota fina
@pedidos_bp.route("/pedidos", methods=["POST"])
def criar_pedido():
    body, status = pedido_controller.criar(request.get_json(silent=True) or {})
    return jsonify(body), status
```

- **Notas:** um model + um controller **por domínio**. O Entry point / Composition root instancia models (com a conexão), controllers (com os models) e registra os blueprints. Em Node, o equivalente é quebrar a God Class (ex.: `AppManager`) em `models/`, `controllers/` e `routes/` com `Router` por domínio.

## RP-04 — Hash de senha seguro (e nunca expor senha/hash)

- **Anti-pattern alvo:** AP-04
- **Objetivo:** hashing com algoritmo dedicado a senhas (salt embutido); resposta da API jamais contém senha/hash; dados sensíveis fora dos logs.

**ANTES**:

```python
senha_hash = hashlib.md5(senha.encode()).hexdigest()      # MD5 sem salt
return jsonify({"id": u.id, "senha": u.senha_hash})       # hash devolvido na API
```

**DEPOIS**:

```python
from werkzeug.security import generate_password_hash, check_password_hash

senha_hash = generate_password_hash(senha)                 # salt automático
# login:
if check_password_hash(u.senha_hash, senha_informada): ...
# serialização segura no Model:
def to_dict(self):
    return {"id": self.id, "nome": self.nome, "email": self.email}  # sem senha/hash
```

**Versão Node** (substituindo hash caseiro reversível tipo `badCrypto`):

```js
// ANTES: badCrypto(pwd) — XOR/base64 reversível; console.log(cardNumber)
// DEPOIS:
const bcrypt = require("bcrypt");
const hash = await bcrypt.hash(password, 10);
const ok = await bcrypt.compare(password, user.passwordHash);
// e remover QUALQUER log de cartão/senha/chave
```

- **Notas:** migração dos hashes antigos: re-hash no próximo login bem-sucedido (verifica no formato antigo, regrava no novo). `bcrypt`/`werkzeug` embutem salt — nunca implementar hash próprio.

## RP-05 — Mover lógica de negócio do Controller/rota para Model/serviço

- **Anti-pattern alvo:** AP-07
- **Objetivo:** handler HTTP fino; regra de negócio testável sem HTTP, vivendo no Model (ou serviço de domínio quando o projeto já tem `services/`).

**ANTES** (regra de desconto dentro da rota):

```python
@app.route("/pedidos", methods=["POST"])
def criar_pedido():
    data = request.json
    total = sum(i["preco"] * i["qtd"] for i in data["itens"])
    if total > 10000:
        total = total * 0.9          # regra de negócio no handler
    enviar_email_confirmacao(data["email"])   # efeito colateral no handler
    conn.execute("INSERT INTO pedidos ...")
    return jsonify({"total": total})
```

**DEPOIS**:

```python
# models/pedido_model.py (regra de domínio nomeada e testável)
LIMITE_DESCONTO = 10_000
PERCENTUAL_DESCONTO = 0.10

def calcular_total(itens):
    total = sum(i["preco"] * i["qtd"] for i in itens)
    if total > LIMITE_DESCONTO:
        total -= total * PERCENTUAL_DESCONTO
    return total

# controllers/pedido_controller.py (orquestra; efeitos colaterais explícitos)
def criar(self, data):
    total = calcular_total(data["itens"])
    pedido = self.pedido_model.criar(data["usuario_id"], data["itens"], total)
    self.notificador.confirmar_pedido(data["email"], pedido)   # injetado
    return pedido, 201
```

- **Notas:** o critério é: "dá para testar essa regra sem subir o servidor?". Envio de email/cobrança vira colaborador injetado pelo composition root (mock trivial em teste). Em projeto com `services/` já existente e correto, mover a regra para lá e fazer o controller usá-lo.

## RP-06 — Substituir estado global mutável por injeção/escopo de request

- **Anti-pattern alvo:** AP-08
- **Objetivo:** nenhum dado de negócio em variáveis de módulo; conexão com escopo gerenciado; estado persistente no banco.

**ANTES** (Node):

```js
let globalCache = {};        // cresce para sempre — memory leak
let totalRevenue = 0;        // some no restart; errado com 2+ workers
db = new sqlite3.Database(":memory:");   // singleton global
app.post("/checkout", (req, res) => { totalRevenue += req.body.amount; ... });
```

**DEPOIS**:

```js
// models/orderModel.js — receita é derivada do banco, não acumulada em memória
function getTotalRevenue(db, cb) {
  db.get("SELECT COALESCE(SUM(amount), 0) AS total FROM payments", cb);
}
// app.js (composition root) — cria a conexão UMA vez e injeta nos models
const db = createDatabase(config.dbPath);
const orderModel = new OrderModel(db);
```

**Versão Python** (conexão por request):

```python
# ANTES: conn = sqlite3.connect("app.db") no topo do módulo, compartilhada
# DEPOIS: database.py
from flask import g
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()
```

- **Notas:** cache legítimo precisa de TTL e limite de tamanho (ou sai de cena na refatoração). Estado que precisa sobreviver a restart pertence ao banco. A injeção acontece no Entry point / Composition root.

## RP-07 — Envolver escritas relacionadas em transação

- **Anti-pattern alvo:** AP-09
- **Objetivo:** conjunto de escritas relacionadas é atômico: tudo commita ou tudo reverte.

**ANTES**:

```python
conn.execute("INSERT INTO pedidos (usuario_id, total) VALUES (?, ?)", (uid, total))
conn.commit()
for item in itens:
    conn.execute("INSERT INTO itens_pedido ... ", (...))   # se falhar aqui,
    conn.commit()                                          # o pedido fica órfão
```

**DEPOIS**:

```python
try:
    cur = conn.execute("INSERT INTO pedidos (usuario_id, total) VALUES (?, ?)", (uid, total))
    pedido_id = cur.lastrowid
    for item in itens:
        conn.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, qtd) VALUES (?, ?, ?)",
            (pedido_id, item["produto_id"], item["qtd"]))
    conn.commit()
except Exception:
    conn.rollback()
    raise
```

**Versão Node** (sqlite3):

```js
db.serialize(() => {
  db.run("BEGIN");
  db.run("INSERT INTO enrollments (userId, courseId) VALUES (?, ?)", [userId, courseId]);
  db.run("INSERT INTO payments (userId, amount) VALUES (?, ?)", [userId, amount], (err) => {
    if (err) return db.run("ROLLBACK", () => next(err));
    db.run("COMMIT", (err2) => (err2 ? next(err2) : res.status(201).json({ ok: true })));
  });
});
```

- **Notas:** a transação mora no Model (método de domínio, ex.: `PedidoModel.criar_com_itens`). Com ORM: `db.session` acumula e `commit()` uma vez no fim, `rollback()` no except. Combine com RP-13 em Node — com `async/await` a transação fica linear.

## RP-08 — Centralizar error handling em Middlewares

- **Anti-pattern alvo:** AP-16 (`except:` nu, erros engolidos) e a parte de vazamento de erro de AP-10; elimina os try/except duplicados (AP-14)
- **Objetivo:** um único ponto converte exceções em respostas HTTP padronizadas, sem vazar stack trace, com logging real.

**ANTES** (repetido em cada handler):

```python
@app.route("/produtos/<int:pid>")
def get_produto(pid):
    try:
        ...
    except:                      # except nu, engole tudo
        return str(e), 500       # vaza detalhes internos
```

**DEPOIS** (`middlewares/error_handler.py`):

```python
import logging
from flask import jsonify
logger = logging.getLogger(__name__)

class NotFoundError(Exception): ...
class ValidationError(Exception): ...

def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation(e):
        return jsonify({"error": str(e)}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(e):
        return jsonify({"error": str(e)}), 404

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        logger.exception("Erro não tratado")          # log completo no servidor
        return jsonify({"error": "Erro interno"}), 500  # resposta genérica ao cliente
```

**Versão Node** (`middlewares/errorHandler.js` — registrado por último no `app.js`):

```js
module.exports = (err, req, res, next) => {
  console.error(err);                               // trocar por logger estruturado
  const status = err.status || 500;
  const message = status === 500 ? "Erro interno" : err.message;
  res.status(status).json({ error: message });
};
// nos handlers async: catch(next) — nunca try/catch duplicado por rota
```

- **Notas:** controllers levantam exceções tipadas (`ValidationError`, `NotFoundError`); nenhum handler tem try/except próprio. `print()`/`console.log` de erro vira logging estruturado. Registrado no Entry point / Composition root.

## RP-09 — Corrigir N+1 com JOIN / eager loading

- **Anti-pattern alvo:** AP-11
- **Objetivo:** 1 query (ou 2 com eager loading) no lugar de 1 + N.

**ANTES** (SQL cru):

```python
pedidos = conn.execute("SELECT * FROM pedidos").fetchall()
for p in pedidos:
    itens = conn.execute(
        "SELECT * FROM itens_pedido WHERE pedido_id = " + str(p["id"])).fetchall()  # N+1 (e AP-02)
```

**DEPOIS**:

```python
rows = conn.execute("""
    SELECT p.id, p.total, i.produto_id, i.qtd
    FROM pedidos p
    LEFT JOIN itens_pedido i ON i.pedido_id = p.id
""").fetchall()
# agrupar por p.id em memória para montar a resposta
```

**Versão ORM (SQLAlchemy)**:

```python
# ANTES: for t in Task.query.all(): categoria = Category.query.get(t.category_id)
# DEPOIS:
from sqlalchemy import select
from sqlalchemy.orm import selectinload
tasks = db.session.execute(
    select(Task).options(selectinload(Task.category))
).scalars().all()   # 2 queries no total, independente de N
```

- **Notas:** a query consolidada mora no Model. Em Node, mesma ideia: um `db.all` com JOIN em vez de `db.get` dentro de loop/`forEach`.

## RP-10 — Substituir APIs deprecated

- **Anti-pattern alvo:** AP-12
- **Objetivo:** nenhum uso das APIs listadas nas tabelas do catálogo; substituir **todas** as ocorrências (são dezenas em alguns projetos — use busca global).

**ANTES** (Python):

```python
from datetime import datetime
created_at = datetime.utcnow()          # deprecated (naive)
task = Task.query.get(task_id)          # API legacy do SQLAlchemy
```

**DEPOIS**:

```python
from datetime import datetime, timezone
created_at = datetime.now(timezone.utc)
task = db.session.get(Task, task_id)
```

**ANTES** (Node):

```js
const bodyParser = require("body-parser");
app.use(bodyParser.json());
const cipher = crypto.createCipher("aes192", key);
const buf = new Buffer(data);
```

**DEPOIS**:

```js
app.use(express.json());
const iv = crypto.randomBytes(16);
const cipher = crypto.createCipheriv("aes-192-cbc", key, iv);
const buf = Buffer.from(data);
```

- **Notas:** em colunas SQLAlchemy, `default=datetime.utcnow` (referência) vira `default=lambda: datetime.now(timezone.utc)`. Callbacks → async/await é o RP-13. Após a troca, rodar a app para confirmar que não há warnings de deprecação no boot.

## RP-11 — Adicionar validação de entrada

- **Anti-pattern alvo:** AP-13
- **Objetivo:** todo input externo é validado (presença + tipo + faixa) antes de uso; payload inválido → 400 com mensagem clara, nunca 500.

**ANTES**:

```python
@app.route("/produtos", methods=["POST"])
def criar_produto():
    data = request.json
    preco = data["preco"]              # KeyError → 500
    conn.execute("INSERT INTO produtos (nome, preco) VALUES (?, ?)",
                 (data["nome"], preco))
```

**DEPOIS**:

```python
# middlewares/validators.py (ou validators do domínio)
def validar_produto(data):
    if not data or not isinstance(data.get("nome"), str) or not data["nome"].strip():
        return "campo 'nome' é obrigatório e deve ser texto"
    if not isinstance(data.get("preco"), (int, float)) or data["preco"] <= 0:
        return "campo 'preco' é obrigatório e deve ser número positivo"
    return None

# controllers/produto_controller.py
def criar(self, data):
    erro = validar_produto(data)
    if erro:
        return {"error": erro}, 400
    produto = self.produto_model.criar(data["nome"], data["preco"])
    return produto, 201
```

- **Notas:** validação chamada pelo Controller (ou como middleware), reutilizada por todas as rotas do domínio — o que também elimina a duplicação de AP-14. Em Node, mesma estrutura: função `validateOrder(body)` retornando mensagem ou `null`; com libs disponíveis, schemas (`zod`, `marshmallow`) são bem-vindos, mas validação manual centralizada já resolve.

## RP-12 — Proteger endpoints e remover rotas perigosas

- **Anti-pattern alvo:** AP-05, AP-06
- **Objetivo:** eliminar execução arbitrária de SQL/código; rotas destrutivas removidas ou atrás de auth real; token verificável em vez de string previsível.

**ANTES**:

```python
@app.route("/admin/query", methods=["POST"])
def admin_query():
    return jsonify(conn.execute(request.json["sql"]).fetchall())   # SQL arbitrário, sem auth

@app.route("/admin/reset-db", methods=["POST"])
def reset_db():
    recreate_tables()                                              # destrutivo, sem auth

token = f"fake-jwt-token-{user.id}"                                # previsível, nunca verificado
```

**DEPOIS**:

```python
# 1. /admin/query: REMOVER — nenhuma refatoração torna SQL arbitrário via HTTP aceitável.
#    (Registrar a remoção no output da Fase 3; consultas ad-hoc pertencem a ferramentas de DB.)

# 2. Rotas administrativas legítimas: atrás de auth (middlewares/auth.py)
import jwt
from functools import wraps
from config.settings import SECRET_KEY

def gerar_token(user_id):
    return jwt.encode({"sub": str(user_id)}, SECRET_KEY, algorithm="HS256")

def auth_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "não autenticado"}), 401
        try:
            payload = jwt.decode(auth[7:], SECRET_KEY, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return jsonify({"error": "token inválido"}), 401
        g.user_id = payload["sub"]
        return f(*args, **kwargs)
    return wrapper

@admin_bp.route("/admin/reset-db", methods=["POST"])
@auth_required
def reset_db(): ...
```

**Versão Node** (`middlewares/auth.js` aplicado em `DELETE`/rotas admin):

```js
const jwt = require("jsonwebtoken");
module.exports = (req, res, next) => {
  const header = req.headers.authorization || "";
  if (!header.startsWith("Bearer ")) return res.status(401).json({ error: "não autenticado" });
  try {
    req.user = jwt.verify(header.slice(7), config.secretKey);
    next();
  } catch {
    res.status(401).json({ error: "token inválido" });
  }
};
// routes: router.delete("/courses/:id", auth, courseController.remove);
```

- **Notas:** decisão por rota perigosa: **remover** (SQL arbitrário) ou **proteger** (admin/destrutivas legítimas). Se adicionar `PyJWT`/`jsonwebtoken` não for viável no projeto, o mínimo é token aleatório (`secrets.token_urlsafe`) armazenado server-side e **verificado** em toda rota protegida — nunca `fake-jwt-token-{id}`. Endpoints protegidos continuam existindo (contrato preservado); apenas passam a exigir auth. Registre no relatório final qualquer mudança de comportamento (ex.: rota removida).

## RP-13 — Converter callbacks aninhados para async/await (Node)

- **Anti-pattern alvo:** AP-12 (callbacks → async/await) e a dimensão "método gigante aninhado" de AP-03
- **Objetivo:** fluxo linear e legível; erros propagam para o error handler central via `next(err)`.

**ANTES** (callback hell no checkout):

```js
app.post("/checkout", (req, res) => {
  db.get("SELECT * FROM users WHERE id = ?", [req.body.userId], (err, user) => {
    if (err) return res.status(500).send(err.message);
    db.get("SELECT * FROM courses WHERE id = ?", [req.body.courseId], (err2, course) => {
      if (err2) return res.status(500).send(err2.message);
      db.run("INSERT INTO enrollments ...", [user.id, course.id], (err3) => {
        if (err3) return res.status(500).send(err3.message);
        db.run("INSERT INTO payments ...", [user.id, course.price], (err4) => {
          if (err4) return res.status(500).send(err4.message);
          sendEmail(user.email, () => res.json({ ok: true }));   // 5 níveis
        });
      });
    });
  });
});
```

**DEPOIS** (db promisificado no módulo de infra + controller async):

```js
// db.js
const { promisify } = require("util");
db.getAsync = promisify(db.get).bind(db);
db.runAsync = promisify(db.run).bind(db);

// controllers/checkoutController.js
async function checkout(req, res, next) {
  try {
    const { userId, courseId } = req.body;
    const user = await db.getAsync("SELECT * FROM users WHERE id = ?", [userId]);
    const course = await db.getAsync("SELECT * FROM courses WHERE id = ?", [courseId]);
    if (!user || !course) return res.status(404).json({ error: "não encontrado" });
    await enrollmentModel.enrollWithPayment(user, course);   // transação (RP-07)
    await mailer.sendConfirmation(user.email);
    res.status(201).json({ ok: true });
  } catch (err) {
    next(err);                                               // error handler central (RP-08)
  }
}
```

- **Notas:** promisificar na borda da infra (uma vez), nunca por chamada. O try/catch único delega ao middleware de erro. Isso habilita RP-07 (transação linear) no mesmo passo.

## RP-14 — Absorver/remover camadas de fachada e deduplicar

- **Anti-pattern alvo:** AP-14
- **Objetivo:** cada regra existe em UM lugar; camadas existentes viram parte real do fluxo ou são removidas.

**ANTES** (projeto "parcialmente em camadas"):

```
routes/task_routes.py     → contém a lógica de verdade (inline, duplicada)
services/task_service.py  → implementa a mesma lógica, NUNCA importado (fachada)
utils/helpers.py          → duplica validações do services/, também não usado
```

**DEPOIS**:

```python
# 1. Eleger a implementação canônica (a mais correta/completa — muitas vezes a do services/).
# 2. Conectá-la ao fluxo real:
# routes/task_routes.py
@tasks_bp.route("/tasks", methods=["POST"])
def criar_task():
    body, status = task_controller.criar(request.get_json(silent=True) or {})
    return jsonify(body), status

# controllers/task_controller.py usa o service/model canônico:
def criar(self, data):
    erro = validar_task(data)            # ÚNICA implementação da validação
    if erro:
        return {"error": erro}, 400
    task = self.task_service.criar(data) # service existente, agora usado de verdade
    return task.to_dict(), 201

# 3. Remover os clones (utils/helpers.py duplicado) e registrar a remoção no output.
```

- **Notas:** segue a "Regra de ADAPTAÇÃO" das guidelines: aproveitar métodos de domínio existentes em vez de reescrever. Antes de remover um arquivo "morto", confirmar com busca global que nada o importa. Blocos repetidos entre rotas viram função única em validators/serializers do domínio.

## RP-15 — Limpeza de código (naming, magic numbers, dead code)

- **Anti-pattern alvo:** AP-15, AP-16
- **Objetivo:** nomes que revelam intenção, constantes nomeadas, zero código morto, erros nunca engolidos.

**ANTES**:

```python
import os, json, hashlib, base64, random   # metade nunca usada

def proc(u, p, cc):
    d = cc * 0.1 if cc > 10000 else 0
    try:
        ...
    except:                                # except nu
        print("erro")                      # print como logging
```

**DEPOIS**:

```python
import logging
logger = logging.getLogger(__name__)

LIMITE_DESCONTO = 10_000
PERCENTUAL_DESCONTO = 0.10

def calcular_desconto(usuario, valor_compra):
    if valor_compra > LIMITE_DESCONTO:
        return valor_compra * PERCENTUAL_DESCONTO
    return 0.0
# exceções específicas propagam para o error handler central (RP-08);
# nunca `except:` nu — capture o tipo específico ou deixe subir.
```

- **Notas:** remover imports não usados e dependências mortas do manifesto (`requirements.txt`/`package.json`) quando nada as importa. Constantes de negócio moram no Model do domínio (ou na Config, se configuráveis). `print`/`console.log` → logger. Renomeações não podem mudar contratos HTTP (nomes de campos JSON expostos só mudam se o contrato for preservado).

---

## Ordem de aplicação recomendada na Fase 3

1. **RP-01** (Config) — desbloqueia o resto sem secrets espalhados.
2. **RP-03 / RP-14** (estrutura: quebrar God Class ou adaptar camadas existentes) — cria o esqueleto MVC.
3. **RP-02, RP-04, RP-12** (segurança: queries, hashing, auth/rotas perigosas).
4. **RP-13** (async/await em Node) e **RP-07** (transações).
5. **RP-05, RP-06** (negócio para Models; eliminar estado global).
6. **RP-08** (error handling central), **RP-11** (validação).
7. **RP-09** (N+1), **RP-10** (deprecated), **RP-15** (limpeza).
8. Validação final: boot + endpoints (conforme SKILL.md, Fase 3).
