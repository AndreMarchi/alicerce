"""
Classificação de perfil patrimonial/imóveis — quarto e último dos 4
perfis de `RegraPerfil` do `docs/ROADMAP.md` (auditoria do
valuation-tracker). Caso real de referência: HBRE3 (HBR Realty) — não é
um dos 6 tickers-piloto do Alicerce, só o caso documentado no
valuation-tracker como pendência não resolvida (fica em perfil
genérico/fallback, sem calibração própria).

**Escopo desta tarefa: SÓ classificação.** Diferente dos 3 perfis
anteriores (insolvência, classe de ativo, financeiro), este não teve
nenhuma decisão sobre bloquear/permitir um método existente — a pergunta
de fundo (qual método de valuation cabe pra empresa patrimonial: P/VP/
NAV em vez de P/L/DDM?) não tem resposta ainda, e não é decisão pra
tomar numa tarefa de classificação. Formalizada como pergunta de
modelagem financeira EM ABERTO em CONTEXT.md, "Perfil
patrimonial/imóveis" — não implementar P/VP, NAV, nem nenhum bloqueio de
DDM aqui.
"""

from __future__ import annotations

from alicerce.perfis.motor import obter_perfil


def ticker_e_perfil_patrimonial(ticker: str) -> bool:
    """
    `True` se `ticker` tiver `PerfilSetor.perfil_patrimonial` marcado —
    empresa cujo negócio é essencialmente posse/gestão de patrimônio
    (ex: imóveis), onde lucro contábil corrente pode não refletir
    geração de valor real (que vem de variação de valor do patrimônio,
    não de operação).

    Levanta `TickerSemPerfilError` (propagada de
    `perfis/motor.py::obter_perfil()`) se `ticker` não estiver
    cadastrado — mesmo padrão de erro explícito dos 3 perfis anteriores.

    Função pura, só classificação — nenhuma decisão de método de
    valuation, nenhum bloqueio, nenhuma integração com `pipeline/` ainda.
    """
    return obter_perfil(ticker).perfil_patrimonial
