"""
Portão de classe de ativo incompatível — segundo dos 4 perfis de
`RegraPerfil` encontrados na auditoria do valuation-tracker (ver
`docs/ROADMAP.md`, Fase 1). Caso real de referência: RZAG11 (FIAGRO —
fundo de crédito do agronegócio) e outros tickers terminados em "11"
identificados na mesma auditoria (provavelmente FIIs).

Fundos (FIAGRO/FII) não são empresas: distribuem quase toda a renda como
dividendo por lei e não têm "lucro"/"crescimento" no sentido que
DDM/DCF/Graham assumem. Rodar esses métodos num fundo produz número sem
sentido — mesmo espírito de portão binário do perfil de insolvência
(`perfis/insolvencia.py`): "isso não é candidato a nenhum método de
valuation de AÇÃO disponível hoje", independente do que qualquer método
calcule se for chamado de qualquer forma.

**Mesma decisão de nomenclatura do perfil de insolvência, mesmo
raciocínio**: NÃO é `RegraPerfil` (Protocol reservado no ROADMAP pro
design geral de N regras com precedência via `ContextoValuation`, que
não existe em código) — é outro pré-filtro sem "método" a escolher, não
uma das regras compostas. Mora em `perfis/` (classificação), não em
`pipeline/` (orquestração de cálculo, onde `ddm_only.py` mora) pelo
mesmo motivo: só lê um campo de `PerfilSetor`, não orquestra nada.

## ARMADILHA REAL — não inferir classe de ativo pelo sufixo do ticker

`TAEE11` é uma UNIT (bundle TAEE3+TAEE4) da TAESA, uma empresa real —
NÃO um fundo, apesar do sufixo "11" que FIAGROs/FIIs também usam.
Terminar em "11" é necessário mas NÃO suficiente pra ser FIAGRO/FII
(RZAG11 termina em "11" E é fundo; TAEE11 termina em "11" e NÃO é
fundo). Uma heurística de detecção por sufixo classificaria TAEE11
incorretamente como fundo — exatamente o tipo de regra "genérica
demais" que motivou registrar este perfil em primeiro lugar (ver
CONTEXT.md, "Perfil de classe de ativo incompatível", pela investigação
completa, incluindo outros tickers com o mesmo risco no universo do
Alicerce). Por isso `PerfilSetor.classe_ativo` é um campo EXPLÍCITO,
nunca inferido de string — e por isso não tem default seguro (`None`
levanta erro aqui, não vira "acao" por padrão).
"""

from __future__ import annotations

from alicerce.perfis.motor import obter_perfil

_CLASSES_INCOMPATIVEIS_COM_METODOS_DE_ACAO = frozenset({"fiagro", "fii"})


class ClasseAtivoNaoClassificadaError(ValueError):
    """
    Ticker cadastrado em `PerfilSetor` mas sem `classe_ativo` definido.
    Erro explícito, mesmo padrão de `TickerSemPerfilError`
    (`perfis/motor.py`) e `CampoObrigatorioAusenteError`
    (`pipeline/ddm_only.py`) — nunca assumir "compatível" (ação) por
    ausência de dado, que seria uma falha silenciosa (mesmo raciocínio
    já aplicado ao portão de insolvência pra campo ausente).
    """


def ticker_bloqueado_por_classe_ativo_incompativel(ticker: str) -> bool:
    """
    `True` se a `classe_ativo` de `ticker` for `"fiagro"` ou `"fii"` —
    sinal de que nenhum método de valuation de AÇÃO disponível hoje
    (DDM, e no futuro DCF/Graham/etc.) se aplica, independente do que
    qualquer um deles calcule se for chamado. `False` se for `"acao"`
    ou `"unit"` (representam uma empresa real, mesmo que via bundle de
    classes de ação — ver armadilha do `TAEE11` na docstring do módulo).

    Levanta `TickerSemPerfilError` (propagada de
    `perfis/motor.py::obter_perfil()`) se `ticker` não estiver
    cadastrado.

    Levanta `ClasseAtivoNaoClassificadaError` se `ticker` estiver
    cadastrado mas sem `classe_ativo` definido — nunca assume
    "compatível" por ausência de dado.

    Função pura: só lê `PerfilSetor`, nenhum efeito colateral, nenhuma
    integração com `pipeline/` ou com o portão de insolvência ainda —
    ver CONTEXT.md pela pendência explícita de composição futura.
    """
    perfil = obter_perfil(ticker)
    if perfil.classe_ativo is None:
        raise ClasseAtivoNaoClassificadaError(
            f"PerfilSetor de '{perfil.ticker}' não tem classe_ativo definida — "
            "não é possível decidir compatibilidade sem esse dado."
        )
    return perfil.classe_ativo in _CLASSES_INCOMPATIVEIS_COM_METODOS_DE_ACAO
