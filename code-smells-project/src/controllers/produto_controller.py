"""Controller do domínio Produto (RP-03, RP-11, RP-14).

Orquestra validação → model → resposta. A validação de produto existe em
UMA função, compartilhada por criação e atualização (o legado duplicava os
blocos), checando presença + tipo + faixa e respondendo 400 — nunca 500.
"""
from src.exceptions import NotFoundError, ValidationError
from src.models.produto_model import CATEGORIA_PADRAO, CATEGORIAS_VALIDAS

NOME_TAMANHO_MIN = 2
NOME_TAMANHO_MAX = 200


def _validar_produto(dados):
    """Validação única de payload de produto (presença + tipo + faixa)."""
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")

    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    descricao = dados.get("descricao", "")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if not isinstance(nome, str):
        raise ValidationError("Nome deve ser texto")
    if not isinstance(preco, (int, float)) or isinstance(preco, bool):
        raise ValidationError("Preço deve ser um número")
    if not isinstance(estoque, int) or isinstance(estoque, bool):
        raise ValidationError("Estoque deve ser um número inteiro")
    if not isinstance(descricao, str):
        raise ValidationError("Descrição deve ser texto")
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < NOME_TAMANHO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_TAMANHO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(
            "Categoria inválida. Válidas: " + str(list(CATEGORIAS_VALIDAS))
        )

    return {
        "nome": nome,
        "descricao": descricao,
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def _converter_preco(valor, nome_campo):
    """Converte filtro de preço da query string; inválido → 400 (RP-11)."""
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except ValueError:
        raise ValidationError(f"Filtro '{nome_campo}' deve ser um número") from None


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self):
        return {"dados": self._produtos.listar(), "sucesso": True}, 200

    def buscar(self, produto_id):
        produto = self._produtos.buscar_por_id(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado", extra={"sucesso": False})
        return {"dados": produto, "sucesso": True}, 200

    def criar(self, dados):
        campos = _validar_produto(dados)
        novo_id = self._produtos.criar(**campos)
        return {
            "dados": {"id": novo_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }, 201

    def atualizar(self, produto_id, dados):
        if self._produtos.buscar_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")
        campos = _validar_produto(dados)
        self._produtos.atualizar(produto_id, **campos)
        return {"sucesso": True, "mensagem": "Produto atualizado"}, 200

    def deletar(self, produto_id):
        if self._produtos.buscar_por_id(produto_id) is None:
            raise NotFoundError("Produto não encontrado")
        self._produtos.deletar(produto_id)
        return {"sucesso": True, "mensagem": "Produto deletado"}, 200

    def buscar_com_filtros(self, args):
        termo = args.get("q", "")
        categoria = args.get("categoria")
        preco_min = _converter_preco(args.get("preco_min"), "preco_min")
        preco_max = _converter_preco(args.get("preco_max"), "preco_max")

        resultados = self._produtos.buscar(termo, categoria, preco_min, preco_max)
        return {"dados": resultados, "total": len(resultados), "sucesso": True}, 200
