"""
Perfil setorial por ticker — Fase 1 do motor de perfis.

Ver CONTEXT.md, seção "Fase 1 — Motor de Perfis", para a investigação real
no valuation-tracker que fundamenta estes campos
(valuation/perfil_setor.py, wacc.py, sotp.py) e para a decisão de projetar
o perfil por TICKER, não por setor com cascata no schema — a cascata
existe só como mecanismo de carga de dados (ver "Herança de setor" no
CONTEXT.md), não como um conceito do schema em si.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from alicerce.proveniencia.schema import CampoComProveniencia


@dataclass
class PerfilSetor:
    """
    Perfil setorial de um ticker. Campos de classificação (`eh_regulado`,
    `eh_ciclico`, `taxonomia_financeira_especial`) são booleanos simples —
    fora do escopo de proveniência da Fase 0, que cobre só "campo de dado
    NUMÉRICO relevante" (ver CONTEXT.md). Campos numéricos de referência
    usam `CampoComProveniencia`: nunca um float cru, sempre com fonte,
    confiança e data — ver `tests/provenance_contract/`.
    """

    ticker: str
    setor: str
    subsetor: Optional[str] = None

    eh_regulado: bool = False
    eh_ciclico: bool = False
    # Bancos/seguradoras/holdings financeiras: EBIT/EBITDA/FCF não são
    # conceitos limpos pro negócio (mesma razão documentada em
    # valuation-tracker/valuation/perfil_setor.py pra bancos/seguradoras).
    taxonomia_financeira_especial: bool = False
    # Controle estatal (governo, direto ou golden share), consumido
    # diretamente por capm.calcular_capm(eh_estatal=...) — bool simples
    # como os demais campos de classificação acima, não
    # CampoComProveniencia, porque não é um DADO NUMÉRICO (ver docstring
    # da classe). Deliberadamente separado de
    # `TagPerfilEconomico.ESTATAL_CONTROLADA` (tags.py): a tag existe pra
    # composição de metodologia via `RegraPerfil` (ainda não
    # implementado), este campo é o input direto e mais estreito que o
    # CAPM já consome hoje. Ver CONTEXT.md, "TAEE3 — dados reais para
    # DDM+CAPM", pela decisão de eh_estatal=False para TAEE3 apesar da
    # CEMIG (estatal mineira) ser sócia controladora em conjunto com a
    # ISA Brasil — controle é COMPARTILHADO, nenhuma das duas partes tem
    # maioria isolada, e o mercado descreve a TAESA como empresa privada.
    eh_estatal: bool = False

    # Referências numéricas — todas opcionais: None = "sem override, usa
    # o fallback genérico" de quem consumir isso depois (Fase 2+), nunca
    # um número inventado aqui.
    beta_referencia: Optional[CampoComProveniencia] = None
    ev_ebitda_medio_referencia: Optional[CampoComProveniencia] = None
    psr_medio_referencia: Optional[CampoComProveniencia] = None
    fator_conversao_nopat_referencia: Optional[CampoComProveniencia] = None
    pct_divida_moeda_estrangeira: Optional[CampoComProveniencia] = None
    cap_crescimento_ciclico: Optional[CampoComProveniencia] = None

    # Métrica PRÓPRIA do ticker (não uma referência de fallback setorial
    # como os campos acima — por isso sem o sufixo "_referencia"). Volume
    # financeiro médio diário negociado (R$), sinal de liquidez de
    # mercado. Decisão de design (ver CONTEXT.md, investigação "liquidez:
    # campo vs. tag"): fica aqui, não como TagPerfilEconomico, porque é
    # uma condição de MERCADO que muda com o tempo sem nenhuma mudança na
    # empresa — precisa do mecanismo de staleness que só
    # CampoComProveniencia tem (`esta_desatualizado`, reaproveitado, não
    # duplicado). Opcional: None = liquidez ainda não investigada pra
    # esse ticker, nunca um número inventado.
    volume_medio_diario: Optional[CampoComProveniencia] = None

    # Inputs de DDM (Gordon Growth, valuation/ddm.py::calcular_ddm) —
    # ambos pendentes desde a sessão que implementou a função pura (ver
    # CONTEXT.md, "DDM (Gordon Growth)", seção "Pendente pra quando TAEE3
    # for populado"). Nome `dividendo_projetado` escolhido (não
    # `dpa_projetado`, que era a alternativa em aberto) por consistência
    # direta com o parâmetro de mesmo nome em `calcular_ddm()` — o valor
    # flui de um pro outro sem tradução de nome no meio do caminho.
    dividendo_projetado: Optional[CampoComProveniencia] = None
    taxa_crescimento_perpetuidade_ddm: Optional[CampoComProveniencia] = None

    # Input de CAPM (capm/capm.py::calcular_capm) — tamanho da empresa
    # (R$), usado pro size premium. Mesmo campo que uma cascata de
    # tamanho/liquidez futura reaproveitaria (não duplicar).
    valor_mercado: Optional[CampoComProveniencia] = None

    notas: Optional[str] = None

    def __post_init__(self) -> None:
        self.ticker = self.ticker.upper().strip()
        if not self.ticker:
            raise ValueError("PerfilSetor exige um ticker não-vazio.")
        if not self.setor or not self.setor.strip():
            raise ValueError(
                f"PerfilSetor de '{self.ticker}' exige um setor não-vazio "
                "— ticker sem setor não é um perfil válido."
            )
