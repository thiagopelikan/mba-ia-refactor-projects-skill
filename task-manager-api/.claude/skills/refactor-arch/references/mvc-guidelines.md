# Guidelines da Arquitetura MVC Alvo (Fase 3)

Estrutura-alvo que a Fase 3 cria. As camadas são: **Config**, **Models**, **Views/Routes**, **Controllers**, **Middlewares** e **Entry point / Composition root**. O playbook (`references/refactoring-playbook.md`) usa exatamente estes nomes.

## Camadas e responsabilidades

### Config (`config/settings.py` | `config/index.js`)

- Carrega **todas** as configurações de variáveis de ambiente: `SECRET_KEY`, string de conexão do DB, credenciais SMTP, chaves de pagamento, porta, flags de debug.
- **Zero valores hardcoded** no restante do código — se um valor é configurável ou sensível, ele mora aqui e vem de env var (com default seguro apenas para valores não sensíveis, ex.: porta).
- Acompanha um `.env.example` na raiz documentando cada chave esperada (sem os valores reais).
- Não contém lógica; apenas leitura e exposição de configuração.

### Models (`models/`)

- Abstração de dados **por domínio**: `models/produto_model.py`, `models/usuario_model.py` (Python) | `models/courseModel.js` (Node).
- Único lugar que fala com o banco: queries parametrizadas, ou classes/consultas do ORM se o projeto já usa ORM.
- Regras de negócio ligadas ao dado (cálculo de total, transição de status) vivem aqui ou em métodos de domínio.
- **Não contém:** regra de apresentação (formatação de resposta HTTP), roteamento, parsing de request. Nunca devolve campos sensíveis (senha/hash) na serialização.

### Views/Routes (`views/routes.py` | `routes/`)

- Definição das rotas HTTP: método + path + binding para o controller.
- Faz apenas parsing fino de request/response (extrair params, devolver o status/JSON que o controller decidiu).
- **Delega tudo ao Controller.** Não contém SQL, não contém regra de negócio, não contém efeitos colaterais.
- Em Flask, preferir Blueprints por domínio; em Express, um `Router` por domínio (`routes/courseRoutes.js`).

### Controllers (`controllers/`)

- Orquestra o fluxo da aplicação: **validação → chamada ao Model → montagem da resposta**.
- Um controller por domínio: `controllers/produto_controller.py`, `controllers/pedido_controller.py` | `controllers/checkoutController.js`.
- Concentra a lógica de aplicação (coordenação, decisão de status HTTP); regras de negócio pesadas descem para o Model/serviço de domínio.
- Não fala diretamente com o driver do banco — sempre via Model.

### Middlewares (`middlewares/`)

- **Error handling centralizado** (`middlewares/error_handler.py` | `middlewares/errorHandler.js`): um único ponto converte exceções em respostas HTTP consistentes (400/404/500 com JSON padronizado), sem vazar stack trace.
- Autenticação/autorização (`middlewares/auth.py` | `middlewares/auth.js`): verificação de token **efetivamente aplicada** às rotas destrutivas/sensíveis apontadas na auditoria (AP-05/AP-06), **ligada por padrão**. Infra declarada mas não aplicada (decorator não usado, `router.use(auth)` atrás de flag desligada como `ENFORCE_AUTH=0`) **não** conta como proteção — o finding continua vivo.
- Outros transversais: logging estruturado, CORS restrito, rate limiting.

### Entry point / Composition root (`app.py` | `app.js`)

- Monta a aplicação: cria a instância do framework, carrega a Config, **injeta dependências** (conexão/ORM nos models ou factories), registra rotas (blueprints/routers) e middlewares, define o error handler.
- **Nada de lógica** de negócio, nenhuma rota inline, nenhum SQL. É apenas composição + `app.run(...)`/`app.listen(...)`.

## Regras de dependência

```
Views/Routes ──▶ Controllers ──▶ Models ──▶ DB
      │               │             │
      └───────────────┴─────────────┴──▶ Config (injetada pelo composition root)
```

