"""
Schema de proveniência por campo — Fase 0 do roadmap.

Todo dado fundamentalista carregado no Alicerce passa por este schema.
O objetivo é nunca ter um campo "mudo" (valor sem saber de onde veio,
com que confiança, ou quando foi atualizado).

Ver docs/ROADMAP.md, Fase 0, para o critério de saída desta fase.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal, Optional

Fonte = Literal["manual", "cvm", "brapi", "yfinance", "fundamentus"]
Confianca = Literal["alta", "media", "baixa"]


@dataclass
class CampoComProveniencia:
    """
    Um único campo de dado fundamentalista, com proveniência completa.

    `motivo_override` é obrigatório sempre que `fonte == "manual"` —
    isso é validado em __post_init__, não só documentado em comentário.
    """

    valor: float
    fonte: Fonte
    confianca: Confianca
    data_atualizacao: date
    motivo_override: Optional[str] = None

    def __post_init__(self) -> None:
        if self.fonte == "manual" and not self.motivo_override:
            raise ValueError(
                "motivo_override é obrigatório quando fonte == 'manual'. "
                "Registrar por que o dado automático foi rejeitado/sobrescrito."
            )

    @property
    def esta_desatualizado(self) -> bool:
        """Placeholder de regra de negócio — ajustar limiar por tipo de campo."""
        return (date.today() - self.data_atualizacao).days > 180


# Cascata de fontes explícita, na ordem de prioridade (Fase 0).
# A função que resolve um campo deve registrar QUAL fonte da cascata
# respondeu, não só o valor final — isso é o que a Fase 5 (backtesting)
# e a auditoria de override manual dependem para funcionar.
CASCATA_FONTES: tuple[Fonte, ...] = ("fundamentus", "brapi", "yfinance", "cvm", "manual")


@dataclass
class RegistroAuditoria:
    """
    Um registro por (ticker, campo) indicando quantos campos estão em
    override manual — sinal de que a fonte automática está falhando
    para aquele perfil de empresa. Ver critério de saída da Fase 0.
    """

    ticker: str
    campo: str
    fonte_usada: Fonte
    campos_em_override_manual: int = field(default=0)
