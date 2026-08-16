"""
Portão de insolvência confirmada — maior prioridade dos 4 perfis de
`RegraPerfil` encontrados na auditoria do valuation-tracker (ver
`docs/ROADMAP.md`, Fase 1, "Achado real que motiva priorização"; caso
real de referência: LIGT3, recuperação judicial).

Diferente de `pipeline/ddm_only.py::calcular_valor_ddm_only()` (Fase 1,
mesmo commit anterior): aquele é uma decisão de MÉTODO (qual valuation
usar), este é um PORTÃO BINÁRIO — "isso não deveria produzir
recomendação de compra, independente do que qualquer método calcule".
Não há "método" a escolher aqui, então não faz sentido nenhum tentar se
encaixar na mesma família conceitual de `RegraPerfil`/`ContextoValuation`
(Protocol ainda não implementado, ver `docs/ROADMAP.md`) nem do padrão
usado em `ddm_only.py` — é uma checagem mais simples, um pré-filtro que
rodaria ANTES de qualquer `RegraPerfil`, não uma das `N` regras
compostas. Ver CONTEXT.md, "Perfil de insolvência confirmada", pela
decisão completa de nomenclatura.

Nenhum ticker hardcoded aqui de propósito — o valuation-tracker tinha
`EMPRESAS_RECUPERACAO_JUDICIAL` como lista hardcoded manual (só 4
tickers, penalização de score fraca demais), exatamente o padrão que a
auditoria já criticou. O dado vem de
`PerfilSetor.em_recuperacao_judicial`, carregado de
`perfis/dados/perfis_ticker.json` — atualizar o cadastro é a única forma
de mudar o resultado, nunca uma edição de código.
"""

from __future__ import annotations

from alicerce.perfis.motor import obter_perfil


def ticker_bloqueado_por_insolvencia(ticker: str) -> bool:
    """
    `True` se `ticker` estiver marcado como `em_recuperacao_judicial` em
    `PerfilSetor` — sinal de que ele NÃO deveria aparecer como
    recomendação, independente de qualquer valor calculado por qualquer
    método. `False` caso contrário (default de `PerfilSetor`, campo não
    populado ainda é tratado como "não confirmado", não como "seguro" —
    ver CONTEXT.md pela distinção).

    Levanta `TickerSemPerfilError` (propagada de
    `perfis/motor.py::obter_perfil()`) se `ticker` não estiver cadastrado
    — nunca retorna `False` por ausência de cadastro, que seria uma
    falha silenciosa do mesmo tipo já criticado na auditoria do
    valuation-tracker (recomendação passando batida por falta de dado,
    não por dado confirmado seguro).

    Função pura: só lê `PerfilSetor`, nenhum efeito colateral, nenhuma
    integração com `pipeline/` ainda — ver CONTEXT.md pela pendência
    explícita de quando/como compor isso com o resultado de valuation.
    """
    return obter_perfil(ticker).em_recuperacao_judicial