1. **Routes → Controllers → Models. Nunca o inverso:** Model não importa controller; controller não importa rota; Model não conhece HTTP.
2. **Sem estado global mutável:** nada de variáveis de módulo acumulando dados entre requisições; conexão de DB por request ou gerenciada pelo ORM/pool, injetada pelo composition root.
3. **Config é injetada, não importada de módulo global com valores hardcoded:** o composition root lê a Config e passa o que cada camada precisa (ou as camadas leem o módulo Config, que por sua vez só lê env vars).
4. **Middlewares são transversais:** aplicados no composition root, nunca duplicados dentro de cada handler.
5. **Serialização segura:** o que sai para o cliente é decidido no Controller/Model via método explícito (`to_dict()` sem campos sensíveis), nunca "despejar" a linha do banco.

## Estrutura-alvo — diagrama por stack

### Python (Flask)

```
projeto/
├── config/
│   └── settings.py          # env vars, zero hardcoded
├── models/
│   ├── produto_model.py
│   ├── usuario_model.py
│   └── pedido_model.py
├── views/
│   └── routes.py            # blueprints; rotas finas → controllers
├── controllers/
│   ├── produto_controller.py
│   ├── usuario_controller.py
│   └── pedido_controller.py
├── middlewares/
│   ├── error_handler.py     # error handling centralizado
│   └── auth.py
├── database.py              # criação de conexão/ORM (infra)
├── .env.example
└── app.py                   # composition root
```

### Node (Express) — mapeamento de nomes equivalentes

O prefixo `src/` abaixo é opcional/convencional — use-o quando o projeto já adota `src/`; caso contrário, as mesmas pastas ficam direto na raiz (ex.: `models/` em vez de `src/models/`). A estrutura de camadas é idêntica com ou sem esse prefixo.

| Camada (nome canônico) | Pasta/arquivo em Node |
|---|---|
| Config | `src/config/index.js` |
| Models | `src/models/*.js` |
| Views/Routes | `src/routes/*.js` (Express `Router`) |
| Controllers | `src/controllers/*.js` |
| Middlewares | `src/middlewares/*.js` |
| Entry point / Composition root | `src/app.js` (+ `src/server.js` se separar listen) |

```
src/
├── config/
│   └── index.js             # env vars via process.env
├── models/
│   ├── courseModel.js
│   ├── userModel.js
│   └── orderModel.js
├── routes/
│   ├── courseRoutes.js
│   └── checkoutRoutes.js
├── controllers/
│   ├── courseController.js
│   └── checkoutController.js
├── middlewares/
│   ├── errorHandler.js      # (err, req, res, next) único
│   └── auth.js
├── db.js                    # conexão sqlite/pool (infra)
├── .env.example
└── app.js                   # composition root
```

## Regra de ADAPTAÇÃO (projeto já parcialmente em camadas)

Se o projeto **já tem** diretórios de camada (ex.: `models/`, `routes/`, `services/`, `utils/`):

1. **Não recrie a estrutura do zero** — reorganize a existente para cumprir as regras acima.
2. **Mova a lógica das rotas para controllers/services:** se as rotas contêm regra de negócio, crie `controllers/` (ou aproveite `services/` existente como camada de lógica) e deixe as rotas finas.
3. **Use os métodos de domínio existentes:** se os models já têm métodos úteis (ou o `services/` já implementa a regra correta mas está morto), **conecte-os ao fluxo real** em vez de reescrever.
4. **Elimine camadas de fachada:** `services/` nunca importado ou `utils/` duplicando services é código morto — absorva o que for útil na camada certa e remova o resto (registre a decisão no output).
5. **Se o projeto usa ORM, permaneça no ORM:** models continuam `db.Model`; a refatoração moderniza as chamadas (estilo SQLAlchemy 2.x), nunca reintroduz SQL cru.
6. **Preserve os endpoints:** a reorganização interna não pode alterar método + path de nenhuma rota existente.

A régua de sucesso é a mesma nos dois cenários (do zero ou adaptação): cada camada com uma responsabilidade, dependências fluindo Routes → Controllers → Models, config centralizada, error handling único e endpoints intactos.
