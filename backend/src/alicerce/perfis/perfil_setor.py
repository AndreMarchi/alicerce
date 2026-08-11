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
