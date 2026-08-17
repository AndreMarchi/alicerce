"""
Classificação de perfil financeiro/seguradora — terceiro dos 4 perfis de
`RegraPerfil` do `docs/ROADMAP.md` (auditoria do valuation-tracker).
Caso real: WIZC3 — setor mal classificado rodava DCF/EV-EBITDA/Graham
numa corretora de seguros, score inflado (8,2); corrigido lá marcando
esses métodos "Não aplicável" pra esse perfil (Bazin, dividend-based,
continuou válido).

**DECISÃO (a) desta tarefa — SÓ classificação, sem função de bloqueio.**
Raciocínio completo em CONTEXT.md, "Perfil financeiro/seguradora"; resumo
aqui: os 2 perfis anteriores (`insolvencia.py`, `classe_ativo.py`) são
bloqueios UNIVERSAIS (se `True`, bloqueia tudo). Este é diferente — no
valuation-tracker o bloqueio era POR MÉTODO (DCF/EV-EBITDA/Graham
bloqueados, Bazin liberado). O único método que o Alicerce tem hoje é
DDM (`valuation/ddm.py`), que é dividend-based — mais parecido com Bazin
do que com os métodos que causaram o problema no WIZC3. Não existe hoje
nenhum método incompatível com este perfil pra bloquear; implementar uma
função de bloqueio agora seria antecipar uma decisão sem o método
problemático (DCF/Graham/EV-EBITDA) existir pra justificá-la.
`test_financeiro.py` confirma isso de forma EXECUTÁVEL, não só em
comentário: um ticker sintético com `taxonomia_financeira_especial=True`
e tag `DDM_ONLY` calcula DDM normalmente via
`pipeline/ddm_only.py::calcular_valor_ddm_only()`, sem nenhum bloqueio.

**Nenhum campo novo criado.** `PerfilSetor.taxonomia_financeira_especial`
já existe desde a Fase 1 (`perfil_setor.py`) com exatamente este
propósito ("Bancos/seguradoras/holdings financeiras: EBIT/EBITDA/FCF não
são conceitos limpos pro negócio") e já está populado corretamente pros
6 pilotos (WIZC3=True, ITSA4=True, os outros 4 False) — confirmado por
investigação antes de escrever qualquer código, não assumido. Este
módulo só expõe uma função de leitura sobre esse campo já existente.
"""

from __future__ import annotations

from alicerce.perfis.motor import obter_perfil


def ticker_e_perfil_financeiro(ticker: str) -> bool:
    """
    `True` se `ticker` tiver `PerfilSetor.taxonomia_financeira_especial`
    marcado — bancos, seguradoras, holdings financeiras, onde
    EBIT/EBITDA/FCF não são conceitos limpos pro negócio.

    Levanta `TickerSemPerfilError` (propagada de
    `perfis/motor.py::obter_perfil()`) se `ticker` não estiver
    cadastrado — mesmo padrão de erro explícito dos perfis anteriores.

    Função pura, sem hardcode de ticker, sem integração com
    `pipeline/` ou com os outros perfis (insolvência, classe de ativo)
    ainda — mesma pendência explícita já registrada pros dois
    anteriores, composição fica pra quando `RegraPerfil` for retomado.
    """
    return obter_perfil(ticker).taxonomia_financeira_especial
