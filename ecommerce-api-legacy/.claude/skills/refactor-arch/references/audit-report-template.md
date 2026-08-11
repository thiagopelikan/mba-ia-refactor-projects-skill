# Template do Relatório de Auditoria (Fase 2)

Formato exato do relatório que a Fase 2 renderiza no terminal e salva em `reports/audit-project-N.md`. Siga a estrutura à risca — cabeçalho, `## Summary`, `## Findings` ordenados, rodapé `Total:`.

## Regras de preenchimento

1. **Todo finding tem arquivo e linha exatos** (`File: caminho/arquivo.py:42` ou intervalo `File: models.py:1-350`). **Nunca omita a linha, nunca invente arquivo/linha** — abra o arquivo e confirme antes de citar. Ocorrências múltiplas do mesmo problema podem listar várias linhas (`File: app.py:8, 23, 51`).
2. **Ordene os findings por severidade:** todos os CRITICAL primeiro, depois HIGH, MEDIUM e LOW.
3. **Cite o anti-pattern pelo nome e ID do catálogo** (`references/anti-patterns-catalog.md`), ex.: `### [CRITICAL] SQL Injection (AP-02)`.
4. **`Description`** traz evidência concreta: o trecho, valor ou padrão encontrado — não uma generalidade.
5. **`Impact`** explica por que importa (segurança, manutenção, performance).
6. **`Recommendation`** aponta a transformação do playbook (`references/refactoring-playbook.md`) pelo ID, ex.: "Aplicar RP-02 (parametrizar queries)".
7. **`## Summary`** traz a contagem por severidade na linha única `CRITICAL: n | HIGH: n | MEDIUM: n | LOW: n`; o rodapé traz `Total: N findings`. As contagens devem bater com os findings listados.
8. Texto em português; rótulos estruturais (`File:`, `Description:`, `Impact:`, `Recommendation:`, `Total:`) permanecem em inglês como no template.

## Template

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome-do-projeto>
Stack:   <linguagem + framework>
Files:   <N> analyzed | ~<X> lines of code

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [<SEVERITY>] <Nome do anti-pattern> (<AP-ID>)
File: <arquivo>:<linha(s)>
Description: <o que é, com evidência concreta do código>
Impact: <por que importa>
Recommendation: <transformação sugerida — apontar o padrão RP-NN do playbook>

### [<SEVERITY>] <Nome do anti-pattern> (<AP-ID>)
File: <arquivo>:<linha(s)>
Description: ...
Impact: ...
Recommendation: ...

(... um bloco por finding, ordenados CRITICAL → HIGH → MEDIUM → LOW ...)

================================
Total: <N> findings
================================
```

## Exemplo preenchido (para calibrar o tom)

```
================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code

## Summary
CRITICAL: 2 | HIGH: 0 | MEDIUM: 0 | LOW: 0

## Findings

### [CRITICAL] God Class / God Module / God Method (AP-03)
File: models.py:1-350
Description: Arquivo único contém toda a lógica de negócio, queries SQL, validação e formatação para 4 domínios diferentes (produtos, usuários, pedidos, itens).
Impact: Impossível testar em isolamento; qualquer mudança afeta tudo; viola completamente a separação de responsabilidades do MVC.
Recommendation: Aplicar RP-03 — quebrar em models/ e controllers/ por domínio, com rotas finas em views/routes.py.

### [CRITICAL] Hardcoded Credentials / Secrets (AP-01)
File: app.py:8
Description: SECRET_KEY hardcoded como 'minha-chave-super-secreta-123' diretamente no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório obtém a chave de assinatura de sessões; rotacionar exige alterar código e fazer deploy.
Recommendation: Aplicar RP-01 — extrair para config/settings.py lendo de variável de ambiente, com .env.example documentando as chaves.

================================
Total: 2 findings
================================
```

O relatório real terá muitos mais findings (mínimo 5 por projeto, incluindo ao menos 1 CRITICAL ou HIGH) — o exemplo acima mostra apenas o formato e o nível de especificidade esperado em cada campo.
